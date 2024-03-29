from db import mongo

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Photo:
    def __init__(self, file_path, user_id):
        self.file_path = file_path
        self.user_id = user_id
