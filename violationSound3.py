from tkinter import *
from firebase_dbDecouple import firedb
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import date
from datetime import datetime
import cv2
import random
from PIL import Image, ImageTk
import winsound

#scrable the string to create unique id for the photos

def scramble_string(text):
    # Convert the string into a list of characters
    chars = list(text)
    # Shuffle the characters randomly
    random.shuffle(chars)
    # Convert the list back into a string
    scrambled_text = ''.join(chars)
    scrambled_text = scrambled_text.replace('-',"").replace(':','')
    return scrambled_text

def grab_events(new_window: Toplevel):
            new_window.grab_set()  # grab all events for the new window
            new_window.protocol("WM_DELETE_WINDOW", lambda: passport())  # handle window closing  

def close_window(window: Toplevel):
    window.grab_release()  # release the grab on all events
    window.destroy()

def passport():
     pass
#if user select revoke
                            #pass in student in the form of list, and the inference result
def violation_window(student, clothingResult, mainPage, img, gray):
    violation_window = Toplevel(mainPage.root)
    violation_window.geometry('500x720+380+200')
    violation_window.resizable(False,False)
    violation_window.title("Violation detected!")

    global acknowledge_butt
    acknowledge_butt = PhotoImage(file="images/acknowledge_butt.png")

    global revoke_butt
    revoke_butt = PhotoImage(file= "images/revoke_butt.png")

    grab_events(violation_window) #force user to interact with  add_window first.

    studentName = StringVar()
    studentID = StringVar()


    def acknowledge(window:Toplevel, studentID, mainPage):
        print('acknowledge')
        student = firedb.checkStudentBlocked(studentID)
        existStudent = firedb.checkStudentExist(studentID)

        #if student doesn't exist
        if not(existStudent):
            messagebox.showerror("Student Not Found", f"The student ID {studentID} does not exist!")  
        #if student already blocked
        elif student:
            #do nothing
            #stop the alert sound
            winsound.PlaySound(None, winsound.SND_ASYNC)
            close_window(window)
        else:
            #else if not block, add the student to the list
            today = str(date.today())
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            blockedID = firedb.BL_ID()   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
            firedb.blocked.document(blockedID).set({'date': today, 'time': current_time, 'blockedID': blockedID, 'status': '', 'studentID': studentID, 'guardID': mainPage.guardID, 'studentName': existStudent[0].to_dict()['studentName']})
            
            mainPage.table_Frame.default_stream(mainPage.guardID) #refresh the table
            
            #save picture to the cloud
            cv2.imwrite("saveid/"+ today +"-"+str(studentID) + ".jpg", gray)     
            mainPage.db1.child(today+"-"+str(studentID)).put("saveid/"+ today +"-"+ str(studentID) + ".jpg")

            #if student in the return list, remove it
            student = firedb.checkStudentReturned(studentID)
            if student:
                docs = firedb.returns.where("studentID", "==",studentID).where("date","==", str(today)).get()
            #delete the record using return ID
                for doc in docs:
                    key = doc.id
                    firedb.returns.document(key).delete()
            winsound.PlaySound(None, winsound.SND_ASYNC)
            close_window(window)
    
    
    def revoke(window:Toplevel,studentID, mainPage,img):
        #stop the alert sound
        winsound.PlaySound(None, winsound.SND_ASYNC)
        student = firedb.checkStudentBlocked(studentID)
        today = str(date.today())
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        #if already blocked, remove student from the blocked list and add to return list
        if student:
            returnID = firedb.RETURN_ID()   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
            firedb.returns.document(returnID).set({'date': today, 'time': current_time, 'returnID': returnID, 'status': '', 'studentID': student[0].to_dict()['studentID'], 'guardID': mainPage.guardID, 'studentName': student[0].to_dict()['studentName']})
            
            #get the blocked ID of the student
            docs = firedb.blocked.where("studentID", "==",studentID).where("date","==", str(today)).get()
            #delete the record using blocked ID
            for doc in docs:
                key = doc.id
                firedb.blocked.document(key).delete()

            mainPage.table_Frame.default_stream(mainPage.guardID) #refresh the table

        #save the wrongly clasified picture for future learning and annotation
        scramble_text = scramble_string(today+current_time)
        savePath = f'activeLearning/{scramble_text}.png'
        cv2.imwrite(savePath,img)
        print(savePath)

        close_window(window)

    displayFrame= Frame(violation_window)
    Label(displayFrame, text= "Alert! Violation Detected\nPlease acknowledge or revoke the violation", pady=25, font= ("Helvetica", 14),wraplength=310).grid(row=0,column=0,columnspan=2)
    
    #getStudent image
    studentImage = mainPage.getStudentPic(student[0].to_dict()['studentID'])
    imgLabel = Label(displayFrame, image=studentImage)
    imgLabel.grid(row=1,column=0, columnspan=2)

    Label(displayFrame, text= "Tips: You can insert the student ID below and press ENTER to change the student", wraplength=310).grid(row=2,column=0,sticky=E,columnspan=2,pady=(0,15), padx=(0,35))
    Label(displayFrame, text= "Student ID: ").grid(row=3,column=0,sticky=E)
    IDEntry= Entry(displayFrame, textvariable=studentID, width=15 )
    IDEntry.grid(row=3, column=1, sticky=W)

    Label(displayFrame, text= "Student Name: ").grid(row=4,column=0,sticky=E)
    Label(displayFrame, textvariable=studentName).grid(row=4, column=1, sticky=W)
    

    Label(displayFrame, text= "Reason: ").grid(row=5,column=0,sticky=E,pady=(0,25))
    Label(displayFrame, text= clothingResult , wraplength= 180).grid(row=5, column=1, sticky=W,pady=(0,25))
    #acknowledge button
    button_acknowledge = Button(displayFrame, image= acknowledge_butt, borderwidth=0, command= lambda: acknowledge(violation_window, studentID.get().upper(),mainPage))
    button_acknowledge.grid(sticky=E,row=6,column=0,pady=20, padx=18)

    #revoke button
    Button(displayFrame, image= revoke_butt, borderwidth=0, command= lambda: revoke(violation_window, studentID.get().upper(),mainPage,img=img)).grid(sticky=W,padx=18,row=6,column=1)
    

    IDEntry.insert(0,student[0].to_dict()['studentID'])
    studentName.set(student[0].to_dict()['studentName'])

    
    def IDEntryEnter(event):
            student = firedb.checkStudentExist(str(studentID.get()))
            #if student is found
            if student:
                studentName.set(student[0].to_dict()['studentName'])
                #change pic of student
                studentImage = mainPage.getStudentPic(student[0].to_dict()['studentID'])
                imgLabel.config(image= studentImage)
            else:
                messagebox.showerror("Student Not Found", f"The student ID {studentID.get()} does not exist!")       

    #when uesr press enter on the entry field
    IDEntry.bind("<Return>", IDEntryEnter)
    
    #start playing alert sound
    winsound.PlaySound("alarm.wav", winsound.SND_ASYNC | winsound.SND_ALIAS )

    displayFrame.pack()

    violation_window.wait_window()
    #the frame itself is blocked by violation_window, thus need to add code here to update the table.
    mainPage.update()

if __name__ == "__main__":
    root = Tk()
    Label(root, text=f"Hi I am here, World").pack()
    #these two variables are used to simulate the argument parsing
    student = firedb.student.where('studentID','==',"20WMR12039").get()
    clothingResult = "1 Crop_Top 1 Sleeveless 2 pants pretty"

    def func1():
        print('yayajsdlfkgj')

    violation_window(root,func1, student, clothingResult)
    root.mainloop()