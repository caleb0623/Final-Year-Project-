package com.example.firebasedemo2.ui.Notification

import android.content.Intent
import android.icu.lang.UProperty.BLOCK
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentBlockedlistBinding
import com.example.firebasedemo2.databinding.FragmentTodayblockedlistBinding
import com.example.firebasedemo2.util.BlockedAdapter
import com.google.firebase.firestore.ListenerRegistration
import kotlinx.android.synthetic.main.fragment_todayblockedlist.*
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter


class TodayBlockedListFragment : Fragment() {

    private lateinit var binding: FragmentTodayblockedlistBinding
    private val nav by lazy { findNavController() }
    private val vm: BlockedViewModel by activityViewModels()
    val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")
    val current = LocalDateTime.now().format(formatter)
    var count = 0.0

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentTodayblockedlistBinding.inflate(inflater, container, false)
        vm.search("","")
        val adapter = BlockedAdapter() { holder, blocked ->
            holder.binding.root.setOnClickListener {
                nav.navigate(R.id.studentdetailFragment, bundleOf("student" to blocked.studentID))
                //change to detail of student
            }
        }


        binding.txtDate.text = current
        binding.btnReturn.setOnClickListener {
            nav.navigate(R.id.todayReturnFragment, bundleOf("date" to current))
        }
        binding.btnIntranet.setOnClickListener {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://web.tarc.edu.my/portal/login.jsp"))
            startActivity(intent)
        }
        vm.search( current,"Y")
        BLOCKED
            .whereEqualTo("status","Y")
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    BLOCKED
                        .whereEqualTo("date", current)
                        .get()
                        .addOnSuccessListener {
                            count += 1
                        }
                }

            }

        binding.rv.adapter = adapter
        binding.rv.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))

        vm.getResult().observe(viewLifecycleOwner) {

            adapter.submitList(it)
        }
        return binding.root
    }

    private fun delete(id: String) {
        // TODO: Delete
        vm.delete(id)
    }
}