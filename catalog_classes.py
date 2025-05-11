import csv
import json
from hashlib import sha256

class User:
   # System's user 
    def __init__(self, username, name, password, profile_picture):
        # Constructor: stores data and creates a hash of the password
        self.username = username
        self.name = name
        self.profile_picture = profile_picture
        # We only store the password's hash 
        self.password_hash = self.hash_password(password)

    def hash_password(self, password):
        # Encrypts password using SHA-256
        return sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        # Returns a dictionary with the user's attributes
        return {
            'username': self.username,
            'name': self.name, 
            'profile_picture': self.profile_picture,
            'password_hash': self.password_hash
        }

class Areas:
    def __init__(self, area):
        self.area = area

    def to_dict(self):
        return {
            'area': self.area
        }
    
class Catalogs:
    def __init__(self, catalog):
        self.catalog = catalog

    def to_dict(self):
        return {
            'catalog': self.catalog
        }

class Magazine:
    def __init__(self, h_index=None, title=None, area=None, catalog=None, publisher=None, issn=None, widget=None, publication_type=None, **kwargs):
        self.h_index = h_index if h_index else kwargs.get('id', '')
        self.title = title if title else kwargs.get('title', '')
        self.publisher = publisher
        self.issn = issn
        self.widget = widget
        self.publication_type = publication_type
        # Additional Scimago fields
        self.site = kwargs.get('site', '')
        self.subject_area_category = kwargs.get('subject_area_category', '')
        self.url = kwargs.get('url', '')
        
        # Process subject areas from Scimago data
        self.areas = []
        self.catalogs = []
        if self.subject_area_category:
            self._process_subject_areas()

    def _process_subject_areas(self):
        # Split by comma and process each part
        parts = self.subject_area_category.split(',')
        current_area = None
        
        for part in parts:
            part = part.strip()
            # If it's just a year or quartile (Q1-Q4), skip it
            if part.isdigit() or part.startswith('Q'):
                continue
            # Add as an area if it's not already in the list
            if part and not any(year.isdigit() for year in part.split()):
                current_area = part
                if current_area not in self.areas:
                    self.areas.append(current_area)
        
        # Add Scimago as catalog
        self.catalogs.append('Scimago')

    def to_dict(self):
        return {
            'h_index': self.h_index,
            'title': self.title,
            'areas': self.areas,
            'catalogs': self.catalogs,
            'publisher': self.publisher,
            'issn': self.issn,
            'widget': self.widget,
            'publication_type': self.publication_type,
            'site': self.site,
            'subject_area_category': self.subject_area_category,
            'url': self.url
        }

class Catalog:
    def __init__(self):
        self.users = {}
        self.magazines = {}
        self.areas = {}
        self.catalogs = {}
        self.current_user = None
    
    def load_csv(self, file, system_class):
        print(f"Loading file from {file}")
        with open(file, mode='r', encoding='utf8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if system_class == User:
                    user = User(**row)
                    self.users[user.username] = user
                elif system_class == Magazine:
                    magazine = Magazine(**row)
                    self.magazines[magazine.h_index] = magazine
                elif system_class == Areas:
                    area = Areas(**row)
                    self.areas[area.area] = area
                elif system_class == Catalogs:
                    catalog = Catalogs(**row)
                    self.catalogs[catalog.catalog] = catalog

    def load_scimago_json(self, file_path):
        print(f"Loading Scimago data from {file_path}")
        with open(file_path, mode='r', encoding='utf8') as file:
            data = json.load(file)
            for title, magazine_data in data.items():
                # Add the title to the magazine data since it's the key in the JSON
                magazine_data['title'] = title
                magazine = Magazine(**magazine_data)
                self.magazines[magazine.h_index] = magazine
    
    def login(self, username, password):
        user = self.users.get(username)
        if user and user.password_hash == user.hash_password(password):
            self.current_user = user
            return True
        return False