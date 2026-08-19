from tkinter import *
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date
import re

class firestore_db:
    def __init__(self):
        cred = credentials.Certificate('trying-a2ca1-firebase-adminsdk-xttcu-c56377b38d.json')
        app = firebase_admin.initialize_app(cred)
        global db
        db = firestore.client()
        self.student = db.collection("Student")
        self.blocked = db.collection("blocked")
        self.classes = db.collection("class")
        self.classDetails = db.collection("classDetails")
        self.lecturer = db.collection('lecturer')
        self.login = db.collection('login')
        self.security = db.collection('security')
        self.admin = db.collection('admin')
        self.returns = db.collection('returns')

    def checkStudentExist(self, studentID):
        if studentID !="Enter student ID to search".upper():
            studentID = studentID.upper()
            student = firedb.student.where("studentID", "==",studentID).get()
    
            #if ID not found
            if len(student) ==0:
                return False
            else:
                return student
            
    def checkStudentReturned(self, studentID):
        studentID = studentID.upper()
        student = firedb.returns.where("studentID", "==",studentID).get()
        #if ID not found
        if len(student) ==0:
            return False
        else:
            return student

    def checkStudentBlocked(self, studentID):
        today = date.today()
        studentID = studentID.upper()
        if studentID !="Enter student ID to search".upper():
            student = firedb.blocked.where("studentID", "==",studentID).where("date","==", str(today)).get()
            #if ID blocked
            if len(student) ==0:
                return False
            else:
                return student
                # messagebox.showerror("Already blocked", f"The student ID {studentID} is already blocked!")

    ##function to generate new returnID
    def RETURN_ID(self):
        returns_ref = self.returns
        docs = returns_ref.stream()
        newid = "R00000001"
        biggest = 0
        for doc in docs:
            name1 = doc.to_dict()['returnID']
            num = re.findall(r'\d+', name1)
            converted = int(num[0])
            if converted > biggest:
                biggest = converted
        new = biggest + 1
        convertagain = str(new)
        newidnum = convertagain.zfill(8)
        newid = "R" + newidnum

        return newid
    
    #function to generate new blockedID
    def BL_ID(self):
            blocked_ref = self.blocked
            docs = blocked_ref.stream()
            newid = "BL00000001"
            biggest = 0
            for doc in docs:
                name1 = doc.to_dict()['blockedID']
                num = re.findall(r'\d+', name1)
                converted = int(num[0])
                if converted > biggest:
                    biggest = converted
            new = biggest + 1
            convertagain = str(new)
            newidnum = convertagain.zfill(8)
            newid = "BL" + newidnum

            return newid
    
firedb = firestore_db()