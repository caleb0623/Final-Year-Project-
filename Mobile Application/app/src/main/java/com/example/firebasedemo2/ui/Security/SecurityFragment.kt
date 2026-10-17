package com.example.firebasedemo2.ui.Security

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.SearchView
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.DividerItemDecoration
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.SecurityViewModel
import com.example.firebasedemo2.databinding.FragmentSecurityhomeBinding
import com.example.firebasedemo2.util.SecurityAdapter


class SecurityFragment : Fragment() {

    private lateinit var binding: FragmentSecurityhomeBinding
    private val nav2 by lazy { findNavController() }
    private val vm: SecurityViewModel by activityViewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        binding = FragmentSecurityhomeBinding.inflate(inflater, container, false)
        binding.btnAdd.setOnClickListener {
            nav2.navigate(R.id.addsgFragment)
            //go to add
        }
        vm.search("")

        val adapter = SecurityAdapter() { holder, security ->
            holder.binding.btnDelete.setOnClickListener {
                nav2.navigate(R.id.deleteconfirmFragment, bundleOf("id" to security.guardID))
                //delete(security.guardID)
            }
            holder.binding.btnView.setOnClickListener {
                nav2.navigate(R.id.securitydetailFragment, bundleOf("id" to security.guardID))
            }
            holder.binding.btnEdit.setOnClickListener {
                nav2.navigate(R.id.securityeditFragment, bundleOf("id" to security.guardID))
            }
            //view and edit need to add
        }

        binding.rv.adapter = adapter
        binding.rv.addItemDecoration(DividerItemDecoration(context, DividerItemDecoration.VERTICAL))
        //vm.search("keong")
        vm.getResult().observe(viewLifecycleOwner) {
            adapter.submitList(it)
        }

        binding.sv.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(sename: String) = true
            override fun onQueryTextChange(sename: String): Boolean {
                // TODO(19): Search by [name] -> vm.search(...)
                vm.search(sename)

                return true
            }
        })

        return binding.root
    }

    private fun delete(id: String) {
        // TODO: Delete
        vm.delete(id)
    }

    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}

