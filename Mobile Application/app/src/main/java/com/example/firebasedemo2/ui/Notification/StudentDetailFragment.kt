package com.example.firebasedemo2.ui.Notification


import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.BlockedViewModel
import com.example.firebasedemo2.databinding.FragmentStudentDetailBinding
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import java.text.DecimalFormat

class StudentDetailFragment : Fragment() {

    private lateinit var binding: FragmentStudentDetailBinding
    private val nav by lazy { findNavController() }
    private val vm: BlockedViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("student", "") ?: "" }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentStudentDetailBinding.inflate(inflater, container, false)

        val student = vm.get(id) !!
        // -----------------------------------------------------------------------------------------

        binding.btnBack.setOnClickListener { nav.navigateUp() }

        // -----------------------------------------------------------------------------------------

        // TODO(31): Load a specific delivery
        binding.txtStudentsID.text = student.studentID
        binding.txtStudentsName.text = student.studentName
        binding.txtBlockDates.text = student.date
        binding.txtBlockTimes.text = student.time



        return binding.root
    }


}