from flask import Flask, render_template, request, redirect, url_for, flash, session
import boto3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '748957203498572340598'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:123123123@database-1.cng84gieuv3y.us-east-2.rds.amazonaws.com/422'
app.config['UPLOAD_FOLDER'] = 'path/to/upload/directory'

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('Users')  # DynamoDB table for Users

# Import models after db and app have been defined
# Assuming 'models.py' includes definitions for User (SQL) and Photo (SQL) models
from models import db, User, Photo
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query DynamoDB for the user
        try:
            response = table.get_item(Key={'username': username})
        except Exception as e:
            flash('Login failed. Please try again.')
            return redirect(url_for('login'))
        
        user = response.get('Item')
        if user and check_password_hash(user['password_hash'], password):
            # Successful login
            session['username'] = username  # You can store more in session as needed
            return redirect(url_for('photo_gallery'))  # Adjust the redirect as needed
        else:
            # Invalid credentials
            flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)
        
        # Check if username already exists
        response = table.get_item(Key={'username': username})
        if 'Item' in response:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        # Add new user to DynamoDB
        table.put_item(Item={
            'username': username,
            'password_hash': password_hash
        })
        
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/photo_gallery')
def photo_gallery():
    # Ensure the user is logged in
    if 'username' not in session:
        flash('You must be logged in to view the gallery.')
        return redirect(url_for('login'))
    
    # Here you would typically fetch the user's photos from DynamoDB or wherever they're stored
    # For now, we'll just return a simple message or render a template
    return 'Welcome to the Photo Gallery!!!'  # Or render_template('photo_gallery.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables for SQL models
    app.run(debug=True)
