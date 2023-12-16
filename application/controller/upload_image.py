import os
from flask import jsonify, request
from application import app
from werkzeug.utils import secure_filename

def upload_image_controller(history_id):
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        filename = secure_filename(file.filename)
        extension = filename.split(".")[-1]
        
        save_path = os.path.join(app.config['UPLOADED_IMAGE'], history_id)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        new_filename = str(len(os.listdir(save_path))) + f".{extension}"
        
        file.save(os.path.join(save_path, new_filename))
        
        response_data = {
            "response": "upload successfully",
        }

        return jsonify(response_data)