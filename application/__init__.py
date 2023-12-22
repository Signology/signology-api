from flask import Flask
from flask_session import Session
import os
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime, timedelta
from google.cloud import storage
from sqlalchemy import create_engine
from .db import db

# Change this to your secret key (it can be anything, it's for extra protection)
SECRET_KEY = '-'
PROFILE_FOLDER = "static/profile_pic/"
UPLOADED_IMAGE_BUCKET = "static/uploaded_image/raw/"
BUCKET_NAME = "slangtrap-capstone-406914-bucket"
IMAGE_FOLDER = 'static/image_history/'

ORG_DOMAINS = ['.edu', '.org']
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webp'])
EXP_DATE = datetime.utcnow() + timedelta(days=3650)  # Set expiration to 10 years from now

app = Flask(__name__)

# Enter your database connection details below

DB_USER = '-'
DB_PASSWORD = '-'
DB_NAME = '-'
CLOUD_SQL_CONNECTION_NAME = '-'
DB_PORT = '-'

SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@34.128.82.108:{DB_PORT}/{DB_NAME}"

# Create the engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/db_capstone4'

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
app.config['SECRET_KEY'] = SECRET_KEY
# app.config['PROFILE_FOLDER'] = PROFILE_FOLDER
# app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['EXP_DATE'] = EXP_DATE
app.config['ORG_DOMAINS'] = ORG_DOMAINS
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS


CORS(app, supports_credentials=True)
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
Session(app)
dir_path = os.path.dirname(os.path.realpath(__file__))
app.config.update(
    UPLOADED_IMAGE = os.path.join(dir_path, "static/uploaded_image/raw/"),
    CROPED_IMAGE = os.path.join(dir_path, "static/uploaded_image/croped/"),
    MODEL_PATH = os.path.join(dir_path,'model/slang_app.h5'),
    DATASET_AUTOCORRECT = os.path.join(dir_path,"controller/autocorrect_dataset/talpco_id.txt"),
    PROFILE_FOLDER = PROFILE_FOLDER,
    UPLOADED_IMAGE_BUCKET = UPLOADED_IMAGE_BUCKET,
    BUCKET_NAME = BUCKET_NAME,
    TEMP_FOLDER = os.path.join(dir_path,'temp/'),
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(dir_path, "credential.json")
client = storage.Client()
bucket = client.bucket(app.config["BUCKET_NAME"])

db.init_app(app)

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = "/static/swagger.json"  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Signology-id"
    },
)

app.register_blueprint(swaggerui_blueprint)

from application import routes
