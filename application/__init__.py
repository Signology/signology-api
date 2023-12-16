from flask import Flask
from flask_session import Session
import os
from flask_cors import CORS

from datetime import datetime, timedelta

from sqlalchemy import create_engine

from .db import db

# Change this to your secret key (it can be anything, it's for extra protection)
SECRET_KEY = 'keyrahasiakey'
PROFILE_FOLDER = 'static/profile_pic/'
IMAGE_FOLDER = 'static/image_history/'

ORG_DOMAINS = ['.edu', '.org']
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webp'])
EXP_DATE = datetime.utcnow() + timedelta(days=3650)  # Set expiration to 10 years from now

app = Flask(__name__)

# Enter your database connection details below

DB_USER = 'root'
DB_PASSWORD = 'capstone-db'
DB_NAME = 'db_capstone1'
CLOUD_SQL_CONNECTION_NAME = 'slangtrap-capstone-406914:asia-southeast2:capstone-db'
DB_PORT = '3306'

SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@34.128.82.108:{DB_PORT}/{DB_NAME}"
# SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}?unix_socket=/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"

# Create the engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# # Bind the engine to a session
# Session = sessionmaker(bind=engine)

# app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/db_capstone3'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.config['SECRET_KEY'] = SECRET_KEY
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['EXP_DATE'] = EXP_DATE
app.config['ORG_DOMAINS'] = ORG_DOMAINS
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS


CORS(app, supports_credentials=True)
# app.config["SECRET_KEY"] ='449bf441804501016c9fdcc8c2684a347dda16f7d359c39d6374df211f42'
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
Session(app)
dir_path = os.path.dirname(os.path.realpath(__file__))
app.config.update(
    UPLOADED_IMAGE = os.path.join(dir_path, "static\\uploaded_image\\raw\\"),
    CROPED_IMAGE = os.path.join(dir_path, "static\\uploaded_image\\croped\\"),
    MODEL_PATH = os.path.join(dir_path,'model\\slang_app.h5'),
    DATASET_AUTOCORRECT = os.path.join(dir_path,"controller\\autocorrect_dataset\\talpco_id.txt")
)


db.init_app(app)

from application import routes
