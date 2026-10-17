package com.example.firebasedemo2.ui.Notification

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.BlockedViewModel
import com.example.firebasedemo2.databinding.FragmentBlockedlistBinding
import com.example.firebasedemo2.util.BlockedAdapter
import kotlinx.coroutines.launch


class BlockedListFragment : Fragment() {

    private lateinit var binding: FragmentBlockedlistBinding
    private val nav by lazy { findNavController() }
    private val vm: BlockedViewModel by activityViewModels()
    private val id by lazy { arguments?.getString("date", "") ?: "" }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentBlockedlistBinding .inflate(inflater, container, false)
        vm.search("","")
        val adapter = BlockedAdapter() { holder, blocked ->
            holder.binding.root.setOnClickListener {
                nav.navigate(R.id.studentdetailFragment, bundleOf("student" to blocked.studentID))
                //change to detail of student
            }
        }
        binding.rv.adapter = adapter
        binding.rv.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
        vm.search(id,"Y")
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