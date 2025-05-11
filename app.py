from flask import Flask, request, session, flash, redirect, url_for, render_template
import os
import catalog_classes as cc
import math

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load users from CSV
catalog = cc.Catalog()
catalog.load_csv('datos/users.csv', cc.User)
catalog.load_scimago_json('datos/json/scimago.json')

# Pagination
def paginate(items, page, per_page):
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page) if per_page > 0 else 1
    paginated_items = items[(page-1)*per_page : page*per_page] if per_page > 0 else items
    return {
        'items': paginated_items,
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_num': page - 1,
        'next_num': page + 1
    }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if catalog.login(username, password):
            session['logged_in'] = True
            session['username'] = catalog.current_user.name
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    catalog.current_user = None
    return redirect(url_for('login'))

@app.route('/')
def home():
    # Get search and pagination parameters
    query = request.args.get('query', '').lower()
    per_page = request.args.get('per_page', default=10, type=int)
    page = request.args.get('page', default=1, type=int)
    initial_letter = request.args.get('letter', '').upper()
    
    all_magazines = list(catalog.magazines.values())    # Filter magazines based on search query
    if query:
        filtered_magazines = [
            mag for mag in all_magazines
            if ((mag.title and query in mag.title.lower()) or 
                any(area and query in area.lower() for area in (mag.areas or [])) or 
                any(cat and query in cat.lower() for cat in (mag.catalogs or [])) or
                (mag.publisher and query in mag.publisher.lower()) or  
                (mag.issn and query in mag.issn.lower()) or
                (mag.publication_type and query in mag.publication_type.lower()))
        ]
    else:
        filtered_magazines = all_magazines

    # Filter magazines based on initial letter
    if initial_letter:
        filtered_magazines = [
            mag for mag in filtered_magazines
            if mag.title.upper().startswith(initial_letter)
        ]

    # Paginate magazines
    pagination = paginate(filtered_magazines, page, per_page)
    
    return render_template('home.html',
                         username=session.get('username'),
                         current_user=catalog.current_user,
                         query=query,
                         magazines=pagination['items'],
                         total_magazines=pagination['total_items'],
                         per_page=pagination['per_page'],
                         page=pagination['page'],
                         total_pages=pagination['total_pages'],
                         has_prev=pagination['has_prev'],
                         has_next=pagination['has_next'],
                         prev_num=pagination['prev_num'],
                         next_num=pagination['next_num'])

@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'), current_user=catalog.current_user)

@app.route('/areas')
def areas():
    query = request.args.get('query', '').lower()
    initial_letter = request.args.get('letter', '').upper()
    
    # Get unique areas from magazines
    areas_dict = {}
    for mag in catalog.magazines.values():
        for area in mag.areas:
            if area not in areas_dict:
                areas_dict[area] = {'area_title': area, 'num_magazines': 1}
            else:
                areas_dict[area]['num_magazines'] += 1
    
    areas_list = list(areas_dict.values())
    
    # Filter by search query
    if query:
        areas_list = [a for a in areas_list if query in a['area_title'].lower()]
    
    # Filter by initial letter
    if initial_letter:
        areas_list = [a for a in areas_list if a['area_title'].upper().startswith(initial_letter)]
    
    # Order by area title alphabetically
    areas_list = sorted(areas_list, key=lambda x: x['area_title'])
    
    return render_template('areas.html',
                         username=session.get('username'),
                         current_user=catalog.current_user,
                         query=query,
                         areas=areas_list)

