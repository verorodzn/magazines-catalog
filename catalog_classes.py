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

class Catalog:
    def __init__(self):
        self.users = {}
        self.current_user = None
    
    def load_csv(self, file, system_class):
        print(f"Loading file from {file}")
        with open(file, mode='r', encoding='utf8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if system_class == User:
                    user = User(**row)
                    self.users[user.username] = user
    
    def login(self, username, password):
        user = self.users.get(username)
        if user and user.password_hash == user.hash_password(password):
            self.current_user = user
            return True
        return False