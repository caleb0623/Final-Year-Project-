package com.example.firebasedemo2.ui.Notification

import android.app.DatePickerDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.DatePicker
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.BlockedViewModel
import com.example.firebasedemo2.data.ReturnViewModel
import com.example.firebasedemo2.databinding.FragmentBlockedlistBinding
import com.example.firebasedemo2.databinding.FragmentTodayreturnlistBinding
import com.example.firebasedemo2.util.BlockedAdapter
import com.example.firebasedemo2.util.ReturnAdapter
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*


class TodayReturnListFragment : Fragment() {

    private lateinit var binding: FragmentTodayreturnlistBinding
    private val nav by lazy { findNavController() }
    private val vm: ReturnViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("date", "") ?: "" }
    var cal = Calendar.getInstance()
    var datePicker: DatePickerDialog? = null
    var start = ""
    var end = ""
    lateinit var new : Date
    var milliseconds : Long = 0
    var choose = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentTodayreturnlistBinding.inflate(inflater, container, false)
        vm.search("","")
        val adapter = ReturnAdapter()
        binding.sv.queryHint = id
        binding.rv.adapter = adapter
        binding.rv.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
        vm.search(id,"Y")
        vm.getResult().observe(viewLifecycleOwner) {

            adapter.submitList(it)
        }

        val dateSetListener = object : DatePickerDialog.OnDateSetListener {
            override fun onDateSet(view: DatePicker, year: Int, monthOfYear: Int,
                                   dayOfMonth: Int) {
                cal.set(Calendar.YEAR, year)
                cal.set(Calendar.MONTH, monthOfYear)
                cal.set(Calendar.DAY_OF_MONTH, dayOfMonth)
                updateDateInView()
            }
        }
        // when you click on the button, show DatePickerDialog that is set with OnDateSetListener
        binding.sv1.setOnClickListener {
            DatePickerDialog(
                requireContext(),
                dateSetListener,
                // set DatePickerDialog to point to today's date when it loads up
                cal.get(Calendar.YEAR),
                cal.get(Calendar.MONTH),
                cal.get(Calendar.DAY_OF_MONTH)
            ).show()
        }
        return binding.root
    }

    private fun delete(id: String) {
        // TODO: Delete
        vm.delete(id)
    }
    private fun updateDateInView() {
        val myFormat = "yyyy-MM-dd" // mention the format you need
        val sdf = SimpleDateFormat(myFormat, Locale.US)
        binding.sv.queryHint = sdf.format(cal.time)
        start = sdf.format(cal.time)
        vm.search(sdf.format(cal.time),"Y")
    }
}