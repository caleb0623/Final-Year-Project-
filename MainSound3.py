from tkinter import *
from PIL import ImageTk, Image 
from framesRemove import tableFrame, CRUDFrame
from firebase_dbDecouple import firedb
from tkinter import messagebox
from datetime import date
from datetime import datetime
from FaceSound3 import faceRecognition
import pyrebase
class MainPage(Frame):
    def __init__(self, master: Tk, guardID):
        super().__init__(master)
        self.root = master
        self.root.title("Clothing Detection System")
        self.root.geometry("1280x800+380+220")
        self.root.resizable(False,False)
        self.configure(bg="white")
        self.root.iconbitmap('images/favicon.ico')
        self.guardID = guardID
        
        config = {
                "apiKey": "AIzaSyA_gA8kwiNQduYHWDYcGign2NUDvOgvYUk",
                "authDomain": "trying-a2ca1.firebaseapp.com",
                "databaseURL": "https://trying-a2ca1.firebaseio.com" ,
                "projectId": "trying-a2ca1",
                "storageBucket": "trying-a2ca1.appspot.com",
                "serviceAccount" : "trying-a2ca1-firebase-adminsdk-xttcu-c56377b38d.json"
            }

        #database that store student images
        firebase = pyrebase.initialize_app(config)
        self.db1 = firebase.storage()

        #Images for buttons
        global monitor_butt
        monitor_butt = PhotoImage(file="images/monitor_butt_selected.png")

        global add_butt
        global delete_butt
        global update_butt
        
        add_butt = PhotoImage(file='images/add_butt.png')
        delete_butt = PhotoImage(file='images/delete_butt.png')
        update_butt = PhotoImage(file='images/update_butt.png')
        


        #start of caleb part##################################################################################


##########################################--declare navigation Frame--################################
        self.nav_Frame = Frame(self.root)
        
        #navigation pages_Frame
        self.pages_Frame = Frame(self.nav_Frame)
        #buttons
        button_monitor = Button(self.pages_Frame, image=monitor_butt, borderwidth=0, command= lambda: faceRecognition(self))
        #buttons events

        #self.pages_Frame positioning
        Label(self.pages_Frame, text="",padx=45).pack(side= LEFT) #first empty column
        button_monitor.pack(side= LEFT)


        #navigation search_Frame
        self.search_Frame = Frame(self.nav_Frame)
        studentID = StringVar()    
        searchEntry = Entry(self.search_Frame, width=21, textvariable= studentID)  #entry field
        searchEntry.insert(0,"Enter student ID to search")
        searchEntry.configure(state= DISABLED)

        #events of search entry field
        #user click at the search entry field
        def on_click(event):
            searchEntry.configure(state=NORMAL)
            #delete placeholder
            if studentID.get() == "Enter student ID to search":
                searchEntry.delete(0,END)

        #user focs on other area
        def searchEntry_leave(e):
            if studentID.get():
                pass
            else:
                searchEntry.delete(0,END) #insert placeholder
                searchEntry.insert(0,"Enter student ID to search")
                searchEntry.configure(state= DISABLED)

        #user press enter
        def studentQueryEnter(e):
            if studentID.get(): #if there is anything in the input field
                ID = str(studentID.get())
                ID = ID.upper()
                self.table_Frame.studentID_query(ID)
            else: #if nothing in the field, display default table
                self.table_Frame.default_stream(self.guardID)
            

        searchEntry.bind('<Button-1>', on_click)
        searchEntry.bind('<FocusOut>', searchEntry_leave)
        searchEntry.bind("<Return>", studentQueryEnter)



        #search student button
        def studentQuery():
            if studentID.get(): #if there is anything in the input field
                ID = str(studentID.get())
                ID = ID.upper()
                self.table_Frame.studentID_query(ID)
            else: #if nothing in the field, display default table
               self.table_Frame.default_stream(self.guardID)

        button_searchStudent= Button(self.search_Frame, text= "Search Student", width= 20, borderwidth=2,command=studentQuery)


        #clear button
        def clear():
            searchEntry.delete(0,END)
        button_clear= Button(self.search_Frame, text= "Clear", bg="#ff8886",command=clear)

        #self.search_Frame positioning
        searchEntry.pack(side=LEFT, padx=(0,20))
        button_searchStudent.pack(side= LEFT)
        button_clear.pack(side=LEFT)


        #navigation positioning
        self.pages_Frame.pack(side=LEFT)

        self.search_Frame.pack(side=RIGHT, padx=(402,0))

        self.nav_Frame.pack(pady=20,anchor=W)
 ####################################################--END of nav_Frame--########################################


