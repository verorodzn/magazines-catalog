import csv
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
    def __init__(self, h_index, title, area, catalog, publisher, issn, widget, publication_type):
        self.h_index = h_index
        self.title = title
        self.area = area
        self.catalog = catalog
        self.publisher = publisher
        self.issn = issn
        self.widget = widget
        self.publication_type = publication_type

    def to_dict(self):
        return {
            'h_index': self.h_index,
            'title': self.title,
            'area': self.area,
            'catalog': self.catalog,
            'publisher': self.publisher,
            'issn': self.issn,
            'widget': self.widget,
            'publication_type': self.publication_type
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
    
    def login(self, username, password):
        user = self.users.get(username)
        if user and user.password_hash == user.hash_password(password):
            self.current_user = user
            return True
        return False