package com.example.firebasedemo2.ui.Notification

import android.app.DatePickerDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.DatePicker
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.NotificationViewModel
import com.example.firebasedemo2.databinding.FragmentNotificationBinding
import com.example.firebasedemo2.util.NotificationAdapter
import java.text.SimpleDateFormat
import java.util.*

class NotificationFragment : Fragment() {

    private lateinit var binding: FragmentNotificationBinding
    private val nav by lazy { findNavController() }
    private val vm: NotificationViewModel by activityViewModels()
    var cal = Calendar.getInstance()
    var datePicker: DatePickerDialog? = null
    var start = ""
    var end = ""
    lateinit var new : Date
    var milliseconds : Long = 0
    var milliseconds2 : Long = 0
    var choose = false
    var now = System.currentTimeMillis() - 1000

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentNotificationBinding.inflate(inflater, container, false)
        vm.search(0,now)
        // -----------------------------------------------------------------------------------------

        val dateSetListener = object : DatePickerDialog.OnDateSetListener {
            override fun onDateSet(view: DatePicker, year: Int, monthOfYear: Int,
                                   dayOfMonth: Int) {
                cal.set(Calendar.YEAR, year)
                cal.set(Calendar.MONTH, monthOfYear)
                cal.set(Calendar.DAY_OF_MONTH, dayOfMonth)
                updateDateInView()
            }
        }

        val dateSetListener1 = object : DatePickerDialog.OnDateSetListener {
            override fun onDateSet(view: DatePicker, year: Int, monthOfYear: Int,
                                   dayOfMonth: Int) {
                cal.set(Calendar.YEAR, year)
                cal.set(Calendar.MONTH, monthOfYear)
                cal.set(Calendar.DAY_OF_MONTH, dayOfMonth)
                updateDateInView1()
            }
        }

        // when you click on the button, show DatePickerDialog that is set with OnDateSetListener
        binding.st1.setOnClickListener {
            DatePickerDialog(
                requireContext(),
                dateSetListener,
                // set DatePickerDialog to point to today's date when it loads up
                cal.get(Calendar.YEAR),
                cal.get(Calendar.MONTH),
                cal.get(Calendar.DAY_OF_MONTH)
            ).show()
        }

        binding.st.setOnClickListener {
            DatePickerDialog(
                requireContext(),
                dateSetListener,
                // set DatePickerDialog to point to today's date when it loads up
                cal.get(Calendar.YEAR),
                cal.get(Calendar.MONTH),
                cal.get(Calendar.DAY_OF_MONTH)
            ).show()
        }

        binding.et1.setOnClickListener {
            if (choose) {
                datePicker = DatePickerDialog(
                    requireContext(),
                    dateSetListener1,

                    // set DatePickerDialog to point to today's date when it loads up
                    cal.get(Calendar.YEAR),
                    cal.get(Calendar.MONTH),
                    cal.get(Calendar.DAY_OF_MONTH)
                )
                datePicker!!.getDatePicker().setMinDate(milliseconds)
                datePicker!!.show()
            } else {
                toast("Please choose starting date first!")
            }
        }

        binding.et.setOnClickListener {
            if (choose) {
                datePicker = DatePickerDialog(
                    requireContext(),
                    dateSetListener1,

                    // set DatePickerDialog to point to today's date when it loads up
                    cal.get(Calendar.YEAR),
                    cal.get(Calendar.MONTH),
                    cal.get(Calendar.DAY_OF_MONTH)
                )
                datePicker!!.getDatePicker().setMinDate(milliseconds)
                datePicker!!.show()
            } else {
                toast("Please choose starting date first!")
            }
        }



        val adapter = NotificationAdapter() { holder, notification ->
            holder.binding.btnView.setOnClickListener {
                nav.navigate(R.id.blockedFragment, bundleOf("date" to notification.date))
            }
        }
        binding.rv.adapter = adapter
        binding.rv.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
        binding.BtnSearch.setOnClickListener { search() }

        vm.getResult().observe(viewLifecycleOwner) {
            adapter.submitList(it)
            //binding.txtCount.text = "${it.size} Order(s)"
        }

        return binding.root
    }

    private fun search(){
        vm.search(milliseconds ,milliseconds2)
    }

    private fun updateDateInView() {
        val myFormat = "yyyy-MM-dd" // mention the format you need
        val sdf = SimpleDateFormat(myFormat, Locale.US)
        binding.st.text = sdf.format(cal.time)
        start = sdf.format(cal.time)
        new = sdf.parse(start)
        milliseconds = new.time
        if(start == sdf.format(cal.time)){
            choose = true

        }
    }

    private fun updateDateInView1() {
        val myFormat = "yyyy-MM-dd"  // mention the format you need
        val sdf = SimpleDateFormat(myFormat, Locale.US)
        binding.et.text = sdf.format(cal.time)
        end = sdf.format(cal.time)
        new = sdf.parse(end)
        milliseconds2 = new.time
    }

    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}