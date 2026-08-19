package com.example.firebasedemo2.ui.Notification

import android.os.Bundle
import androidx.fragment.app.Fragment
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.LECTURER
import com.example.firebasedemo2.databinding.FragmentLecturerDetailsBinding


class LecturerDetails : Fragment() {private lateinit var binding: FragmentLecturerDetailsBinding
    private val nav by lazy { findNavController() }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentLecturerDetailsBinding.inflate(inflater, container, false)
        var lecturerid =""
        var lecturerName =""
        var lecturerEmail =""
        var lecturerPhoneNum =""


        LECTURER
            .whereEqualTo("status","logined")
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    lecturerid = doc.getString("lecturerID").toString()
                    lecturerName = doc.getString("lecturerName").toString()
                    lecturerEmail = doc.getString("lecturerEmail").toString()
                    lecturerPhoneNum = doc.getString("lecturerPhoneNo").toString()
                }// TODO(31): Load a specific delivery
                binding.txtLecturerID.text = lecturerid
                binding.txtLecturerName.text = lecturerName
                binding.txtLecturerEmail.text = lecturerEmail
            }



        // -----------------------------------------------------------------------------------------

        binding.btnBack.setOnClickListener { nav.navigateUp() }

        // -----------------------------------------------------------------------------------------





        return binding.root
    }


}