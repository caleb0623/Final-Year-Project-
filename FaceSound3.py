import cv2
import numpy as np
from tkinter import Tk, Button, Canvas, messagebox, Label, StringVar, Entry, BOTH, END, LEFT,RIGHT, ttk, Frame, Toplevel, PhotoImage
from PIL import Image, ImageFont, ImageTk
import pickle
from firebase_dbDecouple import firedb
from detect_cleaning import detect
from violationSound3 import violation_window
from datetime import date
from datetime import datetime

face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
clothingDetector = detect('tiny6.pt')

def faceResult(cam, names, faces, gray, recognizer, font, img):
    for(x,y,w,h) in faces:
        T = True
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        #student id and confidence
        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])

        # Check if confidence is less them 100 ==> "0" is perfect match
        #print(confidence)
        #if confidence <= 70 :
        if (confidence < 500):
            id = names[id]
            #confidence = "  {0}%".format(round(100 - confidence))
            confidence = int( 100 * (1 - (confidence)/400) )

            #if student detected
            if confidence >= 80:
                confidence = "  {0}%".format(round(confidence))
                studentID = str(id) #student id
                student = firedb.student.where('studentID','==',studentID).get()
                stname = student[0].to_dict()['studentName']
                cv2.putText(img, stname, (x+5,y-5), font, 1, (255,255,255), 2)
                cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)

                #return the stduent in the form of a list with size 1, so student[0].to_dict()['studentName'] to access it
                result = [student, gray[y:y+h,x:x+w]]
                return result

            else:#less than 80 not a person
                stname = "unknown"
                confidence = "  {0}%".format(round(confidence))

                cv2.putText(img, stname, (x+5,y-5), font, 1, (255,255,255), 2)
                cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
            
        else: #no face detected
            stname = "unknown"
            #confidence = "  {0}%".format(round(100 - confidence))

            cv2.putText(img, stname, (x+5,y-5), font, 1, (255,255,255), 2)
            #cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)

def faceRecognition(mainPage):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read('trainer/trainer.yml')
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Starting realtime video capture
    cam = cv2.VideoCapture(0)
    cam.set(3, 1280) # set video widht
    cam.set(4, 720) # set video height

    # Define min window size to be recognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    with open('names.pkl', 'rb') as f:
        names = pickle.load(f)

    #used to control the detection module
    whileFlag = True
    #used to indicate whether window is popup or not
    detectFlag = False
    

    while whileFlag==True:
        #if the no detection (detectFlag = false), continue reading the face, else do not read the frames.
        #need to let popupwindow control the detectFlag.
        if not detectFlag:
            ret, img =cam.read()
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            
            #results of face
            faces = face_detector.detectMultiScale( 
                gray,
                scaleFactor = 1.3,
                minNeighbors = 5,
                minSize = (int(minW), int(minH)),
            )
            #count = 0
            #if face detected
            if faces is not ():
                result = faceResult(cam= cam, names= names,faces= faces, gray=gray,recognizer= recognizer, font=font, img= img)
                 
                #if student is detected
                if result:
                    student = result[0]                                     #the picture already have bbox because pass by reference
                    clothesInference= clothingDetector.inference(img)
                    studentID = student[0].to_dict()['studentID']
                    #if improper clothes are detected
                    if clothesInference:
                        #print result of the inference
                        clothingResult= clothesInference[0]
                        print(clothingResult,'\n')

                        #set detectFlag = true, indicate that there is a detection, the system stop reading faces.
                        detectFlag = True
                        # whileFlag = False #break the loop
                        

                     #if blocked student coming back with proper clothing, remove them from blocked list and add them to return list
                    elif firedb.checkStudentBlocked(studentID):
                        today = str(date.today())
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        returnID = firedb.RETURN_ID()   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
                        firedb.returns.document(returnID).set({'date': today, 'time': current_time, 'returnID': returnID, 'status': '', 'studentID': student[0].to_dict()['studentID'], 'guardID': mainPage.guardID, 'studentName': student[0].to_dict()['studentName']})
                        
                        #get the blocked ID of the student
                        docs = firedb.blocked.where("studentID", "==",studentID).where("date","==", str(today)).get()
                        #delete the record using blocked ID
                        for doc in docs:
                            key = doc.id
                            firedb.blocked.document(key).delete()

                        mainPage.table_Frame.default_stream(mainPage.guardID) #refresh the table
            
            cv2.imshow('camera',img) #what if I dont show? Still cannot interact with anything, and no way to exit
            # if detectFlag:
            #     cv2.destroyAllWindows()

            k = cv2.waitKey(1) & 0xff # Press 'ESC' for exiting video
            # if k == 27 or cv2.getWindowProperty('camera',cv2.WND_PROP_VISIBLE) < 1:
            if k == 27 or cv2.getWindowProperty('camera',cv2.WND_PROP_VISIBLE) < 1:
                # detectFlag = False #detectFlag = false, continue reading face
                whileFlag = False
                cam.release()
                cv2.destroyAllWindows()
            
            
            if detectFlag:
                print('yes detected')
                violation_window(mainPage= mainPage, student = student, clothingResult=clothingResult,
                                    img = clothesInference[1], gray = result[1]) #clohtesInference[1] here is image without clohing bbox
                detectFlag = False
                print(detectFlag) 


    #if detection raised and no window is currently popup
    # cam.release()
    # cv2.destroyAllWindows()