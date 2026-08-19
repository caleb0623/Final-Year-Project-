import pyrebase
import os

config = {
                "apiKey": "AIzaSyA_gA8kwiNQduYHWDYcGign2NUDvOgvYUk",
                "authDomain": "trying-a2ca1.firebaseapp.com",
                "databaseURL": "https://trying-a2ca1.firebaseio.com" ,
                "projectId": "trying-a2ca1",
                "storageBucket": "trying-a2ca1.appspot.com",
                "serviceAccount" : "trying-a2ca1-firebase-adminsdk-xttcu-c56377b38d.json"
            }

firebase = pyrebase.initialize_app(config)
db1 = firebase.storage()

        #desired cloud path to be uploaded
# db1.child("students/20WMR12032").put("images/20WMR12032.jpg")
# db1.child("students/20WMR06333").put("images/20WMR06333.jpg")
# studentID = '20WMR06333'
# db1.child(f'students/{studentID}').download(filename=f"students/{studentID}.jpg", path= f'students/{studentID}')
# studentID = '20WMR12032'
# #         #cloud path                         #local path                           #cloud path
# db1.child(f'students/{studentID}').download(filename=f"students/{studentID}.jpg", path= f'students/{studentID}')