###################################################--declare table frame--#######################################
        self.table_Frame = tableFrame(self.root, guardID=self.guardID)

        #event for reset table button
        def resetTable(e):
            self.table_Frame.default_stream(self.guardID) #display default table

        self.table_Frame.button_reset.bind("<Button-1>", resetTable)
        self.table_Frame.pack(anchor=W)
####################################################--END of table Frame--########################################
        def grab_events(new_window: Toplevel):
            new_window.grab_set()  # grab all events for the new window
            new_window.protocol("WM_DELETE_WINDOW", lambda: close_window(new_window))  # handle window closing  

        def close_window(window: Toplevel):
            window.grab_release()  # release the grab on all events
            window.destroy()
###################################################--declare CRUD frame--#######################################
                                #passing in images
        self.CRUD_Frame = CRUDFrame(self.root, add_butt, delete_butt, update_butt)

        #contents of button_add logic
        self.CRUD_Frame.button_add.config(command= lambda: add_window(self.root))
        self.CRUD_Frame.button_delete.config(command= lambda: delete_window(self.root))
        self.CRUD_Frame.button_update.config(command= lambda: update_window(self.root))
        

        #popup windows for add_record
        def add_window(root: Tk):
            add_window = Toplevel(root)
            add_window.geometry('500x416+550+400')
            add_window.resizable(False,False)
            add_window.title("Add Record")
            
            global add_butt_green
            add_butt_green = PhotoImage(file="images/add_butt_green1.png")

            global cancel_butt
            cancel_butt = PhotoImage(file= "images/cancel_butt.png")

            grab_events(add_window) #force user to interact with  add_window first.

            global add_studentID
            add_studentID = StringVar()
            EntryFrame = Frame(add_window)
            #entry field
            Label(EntryFrame, text= "Enter the student ID: ", font=("Arial",12)).pack(side=LEFT)
            Entry_studentID= Entry(EntryFrame, textvariable= add_studentID, width=21)
            Entry_studentID.pack(side=LEFT)
            Entry_studentID.focus_set()

            EntryFrame.pack(anchor=N, pady=(70,0))

            buttonFrame = Frame(add_window)
            #add record button
            button_add_green = Button(buttonFrame, image= add_butt_green,borderwidth=0, command= lambda: addRecord(Entry_studentID))
            button_add_green.pack(anchor=W, padx=(50,18),side=LEFT)
            #cancel button
            Button(buttonFrame, image= cancel_butt,borderwidth=0, command= lambda: close_window(add_window)).pack(anchor=E, padx=(18,50))

            #add record based on user input and error checking    
            def addRecord(Entry_studentID: Entry):
                global add_studentID
                ID = str(add_studentID.get()).upper()
                student = firedb.checkStudentExist(ID)
                #if student not found
                if not (student):
                    messagebox.showerror("Student Not Found", f"The student ID {ID} does not exist!")
                
                elif firedb.checkStudentBlocked(ID):
                    messagebox.showerror("Already Blocked", f"The student ID {ID} is already blocked today!")

                #if student is eligible for blocking
                else: 
                    name = student[0].to_dict()['studentName']
                    response = messagebox.askyesno("Confirmation for adding record",
                                                f"Confirm adding {ID} {name}?")

                    if response == 1: #if user confirm yes
                        # guardID = "SG00001"
                        #1. need to pass in guard ID here from caleb
                        today = str(date.today())
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        blockedID = firedb.BL_ID()   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
                        firedb.blocked.document(blockedID).set({'date': today, 'time': current_time, 'blockedID': blockedID, 'status': '', 'studentID': ID, 'guardID': self.guardID, 'studentName': name})
                        #need to add all details here
                        student = firedb.checkStudentReturned(ID)
                        #if student exist in return table.
                        if student:
                            docs = firedb.returns.where("studentID", "==",ID).where("date","==", str(today)).get()
                        #delete the record using return ID
                            for doc in docs:
                                key = doc.id
                                firedb.returns.document(key).delete()
                        Entry_studentID.delete(0,END) #clear off the field for next input
                        self.table_Frame.default_stream(self.guardID) #refresh the table

            #if user press enter on the entry field
            def addEntryEnter(e):
                addRecord(Entry_studentID)

            Entry_studentID.bind("<Return>", addEntryEnter)
            
            

            buttonFrame.pack(pady=70)

        #popup windows for delete_record
        def delete_window(root:Tk):
            delete_window = Toplevel(root)
            delete_window.geometry('500x416+550+400')
            delete_window.resizable(False,False)
            delete_window.title("Delete Record")
            selected = 0 #Flag to check user has selected a record default: false

            global delete_butt_green
            delete_butt_green = PhotoImage(file="images/delete_butt_green.png")

            global cancel_butt
            cancel_butt = PhotoImage(file= "images/cancel_butt.png")

            grab_events(delete_window) #force user to interact with  add_window first.

            
            #prompt user confirmation to delete the record
            try:
                tree = self.table_Frame.tree
                item = tree.selection()[0]
                selected =1
            except:
                selected =0
                delete_window.destroy()
                messagebox.showerror("No record selected","No record is selected!")
            
            if selected ==1: #if user has selected a record, proceed to create frame.
                displayFrame= Frame(delete_window)
                Label(displayFrame, text= "Are you sure that you want to delete this record?", pady=25, font= ("Helvetica", 14),wraplength=310).grid(row=0,column=0,columnspan=2)
                Label(displayFrame, text= "Blocked ID: ").grid(row=1,column=0,sticky=E)
                Label(displayFrame, text =tree.item(item)['values'][0]).grid(row=1, column=1, sticky=W)
                Label(displayFrame, text= "Time Stamp: ").grid(row=2,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][1]).grid(row=2, column=1, sticky=W)
                Label(displayFrame, text= "Student Name: ").grid(row=3,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][2]).grid(row=3, column=1, sticky=W)
                Label(displayFrame, text= "Student ID: ").grid(row=4, column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][3]).grid(row=4, column=1, sticky=W)
                Label(displayFrame, text= "Guard ID: ").grid(row=5,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][4]).grid(row=5, column=1, sticky=W)

                #delete the record from blocked list in the database.
                def deleteRecord(delete_window):                                                             #student ID                   #student Name
                    response= messagebox.askyesno("Confirmation for deleting record", f"Confirm deleting {tree.item(item)['values'][3]} {tree.item(item)['values'][2]} from the list?")
                    if response ==1:            
                        #add to return table
                        today = str(date.today())
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        returnID = firedb.RETURN_ID()   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
                        firedb.returns.document(returnID).set({'date': today, 'time': current_time, 'returnID': returnID, 'status': '', 'studentID': tree.item(item)['values'][3], 'guardID': guardID, 'studentName': tree.item(item)['values'][2]})
                        
                        #delete using blocked ID
                        firedb.blocked.document(tree.item(item)['values'][0]).delete()
                        self.table_Frame.default_stream(self.guardID)   #refresh table
                        close_window(delete_window)

                #delete button
                button_delete_green = Button(displayFrame, image= delete_butt_green, borderwidth=0,command= lambda: deleteRecord(delete_window))
                button_delete_green.grid(sticky=E,row=6,column=0,pady=20, padx=18)
                Button(displayFrame, image= cancel_butt, borderwidth=0, command= lambda: close_window(delete_window)).grid(sticky=W,padx=18,row=6,column=1)

                displayFrame.pack()

        #popup windows for update_record
        def update_window(root: Tk):
            update_window = Toplevel(root)
            update_window.geometry('500x416+550+400')
            update_window.resizable(False,False)
            update_window.title("Update Record")
            selected = 0 #Flag to check user has selected a record default: false

            global update_butt_green
            update_butt_green = PhotoImage(file="images/update_butt_green.png")

            global cancel_butt
            cancel_butt = PhotoImage(file= "images/cancel_butt.png")

            global correctStudentID
            correctStudentID = StringVar()

            grab_events(update_window) #force user to interact with  add_window first.

            def updateRecord():
                global correctStudentID
                ID = str(correctStudentID.get()).upper()
                student = firedb.checkStudentExist(ID)
                #if student not found
                if not (student):
                    messagebox.showerror("Student Not Found", f"The student ID {ID} does not exist!")
                
                elif firedb.checkStudentBlocked(ID):
                    messagebox.showerror("Already Blocked", f"The student ID {ID} is already blocked today!")
                
                #if student is eligible for updating
                else:
                    name = student[0].to_dict()['studentName']
                    response = messagebox.askyesno("Confirmation for updating record",
                                                f"Confirm updating the record to {ID} {name}?")
                    if response == 1: #if user confirm yes
                        # guardID = "SG00001"
                        # #1. need to pass in guard ID here from caleb
                        today = str(date.today())
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        blockedID = tree.item(item)['values'][0]   #maybe need to use self.guardID here, the self.guardID by passing the value from login page
                        firedb.blocked.document(blockedID).update({'date': today, 'time': current_time, 'studentID': ID, 'studentName': name, 'guardID': self.guardID})
                        
                        #if student exist in return table. line 353 to 359 are added last minute
                        if student:
                            docs = firedb.returns.where("studentID", "==",ID).where("date","==", str(today)).get()
                        #delete the record using return ID
                            for doc in docs:
                                key = doc.id
                                firedb.returns.document(key).delete()

                        #need to destroy window here
                        close_window(update_window)
                        self.table_Frame.default_stream(self.guardID) #refresh the table
            
            #prompt user confirmation to delete the record
            try:
                tree = self.table_Frame.tree
                item = tree.selection()[0]
                selected =1
            except:
                selected =0
                update_window.destroy()
                messagebox.showerror("No record selected","No record is selected!")
            
            if selected ==1: #if user has selected a record, proceed to create frame.
                #use frame to display the details
                displayFrame= Frame(update_window)
                Label(displayFrame, text= "Update this record with correct student ID", pady=25, font= ("Helvetica", 14),wraplength=300).grid(row=0,column=0,columnspan=2)
                Label(displayFrame, text= "Blocked ID: ").grid(row=1,column=0,sticky=E)
                Label(displayFrame, text =tree.item(item)['values'][0]).grid(row=1, column=1, sticky=W)
                Label(displayFrame, text= "Time Stamp: ").grid(row=2,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][1]).grid(row=2, column=1, sticky=W)
                Label(displayFrame, text= "Student Name: ").grid(row=3,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][2]).grid(row=3, column=1, sticky=W)
                Label(displayFrame, text= "Student ID: ").grid(row=4, column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][3]).grid(row=4, column=1, sticky=W)
                Label(displayFrame, text= "Guard ID: ").grid(row=5,column=0,sticky=E)
                Label(displayFrame, text=tree.item(item)['values'][4]).grid(row=5, column=1, sticky=W)
                
                #Entry field for entering correct student ID
                Label(displayFrame, text='Enter the correct Student ID: ').grid(row=6,column=0,sticky=E, pady=18)
                Entry_correctStudentID = Entry(displayFrame, textvariable= correctStudentID)
                Entry_correctStudentID.grid(row=6, column=1, sticky=W)
                Entry_correctStudentID.focus_set()

                #update record button
                button_update = Button(displayFrame, image= update_butt_green, borderwidth=0, command= updateRecord)
                button_update.grid(sticky=E,row=7,column=0,pady=12, padx=18)

                 #cancel button
                Button(displayFrame, image= cancel_butt, borderwidth=0, command= lambda: close_window(update_window)).grid(sticky=W,padx=18,row=7,column=1)
                
                #allow user to update the record using enter
                def updateEntryEnter(e):
                    updateRecord()

                Entry_correctStudentID.bind("<Return>", updateEntryEnter)

                displayFrame.pack()

        
        
        self.CRUD_Frame.pack(pady= 20)
###################################################--end of CRUD frame--#######################################    
        Label(self.root, text=f"Hi, welcome aboard, {self.guardID}").pack()

    #this image is used for identity purpose later in violation window
    def getStudentPic(self, studentID):
        #try to read from local storage
        try:
            image = Image.open(f'students/{studentID}.jpg')
        #if cannot, download the photo from online database and read again
        except:
            print('photo not here')
                                #cloud path                         #local path                           #cloud path
            self.db1.child(f'students/{studentID}').download(filename=f"students/{studentID}.jpg", path= f'students/{studentID}')
            image = Image.open(f'students/{studentID}.jpg')
            # create a PhotoImage object from the resized image
        image = image.resize((250, 333), Image.ANTIALIAS)
        global photo
        photo = ImageTk.PhotoImage(image)
        return photo

        

if __name__ == '__main__':
    root = Tk()

    test = MainPage(root, 'SG00001')
    test.pack()
    root.mainloop()