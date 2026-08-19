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
import com.example.firebasedemo2.data.SecurityViewModel
import com.example.firebasedemo2.databinding.FragmentSecuritydetailBinding
import com.example.firebasedemo2.databinding.FragmentSecurityhomeBinding
import com.example.firebasedemo2.util.SecurityAdapter
import com.google.android.material.bottomsheet.BottomSheetDialogFragment


class SecurityDetailFragment : Fragment(){

    private lateinit var binding: FragmentSecuritydetailBinding
    private val nav by lazy { findNavController() }
    private val vm: SecurityViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("id", "") ?: "" }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        binding = FragmentSecuritydetailBinding.inflate(inflater, container, false)

        binding.btnBack.setOnClickListener { nav.navigateUp() }

        val security = vm.get(id) !!

        binding.txtSrID.text = security.guardID
        binding.txtSrPhoneNum.text = security.guardPhoneNo
        binding.txtSrName.text = security.guardName
        binding.txtSrPassword.text = security.guardPassword
        binding.txtSrCreated.text = security.adminID

        return binding.root
    }
}

