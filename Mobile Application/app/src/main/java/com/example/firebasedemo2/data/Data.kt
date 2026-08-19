package com.example.firebasedemo2.data

import com.google.firebase.firestore.DocumentId
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import java.util.*

data class Login (
    var loginID      : String = "",
    var loginPassword   : String = "",
    var status : String = "",
    var loginDate : String = "",
)

data class Blocked(
    var blockedID: String = "",
    var studentID: String = "",
    var studentName: String = "",
    var guardID: String = "",
    var date: String = "",
    var time:  String = "",
    var status:  String = ""
)


data class Return(
    var returnID: String = "",
    var studentID: String = "",
    var studentName: String = "",
    var guardID: String = "",
    var date: String = "",
    var time:  String = "",
    var status:  String = ""
)

data class Notification(
    var date: String = "",
    var totalnum : Double = 0.00
)

data class Security(
    var guardID: String= "",
    var guardName: String = "",
    var guardPassword: String = "",
    var guardPhoneNo: String = "",
    var adminID: String = "",
)

data class Lecturer(
    var lecturerID: String= "",
    var lecturerEmail: String = "",
    var lecturerName: String = "",
    var lecturerPw: String = "",
    var status : String = "",
    var loginDate : String = "",
)

data class ClassDetails(
    var classID: String= "",
    var studentID: String= "",
)

data class Class(
    var classID: String= "",
    var classTyoe: String = "",
    var lecturerID: String = "",
    var classTime: String = "",
    var classDate: String = "",
    var courseID: String = "",
)

data class Student(
    var studentID: String= "",
    var studentName: String= "",
    var studentPhoneNo: String= "",
    var studentStatus: String = "",
    var studentEmail: String = "",
    var programme: String = "",
    var yearOfStudy: Double = 0.0,
    var semester: Double = 0.0,
    var tutorialGroup: Double = 0.0,
)

data class Admin(
    var adminID: String= "",
    var adminName: String= "",
    var adminPassword: String= "",
    var adminPhoneNo: String = "",
    var adminEmail: String = "",
    var status : String = "",
    var loginDate : String = "",
)
// -------------------------------------------------------------------------------------------------

// TODO(3): Shortcuts to Firestore collections
val STUDENT = Firebase.firestore.collection("Student")
val ADMIN = Firebase.firestore.collection("admin")
val BLOCKED = Firebase.firestore.collection("blocked")
val RETURN = Firebase.firestore.collection("returns")
val CLASS = Firebase.firestore.collection("class")
val CLASSDETAILS = Firebase.firestore.collection("classDetails")
val LECTURER = Firebase.firestore.collection("lecturer")
val LOGIN = Firebase.firestore.collection("login")
val NOTIFICATION = Firebase.firestore.collection("notification")
val SECURITY = Firebase.firestore.collection("security")

// -------------------------------------------------------------------------------------------------



