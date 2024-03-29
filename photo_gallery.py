from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import boto3

app = Flask(__name__)
app.config['SECRET_KEY'] = '748957203498572340598'
app.config['MONGO_URI'] = 'mongodb://localhost:27017'  # MongoDB URI

mongo = PyMongo(app)

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('Users')  # DynamoDB table for Users

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query MongoDB for the user
        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            # Successful login
            session['username'] = username
            return redirect(url_for('photo_gallery'))
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
        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        # Add new user to MongoDB
        mongo.db.users.insert_one({
            'username': username,
            'password': password_hash
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
    
    # Here you would typically fetch the user's photos from MongoDB or wherever they're stored
    # For now, we'll just return a simple message or render a template
    return 'Welcome to the Photo Gallery!!!'

if __name__ == '__main__':
    app.run(debug=True)
