from application import app
# from flask import redirect, render_template, url_for, request,session
from application.controller.upload_image import upload_image_controller
from application.controller.predict import predict_controller
from werkzeug.utils import secure_filename
import nltk
nltk.download('punkt')

import datetime
from distutils.util import strtobool
from functools import wraps
import hashlib
import os
import re
import uuid
from flask import jsonify, request
import jwt

from application import db, app
from application.db import BlacklistToken, History, ImageHistory, User



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def revoke_token(token):
    # Check if the token exists in the blacklist table
    existing_token = BlacklistToken.query.filter_by(token=token).first()

    if existing_token:
        # Token already exists in the blacklist table
        return jsonify({'message': 'Token already revoked'}), 400
    else:
        # Insert the token into the blacklist table
        new_blacklist_token = BlacklistToken(token=token)
        db.session.add(new_blacklist_token)
        db.session.commit()
        return jsonify({'message': 'Token revoked successfully'}), 200

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            if BlacklistToken.query.filter_by(token=token).first():
                return jsonify({'message': 'Token revoked. Please log in again.'}), 401
            
            data=jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data["user_id"]).first()

            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(current_user.to_dict(), *args, **kwargs)

    return decorated

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            if BlacklistToken.query.filter_by(token=token).first():
                return jsonify({'message': 'Token revoked. Please log in again.'}), 401
            data=jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            if 'role' not in data or  data.get('role') != 'admin':
                return {
                    "message": "Invalid Admin Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
            current_user = User.query.filter_by(id=data["user_id"]).first()

            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(current_user, *args, **kwargs)

    return decorated

def delete_image(image_path):
    # Delete associated images
    raw_image_full_path = os.path.join(app.config['UPLOADED_IMAGE'], image_path)
    if os.path.exists(raw_image_full_path):
        os.remove(raw_image_full_path)
    cropped_image_full_path = os.path.join(app.config['CROPED_IMAGE'], image_path)
    if os.path.exists(cropped_image_full_path):
        os.remove(cropped_image_full_path)

@app.route('/')
def index():
    return 'Welcome to slangtrap-api!, with CI/CD FR THIS TIME'

@app.route('/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(' ')[1]  # Extracting the token part after 'Bearer '
        return revoke_token(token)
    return jsonify({'message': 'No token provided'}), 400

# http://localhost:5000/login/
@app.route('/login', methods=['POST'])
def login():
    # Output message if something goes wrong...
    msg = ''

     # Check if "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Retrieve the hashed password
        hash = password + app.config["SECRET_KEY"]
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()

        # Check if user exists using MySQL
        user = User.query.filter_by(email=email, password=password).first()
        
         # If user exists in user table in out database
        if user:
            user_dict = user.to_dict()
            if user_dict['profile_pic']:
                user_dict['profile_pic'] = os.path.join(app.config['PROFILE_FOLDER'], user_dict['profile_pic'])
            if email == "admin0@gmail.com":
                 user_dict["token"] = jwt.encode(
                    {"user_id": user_dict["id"],
                     "exp": app.config['EXP_DATE'],
                     "role": "admin"},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
            else:
                user_dict["token"] = jwt.encode(
                        {"user_id": user_dict["id"],
                        "exp": app.config['EXP_DATE'],
                        "role": "user"},
                        app.config["SECRET_KEY"],
                        algorithm="HS256"
                    )
            response = {
                "error": False,
                "message": "success",
                "loginResult ": user_dict
            }
            
            json_response = jsonify(response)
            json_response.status_code = 200

            return json_response
        else:
            # user doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    response = {
                "error": True,
                "message": msg,
            }
    json_response = jsonify(response)
    json_response.status_code = 401
    return json_response

# http://localhost:5000/register
@app.route('/register', methods=['POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        point = 500

        if any(email.endswith(domain) for domain in app.config['ORG_DOMAINS']):
            point = 1500  # Email is from an organization

        # Check if user exists using MySQL
        user = User.query.filter_by(email=email).first()
        # If user exists show error and validation checks
        if user:
            msg = 'user already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.config["SECRET_KEY"]
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()

            # Create a new user instance
            new_user = User(
                username=username,
                password=password,
                email=email,
                point=point,
            )

            # Add the new user to the session
            db.session.add(new_user)
            db.session.commit()

            msg = 'You have successfully registered!'
            response = {
                "error": False,
                "message": msg,
            }
            json_response = jsonify(response)
            json_response.status_code = 200
            return json_response
    else:
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

#user
# http://localhost:5000/user
@app.route('/allusers', methods=['GET'])
@admin_token_required
def get_all_user(current_user):
    # We need all the user info for the user so we can display it on the profile page
    users = User.query.all()
    # Check if user exists
    if users:
        users_dict = [user.to_dict() for user in users]
        for u_d in users_dict:
            if u_d['profile_pic']:
                u_d['profile_pic'] = os.path.join(app.config['PROFILE_FOLDER'], u_d['profile_pic'])
        response = {
            "error": False,
            "message": "success",
            "user ": users_dict
        }
        # Show the profile page with user info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when user doesn't exist for the given ID
        response = {
            "error": True,
            "message": "User not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/user
@app.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    id = current_user.get('id')

    # We need all the user info for the user so we can display it
    user = User.query.filter_by(id=id).first()
    # Check if user exists
    if user:
        user_dict = user.to_dict()
        if user_dict['profile_pic']:
            user_dict['profile_pic'] = os.path.join(app.config['PROFILE_FOLDER'], user_dict['profile_pic'])
        response = {
            "error": False,
            "message": "success",
            "user ": user_dict
        }
        # Show the profile page with user info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when user doesn't exist for the given ID
        response = {
            "error": True,
            "message": "User not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/edituser
@app.route('/user', methods=['PUT'])
@token_required
def edit_user(current_user):
    # Output message if something goes wrong...
    msg = ''
    user_id = current_user.get('id')

    # We need all the user info for the user so we can display it on the profile page
    user = User.query.get(user_id)
    # Check if user exists
    if user:
        username = request.form.get('username') or user.username

        if 'password' in request.form:
            password = request.form.get('password')
            hash = password + app.config["SECRET_KEY"]
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
        else:
            password = user.password

        is_premium_str = request.form.get('is_premium')
        is_premium = strtobool(is_premium_str) if is_premium_str is not None else user.is_premium
        
        premium_date = request.form.get('premium_date') or user.premium_date
        
        point = request.form.get('point') or user.point

        if 'profile_pic' in request.files:
            save_path = app.config['PROFILE_FOLDER']
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            profile_pic = request.files['profile_pic']

            # Check if the uploaded file is within the size limit
            if profile_pic.content_length > app.config['MAX_CONTENT_LENGTH'] or not allowed_file(profile_pic.filename):
                response = {
                    "error": True,
                    "message": 'File size exceeds the limit or not supported',
                }
                return jsonify(response), 413  # 413: Payload Too Large

            profile_pic_filename = str(uuid.uuid4()) + '.' + profile_pic.filename.rsplit('.', 1)[1].lower()

            # Delete previous profile picture if it exists
            if user.profile_pic:
                previous_profile_pic_path = os.path.join(app.config["PROFILE_FOLDER"], user.profile_pic)
                if os.path.exists(previous_profile_pic_path):
                    os.remove(previous_profile_pic_path)

            profile_pic.save(os.path.join(app.config["PROFILE_FOLDER"], profile_pic_filename))
        else:
            profile_pic_filename = user.profile_pic

        user.username=username
        user.password=password
        user.is_premium = bool(is_premium)
        user.premium_date=premium_date
        user.point=point
        user.profile_pic=profile_pic_filename
        db.session.commit()

        msg = 'User have successfully edited!'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response

    msg= 'User not found'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# edit point
# http://localhost:5000/user/point
@app.route('/user/point', methods=['PATCH'])
@token_required
def edit_user_point(current_user):
    # Output message if something goes wrong...
    msg = ''
    user_id = current_user.get('id')

    # 
    user = User.query.get(user_id)

    # Check if user exists
    if user:    
        point = request.form.get('point') or user.point    
        user.point = point
        db.session.commit()

        msg = 'User point have successfully edited!'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response

    msg= 'User not found'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# http://localhost:5000/user/
@app.route('/user', methods=['DELETE'])
@token_required
def delete_user(current_user):
    user_id = current_user['id']
    user = User.query.get(user_id)

    # Check if user exists
    if user:
        # delete history from deleted user
        history_ids = [history.id for history in user.histories]

        for h_id in history_ids:
            delete_history(h_id)

        if user.profile_pic:
            previous_profile_pic_path = os.path.join(app.config["PROFILE_FOLDER"], user.profile_pic)
            if os.path.exists(previous_profile_pic_path):
                os.remove(previous_profile_pic_path)

        db.session.delete(user)  # Delete the user
        db.session.commit()

        response = {
            "error": False,
            "message": "User successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "User not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# history
# http://localhost:5000/history
@app.route('/allhistories', methods=['GET'])
@admin_token_required
def get_all_history(current_user):
    # We need all the history info for the history so we can display it on the profile page
    histories = History.query.all()

    # Check if history exists
    if histories:
        histories_dict = [history.to_dict() for history in histories]
        response = {
            "error": False,
            "message": "success",
            "history ": histories_dict
        }
        # Show the profile page with history info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when history doesn't exist for the given ID
        response = {
            "error": True,
            "message": "history not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/history
@app.route('/history', methods=['POST'])
@token_required
def post_history(current_user):
    # Output message if something goes wrong...
    msg = ''
    # Check if "word" POST requests exist (user submitted form)
    if 'word' in request.form:
        # Create variables for easy access
        user_id = current_user.get('id')
        word = request.form['word']

        new_history = History(user_id=user_id, word=word)
        db.session.add(new_history)
        db.session.commit()

        # If there are more than 6 records, delete the oldest ones
        user_history = History.query.filter_by(user_id=user_id).order_by(History.created_at.asc()).all()
        if len(user_history) > 6:
            oldest_history = user_history[:len(user_history) - 6]
            for h in oldest_history:
                delete_history(h.id)

        msg = 'history added'
        response = {
            "error": False,
            "message": msg,
            "new_history_id": new_history.id
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    
    # Form is empty... (no POST data)
    msg = 'Please fill out user_id and word'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# http://localhost:5000/edithistory
@app.route('/history/<int:id>/<word>', methods=['PUT'])
@token_required
def edit_history_param(current_user,id,word):
    # Output message if something goes wrong...
    msg = ''
    history_id = id

    # We need all the user info for the user so we can display it on the profile page
    history = History.query.get(history_id)
    # Check if user exists
    if history and word:
        history.word=word

        db.session.commit()

        msg = 'Hisotry have successfully edited!'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response

    msg= 'User not found'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response

# http://localhost:5000/history/
@app.route('/history/<int:id>', methods=['DELETE'])
@token_required
def delete_history(current_user,id):
    history = History.query.get(id)

    # Check if history exists
    if history:
        # delete image_history from deleted history
        for image_history in history.image_histories:
            delete_image_history(image_history.id)
        
        db.session.delete(history)
        db.session.commit()

        response = {
            "error": False,
            "message": "History successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "History not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# image_history
# http://localhost:5000/history
@app.route('/allimagehistories', methods=['GET'])
@admin_token_required
def get_all_image_history(current_user):
    # Check if image_history exists
    image_histories = ImageHistory.query.all()
    if image_histories:
        image_histories_list = [history.to_dict() for history in image_histories]
        for i_hl in image_histories_list:
            if i_hl['image']:
                i_hl['image'] = os.path.join(app.config['UPLOADED_IMAGE'], i_hl['image'])
        response = {
            "error": False,
            "message": "success",
            "image_histories": image_histories_list
        }
        # Show the profile page with image_history info
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        # Handle case when image_history doesn't exist for the given ID
        response = {
            "error": True,
            "message": "image_histories not found",
        }
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# http://localhost:5000/image_history
@app.route('/image_history', methods=['POST'])
@token_required
def post_image_history(current_user):
    msg = ''
    # Check if "history_id", "image" POST requests exist
    if 'history_id' in request.form and 'image' in request.files:
        # Create variables for easy access
        history_id = request.form['history_id']
        image = request.files['image']
        if image.content_length > app.config['MAX_CONTENT_LENGTH'] or not allowed_file(image.filename):
            response = {
                "error": True,
                "message": 'File size exceeds the limit or not supported',
            }
            return jsonify(response), 413  # 413: Payload Too Large
        
        # image_filename = str(uuid.uuid4()) + '.' + image.filename.rsplit('.', 1)[1].lower()

        # image.save(os.path.join(app.config['IMAGE_FOLDER'], image_filename))
        filename = secure_filename(image.filename)
        extension = filename.split(".")[-1]

        save_path = os.path.join(app.config['UPLOADED_IMAGE'], str(history_id))
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        new_filename = str(len(os.listdir(save_path))) + f".{extension}"

        image.save(os.path.join(save_path, new_filename))

        image_filename = os.path.join(str(history_id), new_filename)

        new_image_history = ImageHistory(history_id=history_id, image=image_filename)
        db.session.add(new_image_history)
        db.session.commit()

        msg = 'image history added'
        response = {
            "error": False,
            "message": msg,
        }
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    
    # Form is empty... (no POST data)
    msg = 'Please fill out user_id and word'
    response = {
                "error": True,
                "message": msg,
    }
    json_response = jsonify(response)
    json_response.status_code = 409
    return json_response


# http://localhost:5000/image_history/
@app.route('/image_history/<int:id>', methods=['DELETE'])
@token_required
def delete_image_history(current_user,id):
    # Check if image_history exists
    image_history = ImageHistory.query.filter_by(id=id).first()
    if image_history:
        image_path = image_history.image
        delete_image(image_path)
        db.session.delete(image_history)
        db.session.commit()

        response = {
            "error": False,
            "message": "image_history successfully deleted",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 200
        return json_response
    else:
        response = {
            "error": True,
            "message": "image_history not found",
        }
        
        json_response = jsonify(response)
        json_response.status_code = 404
        return json_response

# history user
@app.route('/user/history', methods=['GET'])
@token_required
def get_user_history(current_user):
    user_id = current_user.get('id')
    # We need all the user info for the user so we can display it on the profile page
    histories = (
            db.session.query(User.id.label('user_id'), History.id.label('history_id'),
                             History.word, ImageHistory.id.label('image_history_id'),
                             ImageHistory.image)
            .outerjoin(History, User.id == History.user_id)
            .outerjoin(ImageHistory, History.id == ImageHistory.history_id)
            .filter(User.id == user_id)
            .all()
        )

    response = {
        "error": False,
        "message": "histories successfully retrieved",
        "histories ": [{
                "user_id": row.user_id,
                "history_id": row.history_id,
                "word": row.word,
                "image_history_id": row.image_history_id,
                "image": row.image
            } for row in histories]
    }
    # Show the user histories
    json_response = jsonify(response)
    json_response.status_code = 200
    return json_response



@app.route('/upload_image/<int:history_id>', methods=['POST'])
@token_required
def upload_image_route(current_user,history_id):
    # post_image_history(history_id)
    
    return upload_image_controller(str(history_id))
    
@app.route('/predict/<int:history_id>', methods=['POST'])
@token_required
def predict_route(current_user,history_id):
    output = predict_controller(str(history_id))
    edit_history_param(history_id, output["word_cnn"])  # Assuming 'edit_history' is the function to edit history
    return jsonify(output)
    
    # return  predict_controller(str(history_id))


    


