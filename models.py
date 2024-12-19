from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid


class UserModel:
    def __init__(self, db):
        self.collection = db.users

    def register_user(self, email, password, user_class):
        """Register a new user."""
        hashed_password = generate_password_hash(password)
        self.collection.insert_one({
            'email': email,
            'password': hashed_password,
            'role': 'user',
            'class': user_class,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
    
    def register_admin(self,email,password):
        """Register a new admin."""
        hashed_password = generate_password_hash(password)
        if self.find_user(email):
            raise ValueError("Admin already exists.")
        self.collection.insert_one({
            'email': email,
            'password': hashed_password,
            'role': 'admin',
            'created_at': datetime.utcnow(),
            
        })

    def find_user(self, email):
        """Find a user by username."""
        #return self.collection.find_one({'email': email})
        try:
            return self.collection.find_one({'email': email})
        except Exception as e:
            print(f"Error finding user: {e}")
            return None

    def verify_password(self, email, password):
        """Check if the password matches for a given username."""
        user = self.find_user(email)
        if user and check_password_hash(user['password'], password):
            return user
        return None
    def get_all_users_by_class(self):
        users_by_class = {}
    # Fetch all users from the database
        for user in self.collection.find():
            users_by_class.setdefault(user['class'], []).append(user)
            return users_by_class


class TimetableModel:
    def __init__(self, db):
        self.collection = db['timetable']

    def add_timetable_entry(self, class_name, exam_date, venue, exam_name, invigilator):
       exam_code = str(uuid.uuid4())[:8]  # Generate a unique exam code
       self.collection.insert_one({
            'class': class_name,
            'exam_date': exam_date,
            'venue': venue,
            'exam_name': exam_name,
            'invigilator': invigilator,
            'exam_code': exam_code
        })

    def get_timetable_by_class(self, class_name):
        return [entry for entry in self.collection if entry['class'] == class_name]

    def get_all_timetables(self):
        return list(self.collection.find())

    def update_timetable_entry(self, exam_code, updated_data):
        self.collection.update_one({'exam_code': exam_code}, {'$set': updated_data})


    def delete_timetable_entry(self, exam_code):
        self.collection.delete_one({'exam_code': exam_code})