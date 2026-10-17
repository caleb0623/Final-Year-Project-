package com.example.firebasedemo2.data

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
