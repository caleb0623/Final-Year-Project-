package com.example.firebasedemo2.util

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.firebasedemo2.data.Security
import com.example.firebasedemo2.databinding.ActivityNotificationBinding.inflate
import com.example.firebasedemo2.databinding.ItemSecurityBinding
import com.example.firebasedemo2.ui.Security.SecurityDetailFragment
import java.text.DecimalFormat

class SecurityAdapter (
    val fn: (ViewHolder, Security) -> Unit = { _, _ -> }
) : ListAdapter<Security, SecurityAdapter.ViewHolder>(DiffCallback) {

    private val formatter = DecimalFormat("0.00")

    companion object DiffCallback : DiffUtil.ItemCallback<Security>() {
        override fun areItemsTheSame(a: Security, b: Security)    = a.guardID == b.guardID
        override fun areContentsTheSame(a: Security, b: Security) = a == b
    }

    class ViewHolder(val binding: ItemSecurityBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemSecurityBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val security = getItem(position)

        holder.binding.txtSrID.text  = security.guardID
        holder.binding.txtSrName.text = security.guardName

        fn(holder, security)
    }

}