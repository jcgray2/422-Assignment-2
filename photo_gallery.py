from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import mongo  # Corrected import
import boto3
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient
import uuid

client = MongoClient('mongodb://localhost:27017/')
db = client['422']  
users_collection = db['users']  # MongoDB collection for users
app = Flask(__name__)
app.config['SECRET_KEY'] = '748957203498572340598'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/422'

mongo.init_app(app)

# Initialize an S3 client
s3 = boto3.client('s3')
S3_BUCKET = 'se422-images'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Retrieve user from MongoDB
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Logged in successfully!')
            return redirect(url_for('index'))  # Assuming you have an index route
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Generate hashed password
        password_hash = generate_password_hash(password)
        
        # Check if username already exists
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        # Add new user to MongoDB
        users_collection.insert_one({
            'username': username,
            'password': password_hash  # Store hashed password
        })
        
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/photo_gallery')
def photo_gallery():
    if 'username' not in session:
        flash('You must be logged in to view the gallery.')
        return redirect(url_for('login'))
    
    return render_template('photo_gallery.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['photo']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            username = session.get('username')
            
            if upload_file_to_s3(file, S3_BUCKET, username):
                photo_id = str(uuid.uuid4())
                file_path = f"https://{S3_BUCKET}.s3.amazonaws.com/{username}/{secure_filename(file.filename)}"
                file_name = file.filename
                
                # Here, you need to implement photosTable or integrate with MongoDB as per your requirement
                # photosTable.put_item(Item={
                #     'id': photo_id,
                #     'username': username,
                #     'file_path': file_path,
                #     'image_name': file_name
                # })
                
                flash('File uploaded successfully')
                return redirect(url_for('upload'))
            else:
                flash('Error uploading file to S3')
                return redirect(request.url)
    
    return render_template('upload.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        image_name = request.form.get('image_name')
        username = session.get('username')
        
        try:
            response = photosTable.scan(
                FilterExpression=Attr('username').eq(username) & Attr('image_name').contains(image_name.lower())
            )
            images = response['Items']
        except Exception as e:
            flash('Error searching for images. Please try again.')
            return redirect(url_for('download'))
        
        return render_template('download.html', images=images)
    
    return render_template('download.html')

if __name__ == '__main__':
    app.run(debug=True)
