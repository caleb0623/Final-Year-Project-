package com.example.firebasedemo2.ui.Security

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SearchView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentSecuritydetailBinding
import com.example.firebasedemo2.databinding.FragmentSecurityeditBinding
import com.example.firebasedemo2.databinding.FragmentSecurityhomeBinding
import com.example.firebasedemo2.util.SecurityAdapter
import com.google.android.material.bottomsheet.BottomSheetDialogFragment


class SecurityEditFragment : Fragment(){

    private lateinit var binding: FragmentSecurityeditBinding
    private val nav by lazy { findNavController() }
    private val vm: SecurityViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("id", "") ?: "" }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        binding = FragmentSecurityeditBinding.inflate(inflater, container, false)

        binding.btnUpdate.setOnClickListener { update() }
        binding.btnCancel.setOnClickListener { nav.navigateUp() }

        val security = vm.get(id) !!

        binding.txtSrID.text = security.guardID
        binding.txtSrCreated.text = security.adminID

        return binding.root
    }

    private fun update() {
        var name    = binding.txtSrName.text.toString().trim()
        var password = binding.txtSrPassword.text.toString().trim()
        var phonenum = binding.txtSrPhoneNum.text.toString().trim()
        val security = vm.get(id) !!
        var seid =""


        if (name == ""){
            SECURITY
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        seid = doc.getString("guardID").toString()
                        if (seid == security.guardID){
                            name = doc.getString("guardName").toString()
                        }
                    }

                }
        }
        if (password == ""){
            SECURITY
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        seid = doc.getString("guardID").toString()
                        if (seid == security.guardID){
                            password = doc.getString("guardPassword").toString()
                        }
                    }

                }
        }


        if (phonenum != "" && phonenum.matches(Regex("^01\\d{8,9}$"))) {
            SECURITY
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        seid = doc.getString("guardID").toString()
                        if (seid == security.guardID){
                            doc.reference.update("guardName", name)
                            doc.reference.update("guardPassword", password)
                            doc.reference.update("guardPhoneNo", phonenum)
                        }
                    }

                }
            nav.navigateUp()
        }
        else if ( phonenum== "" ){
            SECURITY
                .get()
                .addOnSuccessListener {
                    for (doc in it.documents) {
                        seid = doc.getString("guardID").toString()
                        if (seid == security.guardID){
                            phonenum = doc.getString("guardPhoneNo").toString()
                            doc.reference.update("guardName", name)
                            doc.reference.update("guardPassword", password)
                            doc.reference.update("guardPhoneNo", phonenum)
                        }
                    }

                }
            nav.navigateUp()
        }
        else
        { toast("Phone Number format is wrong!")}




    }
    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}