@app.route('/area/<area_title>')
def area_detail(area_title):
    query = request.args.get('query', '').lower()
    per_page = request.args.get('per_page', default=10, type=int)
    page = request.args.get('page', default=1, type=int)
    initial_letter = request.args.get('letter', '').upper()

    all_magazines = list(catalog.magazines.values())

    # Filter by area
    filtered_magazines = [mag for mag in all_magazines if area_title in mag.areas]

    # Filter by search query
    if query:
        filtered_magazines = [
            mag for mag in filtered_magazines
            if (query in mag.title.lower()) or 
               any(query in area.lower() for area in mag.areas) or 
               any(query in cat.lower() for cat in mag.catalogs) or
               (query in mag.publisher.lower()) or  
               (query in mag.issn.lower()) or
               (query in mag.publication_type.lower())
        ]

    # Filter by initial letter
    if initial_letter:
        filtered_magazines = [
            mag for mag in filtered_magazines
            if mag.title.upper().startswith(initial_letter)
        ]

    pagination = paginate(filtered_magazines, page, per_page)

    return render_template('area.html',
        username=session.get('username'),
        current_user=catalog.current_user,
        area_title=area_title,
        query=query,
        magazines=pagination['items'],
        total_magazines=pagination['total_items'],
        per_page=pagination['per_page'],
        page=pagination['page'],
        total_pages=pagination['total_pages'],
        has_prev=pagination['has_prev'],
        has_next=pagination['has_next'],
        prev_num=pagination['prev_num'],
        next_num=pagination['next_num']
    )

@app.route('/catalogs')
def catalogs():
    query = request.args.get('query', '').lower()
    initial_letter = request.args.get('letter', '').upper()
    
    # Get unique catalogs from magazines
    catalogs_dict = {}
    for mag in catalog.magazines.values():
        for cat in mag.catalogs:
            if cat not in catalogs_dict:
                catalogs_dict[cat] = {'catalog_title': cat, 'num_magazines': 1}
            else:
                catalogs_dict[cat]['num_magazines'] += 1
    
    catalogs_list = list(catalogs_dict.values())
    
    # Filter by search query
    if query:
        catalogs_list = [c for c in catalogs_list if query in c['catalog_title'].lower()]
    
    # Filter by initial letter
    if initial_letter:
        catalogs_list = [c for c in catalogs_list if c['catalog_title'].upper().startswith(initial_letter)]
    
    # Order by catalog title alphabetically
    catalogs_list = sorted(catalogs_list, key=lambda x: x['catalog_title'])
    
    return render_template('catalogs.html',
                         username=session.get('username'),
                         current_user=catalog.current_user,
                         query=query,
                         catalogs=catalogs_list)

@app.route('/catalog/<catalog_title>')
def catalog_detail(catalog_title):
    query = request.args.get('query', '').lower()
    per_page = request.args.get('per_page', default=10, type=int)
    page = request.args.get('page', default=1, type=int)
    initial_letter = request.args.get('letter', '').upper()

    all_magazines = list(catalog.magazines.values())    # Filter by catalog
    filtered_magazines = [mag for mag in all_magazines if catalog_title in mag.catalogs]

    # Filter by search query
    if query:
        filtered_magazines = [
            mag for mag in filtered_magazines
            if ((mag.title and query in mag.title.lower()) or 
                any(area and query in area.lower() for area in (mag.areas or [])) or 
                any(cat and query in cat.lower() for cat in (mag.catalogs or [])) or
                (mag.publisher and query in mag.publisher.lower()) or  
                (mag.issn and query in mag.issn.lower()) or
                (mag.publication_type and query in mag.publication_type.lower()))
        ]

    # Filter by initial letter
    if initial_letter:
        filtered_magazines = [
            mag for mag in filtered_magazines
            if mag.title.upper().startswith(initial_letter)
        ]

    pagination = paginate(filtered_magazines, page, per_page)

    return render_template('catalog.html',
        username=session.get('username'),
        current_user=catalog.current_user,
        catalog_title=catalog_title,
        query=query,
        magazines=pagination['items'],
        total_magazines=pagination['total_items'],
        per_page=pagination['per_page'],
        page=pagination['page'],
        total_pages=pagination['total_pages'],
        has_prev=pagination['has_prev'],
        has_next=pagination['has_next'],
        prev_num=pagination['prev_num'],
        next_num=pagination['next_num']
    )

@app.route('/magazine/<h_index>')
def magazine_detail(h_index):
    # Load magazines from JSON
    catalog.load_scimago_json('datos/json/scimago.json')
    magazine = catalog.magazines.get(h_index)
    
    if not magazine:
        return render_template('404.html'), 404
    
    return render_template('magazine.html',
                         username=session.get('username'),
                         current_user=catalog.current_user,
                         magazine=magazine)

if __name__ == '__main__':
    app.run(debug=True)