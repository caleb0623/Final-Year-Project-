package com.example.firebasedemo2.ui.Security

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentAddsgBinding
import java.util.regex.Matcher
import java.util.regex.Pattern


class AddSGFragment : Fragment() {

    private lateinit var binding: FragmentAddsgBinding
    private val nav by lazy { findNavController() }
    private val vm: SecurityViewModel by activityViewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentAddsgBinding .inflate(inflater, container, false)
        binding.btnAddSe.setOnClickListener { add()}
        binding.btnReset.setOnClickListener { reset() }
        binding.btnClose.setOnClickListener {nav.navigateUp() }

        return binding.root
    }

    private fun reset() {
        binding.edtName.text.clear()
        binding.edtPw.text.clear()
        binding.edtPhoneNum.text.clear()

        binding.edtName.requestFocus()
    }

    private fun add() {
        var guardID = ""
        var num = ""
        var number = 0
        var biggest = 0
        var newnum = 0
        var newguardID = "SG00001"

        SECURITY
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    guardID = doc.getString("guardID").toString()
                    num = guardID.filter{it.isDigit()}
                    number = num.toInt()
                    if (number > biggest)
                        biggest = number
                    newnum = biggest+1
                    //guardID = newnum.toString()
                    guardID = String.format("%05d",newnum)
                    newguardID = "SG$guardID"
                }

                val s = Security(
                    guardID = newguardID,
                    guardName = binding.edtName.text.toString().trim(),
                    guardPhoneNo = binding.edtPhoneNum.text.toString().trim(),
                    guardPassword = binding.edtPw.text.toString().trim(),
                    adminID = "AD001", //get from login *** remember
                )
                //Input


                val err = vm.validate(s)
                if (err != "") {
                    toast(err)
                    return@addOnSuccessListener
                }

                // TODO: Set (insert)
                vm.set(s)

                nav.navigateUp()
                }
            }

        private fun toast(text: String) {
            Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
        }
    }
