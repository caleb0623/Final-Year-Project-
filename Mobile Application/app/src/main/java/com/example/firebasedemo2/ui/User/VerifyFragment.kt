package com.example.firebasedemo2.ui.User

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.NotificationActivity
import com.example.firebasedemo2.R
import com.example.firebasedemo2.UserActivity
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentVerifyBinding


class VerifyFragment : Fragment() {

    private lateinit var binding: FragmentVerifyBinding
    private val nav by lazy { findNavController() }
    private val vm: AuthViewModel by activityViewModels()
    private val vm1: Auth1ViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("id") ?: "" }
    private val password by lazy { arguments?.getString("password") ?: "" }
    private val random by lazy { arguments?.getString("random") ?: "" }
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentVerifyBinding.inflate(inflater, container, false)
        binding.btnAdd.setOnClickListener { verify()}
        binding.btnClose.setOnClickListener {nav.navigateUp() }

        return binding.root
    }

    private fun verify() {
        var first = binding.edt1.text.toString().trim()
        var second = binding.edt2.text.toString().trim()
        var third = binding.edt3.text.toString().trim()
        var forth = binding.edt4.text.toString().trim()
        var code = first + second + third + forth

        if (code == random){
            LECTURER.whereEqualTo("lecturerID", id)
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        doc.reference.update("lecturerPw", password)
                        toast("Your password have been updated, Please proceed to login!")
                        nav.navigate(R.id.homeFragment)
                    }
                }

            ADMIN.whereEqualTo("adminID", id)
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        doc.reference.update("adminPassword", password)
                        toast("Your password have been updated, Please proceed to login!")
                        nav.navigate(R.id.homeFragment)
                        }
                    }

        }
        else {
            toast("Please enter a correct code!")
        }



    }

        private fun toast(text: String) {
            Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
        }
    }
