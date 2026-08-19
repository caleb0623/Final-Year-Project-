package com.example.firebasedemo2.ui.User

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.StrictMode
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.AppExecutors
import com.example.firebasedemo2.NotificationActivity
import com.example.firebasedemo2.R
import com.example.firebasedemo2.SecurityActivity
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentAddsgBinding
import com.example.firebasedemo2.databinding.FragmentForgetpwBinding
import kotlinx.coroutines.launch
import javax.mail.internet.InternetAddress
import java.util.Properties
import javax.mail.*
import javax.mail.internet.MimeMessage


class ForgetPwFragment : Fragment() {

    private lateinit var binding: FragmentForgetpwBinding
    private val nav by lazy { findNavController() }
    private val vm: AuthViewModel by activityViewModels()
    private val vm1: Auth1ViewModel by activityViewModels()
    lateinit var appExecutors: AppExecutors
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentForgetpwBinding.inflate(inflater, container, false)
        binding.btnAddCardPayment.setOnClickListener { add()}
        binding.btnReset.setOnClickListener { reset() }
        binding.btnClose.setOnClickListener {nav.navigateUp() }
        appExecutors = AppExecutors()
        context?.let { super.onAttach(it) }
        return binding.root
    }

    private fun reset() {
        binding.edtUserID.text.clear()
        binding.edtPw.text.clear()
        binding.edtPw2.text.clear()

        binding.edtUserID.requestFocus()
    }

    private fun add() {
        var userID = binding.edtUserID.text.toString().trim()
        var pw = binding.edtPw2.text.toString().trim()
        var pw1 = binding.edtPw.text.toString().trim()

        if (userID == "" || pw == "" || pw1 == "") {
            toast("Please fill up the columns!")
        } else {
            LECTURER.whereEqualTo("lecturerID", userID)
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        var myemail = "calebckl-wp19@student.tarc.edu.my"
                        var mypw = "990623127071"

                        var password = doc.getString("lecturerPw").toString()
                        var email = doc.getString("lecturerEmail").toString()
                        if (pw == pw1) {
                            if(pw == password || pw1 == password){
                                toast("Your password cannot same with the previous one!")
                            }
                            else{
                                val r1 = (0..9).random()
                                val r2 = (0..9).random()
                                val r3 = (0..9).random()
                                val r4 = (0..9).random()
                                val random = r1.toString() + r2.toString() + r3.toString() + r4.toString()
                                val messages =
                                    "Your code is $random.\n\n\n\n Please do not reply to this email, this is an auto generated email."
                                val subject = "Auto generated message for resetting your password"

                                appExecutors.diskIO().execute {
                                    val props = System.getProperties()
                                    props.put("mail.smtp.host", "smtp.gmail.com")
                                    props.put("mail.smtp.socketFactory.port", "465")
                                    props.put("mail.smtp.socketFactory.class", "javax.net.ssl.SSLSocketFactory")
                                    props.put("mail.smtp.auth", "true")
                                    props.put("mail.smtp.port", "465")

                                    val session =  Session.getInstance(props,
                                        object : javax.mail.Authenticator() {
                                            //Authenticating the password
                                            override fun getPasswordAuthentication(): PasswordAuthentication {
                                                return PasswordAuthentication(myemail, mypw)
                                            }
                                        })

                                    try {
                                        //Creating MimeMessage object
                                        val mm = MimeMessage(session)
                                        val emailId = email
                                        //Setting sender address
                                        mm.setFrom(InternetAddress(myemail))
                                        //Adding receiver
                                        mm.addRecipient(Message.RecipientType.TO,
                                            InternetAddress(emailId))
                                        //Adding subject
                                        mm.subject = subject
                                        //Adding message
                                        mm.setText(messages)

                                        //Sending email
                                        Transport.send(mm)

                                        appExecutors.mainThread().execute {
                                            //Something that should be executed on main thread.
                                        }

                                    } catch (e: MessagingException) {
                                        e.printStackTrace()
                                    }
                                }


                                nav.navigate(R.id.verifyFragment, bundleOf("id" to userID,"random" to random, "password" to pw))
                            }
                        } else {
                            toast("The password you entered is different!")
                        }
                    }
                }


            ADMIN.whereEqualTo("adminID", userID)
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        var myemail = "calebckl-wp19@student.tarc.edu.my"
                        var mypw = "990623127071"

                        var password = doc.getString("adminPassword").toString()
                        var email = doc.getString("adminEmail").toString()
                        if (pw == pw1) {
                            if(pw == password || pw1 == password){
                                toast("Your password cannot same with the previous one!")
                            }
                            else{
                                val r1 = (0..9).random()
                                val r2 = (0..9).random()
                                val r3 = (0..9).random()
                                val r4 = (0..9).random()
                                val random = r1.toString() + r2.toString() + r3.toString() + r4.toString()
                                val messages =
                                    "Your code is $random.\n\n\n\n Please do not reply to this email, this is an auto generated email."
                                val subject = "Auto generated message for resetting your password"

                                appExecutors.diskIO().execute {
                                    val props = System.getProperties()
                                    props.put("mail.smtp.host", "smtp.gmail.com")
                                    props.put("mail.smtp.socketFactory.port", "465")
                                    props.put("mail.smtp.socketFactory.class", "javax.net.ssl.SSLSocketFactory")
                                    props.put("mail.smtp.auth", "true")
                                    props.put("mail.smtp.port", "465")

                                    val session =  Session.getInstance(props,
                                        object : javax.mail.Authenticator() {
                                            //Authenticating the password
                                            override fun getPasswordAuthentication(): PasswordAuthentication {
                                                return PasswordAuthentication(myemail, mypw)
                                            }
                                        })

                                    try {
                                        //Creating MimeMessage object
                                        val mm = MimeMessage(session)
                                        val emailId = email
                                        //Setting sender address
                                        mm.setFrom(InternetAddress(myemail))
                                        //Adding receiver
                                        mm.addRecipient(Message.RecipientType.TO,
                                            InternetAddress(emailId))
                                        //Adding subject
                                        mm.subject = subject
                                        //Adding message
                                        mm.setText(messages)

                                        //Sending email
                                        Transport.send(mm)

                                        appExecutors.mainThread().execute {
                                            //Something that should be executed on main thread.
                                        }

                                    } catch (e: MessagingException) {
                                        e.printStackTrace()
                                    }
                                }


                                nav.navigate(R.id.verifyFragment, bundleOf("id" to userID,"random" to random, "password" to pw))
                            }
                        } else {
                            toast("The password you entered is different!")
                        }
                    }
                }
        }


    }

        private fun toast(text: String) {
            Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
        }
    }
