from flask import Flask, render_template, url_for, flash, redirect, session, request
from pymongo import MongoClient
from models import UserModel, TimetableModel
from datetime import datetime
from datetime import timedelta
import uuid
import os

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key

client = MongoClient("mongodb://localhost:27017/")
db = client.exam_management

user_model = UserModel(db)
timetable_model = TimetableModel(db)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = user_model.verify_password(email, password)

        if not user:
            flash('Invalid credentials, please try again.')
            return redirect(url_for('login'))

        
        session['email'] = user['email']  
        session['role'] = user['role']
        
        return redirect(url_for('home'))  

    return render_template('Login.html')


@app.route('/Register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_class = request.form['user_class']
    
        if user_model.find_user(email):
            flash('User already exists.')
            return redirect(url_for('register'))
        
        user_model.register_user(email, password, user_class)
        flash('Registration successful.')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/admin/', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = user_model.verify_password(email, password)

        if not user:
            flash('Invalid credentials, please try again.')
            return redirect(url_for('admin'))
        
        if user['role'] != 'admin':
            flash('Access denied. Only admins can log in here.')
            return redirect(url_for('login'))

        
        session['email'] = user['email']  
        session['role'] = user['role']
        flash('Welcome, admin!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/adminregister/', methods = ['GET', 'POST'])
def adminregister():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
        if user_model.find_user(email):
            flash('User already exists.')
            return redirect(url_for('register'))
        
        user_model.register_admin(email, password)
        flash('Registration successful.')
        return redirect(url_for('admin'))
    return render_template('adminregister.html')

@app.route('/')  # This route will be where users land after successful login
def home():
    if 'email' not in session:
        flash('Please log in to view the timetable.')
        return redirect(url_for('login'))
    
    user_email = session['email']
    user_class = user_model.find_user(user_email).get('class', 'N/A')  # Get the user's class

    # Fetch the timetable for the user's class
    #timetable_entries = TimetableModel.get_timetable_by_class(user_class)
    return render_template('home.html',user_class=user_class)

@app.route('/logout/')
def logout():
    """Logs the user out by clearing the session and redirects to the login page."""
    session.clear()  
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'email' not in session or session.get('role') != 'admin':
        flash('Admin access only!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST' and 'generate_timetable' in request.form:
        # Get data from form
        class_name = request.form['class_name'].strip()  # Only a single class is entered now
        subjects = request.form['subjects'].split(',')
        venues = request.form['venues'].split(',')
        invigilators = request.form['invigilators'].split(',')

        # Trim whitespace
        subjects = [sub.strip() for sub in subjects]
        venues = [venue.strip() for venue in venues]
        invigilators = [invigilator.strip() for invigilator in invigilators]

        # Ensure the number of subjects, venues, and invigilators match
        if len(subjects) != len(venues) or len(subjects) != len(invigilators):
            flash("Mismatch in the number of subjects, venues, or invigilators. Please check and try again.", "danger")
            return redirect(url_for('admin_dashboard'))

        # Generate timetable
        exam_dates = generate_exam_dates(len(subjects))
        for i, subject in enumerate(subjects):
            timetable_model.add_timetable_entry(
                class_name=class_name,
                exam_date=exam_dates[i],
                venue=venues[i % len(venues)],  # Wrap around if there are more subjects than venues
                exam_name=subject,
                invigilator=invigilators[i % len(invigilators)]  # Wrap around if there are more subjects than invigilators
            )

        flash(f'Timetable generated successfully for {class_name}!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Data for dashboard display
    class_user_counts = user_model.get_all_users_by_class()
    timetable_entries = timetable_model.get_all_timetables()

    return render_template(
        'admin_dashboard.html',
        class_user_counts=class_user_counts,
        timetable_entries=timetable_entries
    )


@app.route('/delete_timetable/<string:exam_code>', methods=['POST'])
def delete_timetable(exam_code):
    """Deletes a timetable entry based on the provided exam_code."""
    timetable_model.delete_timetable_entry(exam_code)
    flash('Timetable entry deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_timetable/<string:exam_code>', methods=['POST'])
def edit_timetable(exam_code):
    # Debugging: Log form data to ensure it includes all required fields
    print("Form Data:", request.form)
    
    # Validate form data
    missing_keys = [key for key in ['exam_date', 'venue', 'exam_name', 'invigilator'] if key not in request.form]
    if missing_keys:
        flash(f"Missing fields: {', '.join(missing_keys)}", 'danger')
        return redirect(url_for('admin_dashboard'))

    # Update timetable entry
    updated_data = {
        'exam_date': request.form['exam_date'],
        'venue': request.form['venue'],
        'exam_name': request.form['exam_name'],
        'invigilator': request.form['invigilator']
    }
    timetable_model.update_timetable_entry(exam_code, updated_data)
    flash('Timetable entry updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Utility function to generate exam dates dynamically
def generate_exam_dates(count):
    base_date = datetime.now()
    return [(base_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(count)]



if __name__ == "__main__":
    app.run(debug=True)
