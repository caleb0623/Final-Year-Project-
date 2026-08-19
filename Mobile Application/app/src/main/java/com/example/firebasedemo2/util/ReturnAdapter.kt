package com.example.firebasedemo2.util

import android.app.ProgressDialog
import android.graphics.BitmapFactory
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.Toast
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.firebasedemo2.UserActivity
import com.example.firebasedemo2.data.Blocked
import com.example.firebasedemo2.data.Return
import com.example.firebasedemo2.databinding.ItemReturnBinding
import com.google.firebase.storage.FirebaseStorage
import java.io.File


class ReturnAdapter (
    val fn: (ViewHolder, Return) -> Unit = { _, _ -> }
) : ListAdapter<Return, ReturnAdapter.ViewHolder>(DiffCallback) {

    //private val formatter = DecimalFormat("0.00")

    companion object DiffCallback : DiffUtil.ItemCallback<Return>() {
        override fun areItemsTheSame(a: Return, b: Return)    = a.returnID == b.returnID
        override fun areContentsTheSame(a: Return, b: Return) = a == b
    }

    class ViewHolder(val binding: ItemReturnBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemReturnBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val blocked = getItem(position)

        holder.binding.txtStuID.text  = blocked.studentID
        holder.binding.txtStuName.text  = blocked.studentName
        holder.binding.txtTime.text  = blocked.time
        holder.binding.txtReturn.text  = "Return Time:"




        fn(holder, blocked)
    }

}