package com.example.firebasedemo2.ui.Security

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentDeleteconfirmBinding
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import org.greenrobot.eventbus.EventBus
import java.text.DecimalFormat
import java.text.SimpleDateFormat
import java.util.*

class DeleteFragment : BottomSheetDialogFragment() {

    private lateinit var binding: FragmentDeleteconfirmBinding
    private val nav by lazy { findNavController() }
    private val vm: SecurityViewModel by activityViewModels()
    lateinit var date: String

    private val id by lazy { arguments?.getString("id") ?: "" }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentDeleteconfirmBinding.inflate(inflater, container, false)

        // -----------------------------------------------------------------------------------------

        binding.btnCancel.setOnClickListener { dismiss() }
        binding.btnYes.setOnClickListener { complete()}


        // -----------------------------------------------------------------------------------------


        // -----------------------------------------------------------------------------------------

        return binding.root
    }

    private fun complete() {
        vm.delete(id)
        toast("Deleted!")
        dismiss()
    }

    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}