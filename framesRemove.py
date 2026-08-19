from tkinter import*
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore
from tkinter.ttk import Treeview
#from firebase_db import firedb
from firebase_dbDecouple import firedb
from tkinter import ttk
from tkinter import messagebox
from firebase_admin import firestore
from datetime import date


# from CRUD_eventsRefresh import add_window
# Use a service account.
# cred = credentials.Certificate('trying-a2ca1-firebase-adminsdk-xttcu-1708fa60e6.json')

# app = firebase_admin.initialize_app(cred)

# db = firestore.client()

# blocked_ref = db.collection("blocked")

class tableFrame(Frame):
    def __init__(self, master: Tk,guardID):
        super().__init__(master)
        #self.place(x=100,y=10, width=1080, height= 540)

        Label(self,padx=45).pack(side=LEFT) #padding at left handside
        self.button_reset = Button(self, text="Reset Table", bg='#ff8886')
        self.button_reset.pack(anchor=E,padx=17)
        scrollBar= Scrollbar(self)
        scrollBar.pack(side= RIGHT, fill= Y)

        master = ttk.Style()
        master.configure("Treeview", rowheight=22)
        
        self.tree = Treeview(self, 
                        columns= ("c1","c2","c3","c4","c5"),
                        show= "headings",
                        yscrollcommand=scrollBar.set,
                        selectmode= "browse"
                        ,height=20)

        self.tree.column("c1", width= 220, anchor= CENTER)                
        self.tree.column("c2", width= 220, anchor= CENTER)     
        self.tree.column("c3", width= 220, anchor= CENTER)     
        self.tree.column("c4", width= 220, anchor= CENTER)     
        self.tree.column("c5", width= 220, anchor= CENTER)     

        self.tree.heading("c1", text="Blocked ID")
        self.tree.heading("c2", text="Time Stamp")
        self.tree.heading("c3", text="Student Name")
        self.tree.heading("c4", text="Student ID")
        self.tree.heading("c5", text="Guard ID")

        self.tree.pack(side=LEFT, fill=Y)

        scrollBar.config(command= self.tree.yview)

        #add variables of time and date here to set the data date range
        #need to show today block list only, maybe
        self.default_stream(guardID)
        # self.docs = firedb.blocked.order_by("date", direction=firestore.Query.DESCENDING).order_by("time", direction=firestore.Query.DESCENDING).stream()
    
        # for i, doc in enumerate(self.docs):
        #     x = doc.to_dict()
        #     self.tree.insert('',i,
        #                 values=[x["blockedID"],
        #                         x["date"] + " " + x ["time"],
        #                         x["studentName"],
        #                         x["studentID"],
        #                         x["guardID"]])

    #default table
    def default_stream(self, guardID):
        today = str(date.today()) 
        self.docs= firedb.blocked.where(
            'date','==',today).where(
            'guardID','==',guardID).order_by(
            "time", direction=firestore.Query.DESCENDING).stream()
        #delete current table 
        x = self.tree.get_children()         
        for item in x:             
            self.tree.delete(item)
        
        #insert query table
        for i, doc in enumerate(self.docs):
            x = doc.to_dict()
            self.tree.insert('',i,
                        values=[x["blockedID"],
                                x["date"] + " " + x ["time"],
                                x["studentName"],
                                x["studentID"],
                                x["guardID"]])
    
    #query using studentID
    # def studentID_query(self,studentID):
    #     #acquire query from database
    #     self.docs = firedb.blocked.where("studentID", "==",studentID).get()

    #     #error handling - student not found
    #     if len(self.docs) == 0:
    #         messagebox.showerror("Student Not Found", "The student ID does not exist!")
    #     else:
    #         #delete current table 
    #         x = self.tree.get_children()         
    #         for item in x:             
    #             self.tree.delete(item)
            
    #         #insert query table
    #         for i, doc in enumerate(self.docs):
    #             x = doc.to_dict()
    #             self.tree.insert('',i,
    #                         values=[x["blockedID"],
    #                                 x["date"] + " " + x ["time"],
    #                                 x["studentName"],
    #                                 x["studentID"],
    #                                 x["guardID"]])
    def studentID_query(self,studentID):
        today = str(date.today()) 
        #acquire query from database
        exist = firedb.checkStudentExist(studentID)

        #if student exist in database
        if exist:
            #delete current table 
            x = self.tree.get_children()         
            for item in x:             
                self.tree.delete(item)

            #search for student in blocked list
            self.docs = firedb.blocked.where(
                'date','==',today).where(
                "studentID", "==",studentID).order_by(
                "time", direction=firestore.Query.DESCENDING).get()
                #insert query table, if record not found, the table is empty
            for i, doc in enumerate(self.docs):
                x = doc.to_dict()
                self.tree.insert('',i,
                            values=[x["blockedID"],
                                    x["date"] + " " + x ["time"],
                                    x["studentName"],
                                    x["studentID"],
                                    x["guardID"]])
            if not(self.docs):
                messagebox.showinfo("No record found", f"The student ID {studentID} is not blocked today")
        else:
            messagebox.showerror("Student Not Found", f"The student ID {studentID} does not exist!")
    
    
#CRUD buttons
class CRUDFrame(Frame):
    def __init__(self, master: Tk, add_butt, delete_butt, update_butt) :
        super().__init__(master)
        Label(self,padx=45).pack(side=LEFT)   #inside a function, image must use global
                                                                                    #add_window from CRUD_events
        self.button_add= Button(self, image=add_butt, borderwidth=0)#, command=lambda: add_window(master))
        self.button_add.pack(side= LEFT)

        self.button_delete= Button(self, image=delete_butt, borderwidth=0)
        self.button_delete.pack(side= LEFT, padx=72)

        self.button_update= Button(self, image=update_butt, borderwidth=0)
        self.button_update.pack(side= LEFT, padx=(0,72))


if __name__ == "__main__":
    root = Tk()
    root.geometry("1280x800")
    root.resizable(False,False)
    add_butt = PhotoImage(file='images/add_butt.png')
    delete_butt = PhotoImage(file='images/delete_butt.png')
    update_butt = PhotoImage(file='images/update_butt.png')
    report_butt = PhotoImage(file= 'images/report_butt.png')
    tableFrame(root).pack()
    CRUDFrame(root, add_butt, delete_butt, update_butt, report_butt).pack(anchor=W)

    root.mainloop()