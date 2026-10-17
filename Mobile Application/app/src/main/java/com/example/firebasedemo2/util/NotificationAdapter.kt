package com.example.firebasedemo2.util

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.Notification
import com.example.firebasedemo2.databinding.ItemNoticeBinding
import java.text.DecimalFormat

class NotificationAdapter (
    val fn: (ViewHolder, Notification) -> Unit = { _, _ -> }
) : ListAdapter<Notification, NotificationAdapter.ViewHolder>(DiffCallback) {

    //private val formatter = DecimalFormat("0.00")
    private val formatter1 = DecimalFormat("0")

    companion object DiffCallback : DiffUtil.ItemCallback<Notification>() {
        override fun areItemsTheSame(a: Notification, b: Notification) = a.date == b.date
        override fun areContentsTheSame(a: Notification, b: Notification) = a == b
    }

    class ViewHolder(val binding: ItemNoticeBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemNoticeBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val notification = getItem(position)
        holder.binding.txtDate.text  = notification.date
        holder.binding.txtTotalNum.text = formatter1.format(notification.totalnum)

        fn(holder, notification)
    }

}