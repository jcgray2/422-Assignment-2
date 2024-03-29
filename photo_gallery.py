from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import mongo  # Corrected import
import boto3
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length



client = MongoClient('mongodb://localhost:27017/')
db = client['422']  
photos_collection = db['photos']
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

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=1, max=32)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=1, max=32)])
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Create an instance of the LoginForm class
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Retrieve user from MongoDB
        user = users_collection.find_one({'username': username})
        
        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username  # Store username in session
            flash('Logged in successfully!')
            return redirect(url_for('photo_gallery'))  # Assuming you have an index route
        else:
            flash('Invalid username or password.')
            print("Invalid username or password.")  # Log the error for debugging
    
    return render_template('login.html', form=form)

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
        
        try:
            # Add new user to MongoDB
            users_collection.insert_one({
                'username': username,
                'password': password,
                'password_hash': password_hash  # Store hashed password
            })
            flash('Account created successfully. Please log in.')
            return redirect(url_for('login'))
        
        except Exception as e:
            flash('Error creating account. Please try again.')
            print(f"Error: {e}")  # Log the error for debugging
    
    return render_template('signup.html')

@app.route('/photo_gallery')
def photo_gallery():
    if 'username' not in session:
        flash('You must be logged in to view the gallery.')
        return redirect(url_for('login'))
    
    return render_template('photo_gallery.html')

def upload_file_to_s3(file, bucket_name, username):
    try:
        # Check if the folder exists, if not create it
        photo_id = str(uuid.uuid4())
        file_path = f"uploads/{username}/{secure_filename(file.filename)}"
        file_name = file.filename
        folder_key = f"{username}/"
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_key)
        if 'Contents' not in response:
            # Folder doesn't exist, create it
            s3.put_object(Bucket=bucket_name, Key=(folder_key))
        
        # Upload the file to the user's folder in S3
        s3.upload_fileobj(
            file.stream,
            bucket_name,
            f"{folder_key}{secure_filename(file.filename)}",
            ExtraArgs={'ContentType': file.content_type}
        )

        photos_collection.insert_one({
        'id': photo_id,
        'username': username,
        'file_path': file_path,
        'image_name': file_name
    })
        return True
    except Exception as e:
        print("Error uploading file to S3:", e)
        return False

def upload_file_to_mongodb(file, username):
    try:
        # Upload the file to MongoDB
        photo_id = str(uuid.uuid4())
        file_path = f"uploads/{username}/{secure_filename(file.filename)}"
        file_name = file.filename

        # Save file to server
        if not os.path.exists(f"uploads/{username}/"):
            os.makedirs(f"uploads/{username}/")
        file.save(os.path.join(f"uploads/{username}/", secure_filename(file.filename)))

        # Insert metadata into MongoDB
        photos_collection.insert_one({
            'id': photo_id,
            'username': username,
            'file_path': file_path,
            'image_name': file_name
        })

        return True
    except Exception as e:
        print("Error uploading file to MongoDB:", e)
        return False

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
            
            s3_url = upload_file_to_s3(file, S3_BUCKET, username)
            
            if s3_url:
                photo_id = str(uuid.uuid4())
                file_name = file.filename
                
                # Insert metadata into MongoDB
                photos_collection.insert_one({
                    'id': photo_id,
                    'username': username,
                    'file_path': s3_url,
                    'image_name': file_name
                })
                
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
            images = list(photos_collection.find({
                'username': username,
                'image_name': {'$regex': f'.*{image_name.lower()}.*'}
            }))
            
            for image in images:
                # Generate S3 URL for the image
                s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{username}/{image['image_name']}"
                image['file_path'] = s3_url
                
        except Exception as e:
            flash('Error searching for images. Please try again.')
            return redirect(url_for('download'))
        
        return render_template('download.html', images=images)
    
    return render_template('download.html')

if __name__ == '__main__':
    app.run(debug=True)
