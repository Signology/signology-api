from application import app
from PIL import Image
import os
import numpy as np
from tensorflow.keras.models import load_model


def preprocess(img, input_size):
    nimg = img.convert('L').resize(input_size, resample=Image.BICUBIC)
    img_arr = np.array(nimg) / 255.0
    return img_arr

def reshape(imgs_arr):
    return np.stack(imgs_arr, axis=0)


def predict_model(user):
    model = load_model(app.config["MODEL_PATH"],compile=False)
    crop_dir = os.path.join(app.config['CROPED_IMAGE'], user)
    files = os.listdir(crop_dir)
    characters = []
    input_size = (64,64)

    labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N',
            'O','P','Q','R','S','T','U','V','W','X','Y','Z']
    for data in files:
        if data.endswith('.jpg') or data.endswith('.png'):
            print(data)
            imgg = Image.open(os.path.join(crop_dir, data))
            X = preprocess(imgg,input_size)
            X = reshape([X])
            y = model.predict(X)
            print( labels[np.argmax(y)], np.max(y) )
            characters.append(labels[np.argmax(y)])
    separated = ""
    word_cnn = separated.join(characters)
    
    return(word_cnn)