package com.example.firebasedemo2.ui

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.*
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentHomeBinding
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.launch
import org.greenrobot.eventbus.EventBus
import java.text.DecimalFormat
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class HomeFragment : Fragment() {

    private lateinit var binding: FragmentHomeBinding
    private val nav by lazy { findNavController() }
    private val vm: NotificationViewModel by activityViewModels()
    private val formatter1 = DecimalFormat("0")
    private val auth: AuthViewModel by activityViewModels()
    private val auth1: Auth1ViewModel by activityViewModels()
    var admin = false
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentHomeBinding.inflate(inflater, container, false)
        binding.btnLogin.setOnClickListener { login1() }
        binding.btnForgetPassword.setOnClickListener {
            nav.navigate(R.id.forgetpwFragment) }

        return binding.root
    }

    private fun login1() {

        val ctx      = requireContext()
        var id   = binding.edtID.text.toString().trim()
        var password = binding.edtPassword.text.toString().trim()
        var status = "logined"
        val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")
        val current = LocalDateTime.now().format(formatter)
        var cid = ""
        var stuid = ""


        // TODO(3): Login -> auth.login(...)
        //          Clear navigation backstack


        lifecycleScope.launch {
            val success = auth1.login(ctx, id, password)
            if (success) {
                LECTURER
                    .whereEqualTo("lecturerID", id)
                    .get()
                    .addOnSuccessListener {
                        for (doc in it.documents) {
                            doc.reference.update("status", status)
                            doc.reference.update("loginDate", current)
                            CLASS
                                .whereEqualTo("lecturerID", id)
                                .get()
                                .addOnSuccessListener {
                                    for (doc in it.documents) {
                                        cid = doc.getString("classID").toString()

                                        CLASSDETAILS
                                            .whereEqualTo("classID", cid)
                                            .get()
                                            .addOnSuccessListener {
                                                for (doc in it.documents) {
                                                    stuid = doc.getString("studentID").toString()

                                                    BLOCKED
                                                        .whereEqualTo("studentID", stuid)
                                                        .get()
                                                        .addOnSuccessListener {
                                                            for (doc in it.documents) {
                                                                doc.reference.update("status", "Y")
                                                                //count += 1
                                                            }
                                                        }

                                                    RETURN
                                                        .whereEqualTo("studentID", stuid)
                                                        .get()
                                                        .addOnSuccessListener {
                                                            for (doc in it.documents) {
                                                                doc.reference.update("status", "Y")
                                                                //count += 1
                                                            }
                                                        }

                                                }

                                            }
                                    }

                                }
                        }
                    }
                //nav.popBackStack(R.id.homeFragment, false)
                add()
                val intent = Intent(this@HomeFragment.requireContext(), NotificationActivity::class.java)
                startActivity(intent)

            }
            else if(!success) {
                lifecycleScope.launch {
                    val success = auth.login(ctx, id, password)
                    if (success) {
                        ADMIN
                            .whereEqualTo("adminID", id)
                            .get()
                            .addOnSuccessListener {
                                for (doc in it.documents) {
                                    doc.reference.update("status", status)
                                    doc.reference.update("loginDate", current)
                                }
                            }
                        //nav.popBackStack(R.id.homeFragment, false)
                        val intent = Intent(this@HomeFragment.requireContext(), SecurityActivity::class.java)
                        startActivity(intent)
                    } else {
                        toast("Invalid Login Credentials")
                    }
                }
            }
            else {
                toast("Invalid Login Credentials")
            }
        }
    }




    private fun add() {
        var num1 = ""
        var totalnum = formatter1.format(1).toDouble()

        BLOCKED
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    num1 = doc.getString("date").toString()
                    val s = Notification(
                        date = num1,
                        totalnum = totalnum
                    )

                    // TODO: Set (insert)
                    vm.set(s)
                }

            }

    }
    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}