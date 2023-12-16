from application import app
import os
import cv2
import mediapipe as mp
import numpy as np

def autocrop(user):

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

    crop_dir = os.path.join(app.config['CROPED_IMAGE'], user)
    raw_dir = os.path.join(app.config['UPLOADED_IMAGE'], user)
    if not os.path.exists(crop_dir):
            os.makedirs(crop_dir)
            
    counter = 0
    
    for img_path in os.listdir(os.path.join(raw_dir)):
        x_ = []
        y_ = []
        data_aux = []
        img= cv2.imread(os.path.join(raw_dir, img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    H, W, _ = img.shape
                    x_.append(x)
                    y_.append(y)
                
                x1 =int(min(x_) * W) 
                y1 =int(min(y_) * H) 
                x2 =int(max(x_) * W) 
                y2 =int(max(y_) * H) 
                x1, y1, x2, y2 = max(0, x1), max(0, y1), min(W, x2), min(H, y2)
                if (x2 - x1) > (y2 - y1):
                    # Menyesuaikan y2 untuk menjaga rasio persegi
                    y2 = y1 + (x2 - x1)
                    # Menyesuaikan tinggi persegi
                    selisih = y2-y1
                    y2 = int(0.85 * y2)
                    y1 = int(y2-selisih)
                else:
                    # Menyesuaikan x2 untuk menjaga rasio persegi
                    x2 = x1 + (y2 - y1)
                    # Menyesuaikan lebar persegi
                    selisih = x2-x1
                    x2 = int(0.85 * x2)
                    x1 = int(x2 - selisih)

                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)
             
                hand_crop = img_rgb[y1:y2, x1:x2]
                cv2.waitKey(25)
                cv2.imwrite(os.path.join(crop_dir, '{}.jpg'.format(counter)),  cv2.cvtColor(hand_crop, cv2.COLOR_RGB2BGR))
        counter +=1