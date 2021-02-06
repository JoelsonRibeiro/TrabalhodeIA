import face_recognition
from os import path, getcwd
from db import DataBase as Db
import cv2
from PIL import Image
import numpy as np
import io
from datetime import datetime


class Face:
    def __init__(self, app):
        self.storage = app.config['storage']

        self.db = Db()
        self.faces = []
        self.known_encoding_faces = []
        self.face_user_keys = {}
        self.process_this_frame = True
        self.load_all()

    def get_user_by_id(self, user_id):
        user = {}
        results = self.db.select(
            'SELECT users.id,users.name,users.created,faces.user_id,faces.filename FROM users LEFT JOIN faces ON users.id = faces.user_id WHERE users.id = ?',
            [user_id])
        i = 0
        for row in results:

            face = {
                "user_id": row[3],
                "filename": row[4],
            }
            if i == 0:
                user = {
                    "id": row[0],
                    "name": str(row[1]),
                    "created": row[2],
                    "faces": [],
                }
                user["faces"].append(face)
                i += 1
            if 'id' in user:
                return user

            return None

    def load_user_by_index_key(self, index_key=0):
        key_str = str(index_key)
        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]
        return None

    def load_train_file_by_name(self, name):
        trained_storage = path.join(self.storage, 'conhecidas')
        return path.join(trained_storage, name)

    def load_unknown_file_by_name(self, name):
        unknown_storage = path.join(self.storage, 'enviadas')
        return path.join(unknown_storage, name)

    def load_all(self):
        results = self.db.select('SELECT faces.user_id, faces.filename, faces.created FROM faces ')

        for row in results:
            user_id = row[0]
            filename = row[1]

            Created = row[2]
            face = {
                "User_id": user_id,
                "filename": filename,
                "Created": row[2],
            }
            self.faces.append(face)
            face_image = face_recognition.load_image_file('storage/conhecidas/'+ filename)
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def recognizer(self, unknown_image):
        results = face_recognition.compare_faces(self.known_encoding_faces, unknown_image)
        index_key = 0
        for matched in results:
            if matched:
                user_id = self.load_user_by_index_key(index_key)
                return user_id
            index_key += 1
        return None

    def locate(self, filename):
        faceImage = face_recognition.load_image_file(filename)
        face_loc = face_recognition.face_locations(faceImage)
        tam = len(face_loc)
        return tam, faceImage

    def fconfirm(self, filename):
        faceImage = face_recognition.load_image_file(filename)
        face_loc = face_recognition.face_locations(faceImage)
        tam = len(face_loc)
        return tam

    def face_detect(self, frame):
        print('facedetect')
        self.frame = frame
        tam, img = self.locate(self.frame)

        print('Tamanho = ', tam)
        face_names = []
        if tam != 0:
            if self.process_this_frame:
                face_locations = face_recognition.face_locations(img)
                face_encodings = face_recognition.face_encodings(img, face_locations)
                face_names = []
                for face_encoding in face_encodings:
                    user_id = self.recognizer(unknown_image=face_encoding)
                    name = "Desconhecido"
                    if user_id:
                        user = self.get_user_by_id(user_id)
                        name = user['name']
                        face_names.append(name)
                    else:
                        face_names.append(name)

            self.process_this_frame = not self.process_this_frame

        return face_names

    def face_detect_live(self, frame):
        self.scan_storage = path.join(self.storage, 'escaneadas')
        self.frame = frame
        small_frame = cv2.resize(self.frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = self.frame[:, :, ::-1]
        face_loc = face_recognition.face_locations(self.frame)
        tam = len(face_loc)
        face_names = []
        font = cv2.FONT_HERSHEY_SIMPLEX
        if tam != 0:
            if self.process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                face_names = []
                for face_encoding in face_encodings:
                    user_id = self.recognizer(unknown_image=face_encoding)
                    name = "Desconhecido"
                    if user_id:
                        user = self.get_user_by_id(user_id)
                        name = user['name']
                        face_names.append(name)
                    else:
                        face_names.append(name)

            self.process_this_frame = not self.process_this_frame
            for (top, right, bottom, left), name in zip(face_loc, face_names):
                cv2.rectangle(self.frame, (left, top), (right, bottom), (0, 0, 255), 1)
                cv2.putText(self.frame, name, (left, bottom - 6), font, 1.0, (255, 255, 255), 1)
            if tam == 1 and 'Desconhecido' not in face_names and len(face_names) != 0:
                cv2.imwrite(f'{self.scan_storage}/{face_names[0]}.jpeg', self.frame)
                return True, face_names[0]
            else:
                return False, face_names
        return False, face_names
