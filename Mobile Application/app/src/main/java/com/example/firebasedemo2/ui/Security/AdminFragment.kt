package com.example.firebasedemo2.ui.Security


import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.ADMIN
import com.example.firebasedemo2.data.BlockedViewModel
import com.example.firebasedemo2.data.LOGIN
import com.example.firebasedemo2.databinding.FragmentAdminProfileBinding


class AdminFragment : Fragment() {

    private lateinit var binding: FragmentAdminProfileBinding
    private val nav by lazy { findNavController() }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentAdminProfileBinding.inflate(inflater, container, false)
        var adminid =""
        var adminName =""
        var adminEmail =""
        var adminPhoneNum =""


        ADMIN
            .whereEqualTo("status","logined")
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    adminid = doc.getString("adminID").toString()
                    adminName = doc.getString("adminName").toString()
                    adminEmail = doc.getString("adminEmail").toString()
                    adminPhoneNum = doc.getString("adminPhoneNo").toString()
                }// TODO(31): Load a specific delivery
                binding.txtAdminID.text = adminid
                binding.txtAdminName.text = adminName
                binding.txtAdminEmail.text = adminEmail
                binding.txtAdminPhoneNum.text = adminPhoneNum
            }



        // -----------------------------------------------------------------------------------------

        binding.btnBack.setOnClickListener { nav.navigateUp() }

        // -----------------------------------------------------------------------------------------





        return binding.root
    }


}