from flask import Flask, request, session, flash, redirect, url_for, render_template
import os
import catalog_classes as cc
import math

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load users from CSV
catalog = cc.Catalog()
catalog.load_csv('datos/users.csv', cc.User)
catalog.load_csv('datos/magazines.csv', cc.Magazine)

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
    
    # Load magazines from CSV
    catalog.load_csv('datos/magazines.csv', cc.Magazine)
    all_magazines = list(catalog.magazines.values())

    # Filter magazines based on search query
    if query:
        filtered_magazines = [
            mag for mag in all_magazines
            if (query in mag.title.lower()) or 
               (query in mag.area.lower()) or 
               (query in mag.category.lower()) or
               (query in mag.publisher.lower()) or  
               (query in mag.issn.lower()) or
               (query in mag.publication_type.lower())
        ]
    else:
        filtered_magazines = all_magazines

    # Filter magazines based on initial letter
    if initial_letter:
        filtered_magazines = [
            mag for mag in filtered_magazines  # Is applied to the filtered list
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
    # Get search parameters
    query = request.args.get('query', '').lower()
    initial_letter = request.args.get('letter', '').upper()
    
    # Load areas from CSV
    catalog.load_csv('datos/areas.csv', cc.Areas)
    all_areas = list(catalog.areas.values())
    
    # Convert to list of dictionaries for template
    areas_list = [{'area_title': area.area, 'num_magazines': 0} for area in all_areas]  # Starts with 0
    
    # Count magazines per area
    catalog.load_csv('datos/magazines.csv', cc.Magazine)
    for mag in catalog.magazines.values():
        for area in areas_list:
            if mag.area == area['area_title']:
                area['num_magazines'] += 1
    
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
                         areas=areas_list,)

@app.route('/area/<area_title>')
def area_detail(area_title):
    return render_template('area.html',
                         username=session.get('username'),
                         current_user=catalog.current_user,)


if __name__ == '__main__':
    app.run(debug=True)