package com.example.firebasedemo2.ui.Notification

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.databinding.FragmentNotificationhomeBinding


class Notification : Fragment() {

    private lateinit var binding: FragmentNotificationhomeBinding
    private val nav by lazy { findNavController() }


    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentNotificationhomeBinding.inflate(inflater, container, false)

        return binding.root
    }


    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}

