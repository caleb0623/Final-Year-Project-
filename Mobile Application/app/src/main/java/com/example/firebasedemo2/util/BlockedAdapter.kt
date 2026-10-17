package com.example.firebasedemo2.util

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.data.Blocked
import com.example.firebasedemo2.databinding.ItemBlockedBinding


class BlockedAdapter (
    val fn: (ViewHolder, Blocked) -> Unit = { _, _ -> }
) : ListAdapter<Blocked, BlockedAdapter.ViewHolder>(DiffCallback) {

    companion object DiffCallback : DiffUtil.ItemCallback<Blocked>() {
        override fun areItemsTheSame(a: Blocked, b: Blocked)    = a.blockedID == b.blockedID
        override fun areContentsTheSame(a: Blocked, b: Blocked) = a == b
    }

    class ViewHolder(val binding: ItemBlockedBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemBlockedBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val blocked = getItem(position)

        holder.binding.txtStuID.text  = blocked.studentID
        holder.binding.txtStuName.text  = blocked.studentName

        // Violation photo saved by the guard's acknowledgement, served from Supabase Storage by the API
        val context = holder.itemView.context
        Glide.with(context)
            .load(ApiClient.blockedPhoto(context, blocked.blockedID))
            .placeholder(R.drawable.blankprofile)
            .error(R.drawable.blankprofile)
            .into(holder.binding.imgStu)

        fn(holder, blocked)
    }

}
