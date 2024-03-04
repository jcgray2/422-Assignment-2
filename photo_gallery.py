from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, session  # Make sure to import session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Set a secret key for session signing

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import db
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '748957203498572340598'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:123123123@database-1.cng84gieuv3y.us-east-2.rds.amazonaws.com/422'
app.config['UPLOAD_FOLDER'] = 'path/to/upload/directory'

db.init_app(app)

# Import models after db and app have been defined
from models import User, Photo

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Direct comparison
            session['user_id'] = user.id  # Store the user's ID in the session
            flash('You were successfully logged in')
            return redirect(url_for('photos'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['photo']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Assuming the user's ID is stored in the session upon login
            user_id = session.get('user_id')
            if user_id:
                new_photo = Photo(file_path=file_path, user_id=user_id)
                db.session.add(new_photo)
                db.session.commit()
                flash('Photo uploaded successfully!')
            else:
                flash('You must be logged in to upload photos.')
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        # Example search by filename (adjust according to your schema and requirements)
        photos = Photo.query.filter(Photo.file_path.like(f'%{search_query}%')).all()
        return render_template('search_results.html', photos=photos)
    return render_template('search.html')

@app.route('/photos')
def photos():
    if 'user_id' not in session:
        flash('You must be logged in to view photos.')
        return redirect(url_for('login'))
    all_photos = Photo.query.all()  # Retrieve all photos from the database
    return render_template('photos.html', photos=all_photos)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables for our data models
    app.run(debug=True)
