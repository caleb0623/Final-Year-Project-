package com.example.firebasedemo2.util

import android.app.ProgressDialog
import android.graphics.BitmapFactory
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.Toast
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.firebasedemo2.R
import com.example.firebasedemo2.UserActivity
import com.example.firebasedemo2.data.Blocked
import com.example.firebasedemo2.databinding.ItemBlockedBinding
import com.google.firebase.storage.FirebaseStorage
import java.io.File


class BlockedAdapter (
    val fn: (ViewHolder, Blocked) -> Unit = { _, _ -> }
) : ListAdapter<Blocked, BlockedAdapter.ViewHolder>(DiffCallback) {

    //private val formatter = DecimalFormat("0.00")

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
        val date = blocked.date
        val stid = blocked.studentID

        val longid = "$date-$stid"
        val storageRef = FirebaseStorage.getInstance().reference.child("$longid")

        val localfile = File.createTempFile("tempImage","jpg")
        storageRef.getFile(localfile).addOnSuccessListener {

            val bitmap = BitmapFactory.decodeFile(localfile.absolutePath)
            holder.binding.imgStu.setImageBitmap(bitmap)

        }.addOnFailureListener {
            // Handle the case where the image is not found on the cloud storage
            holder.binding.imgStu.setImageResource(R.drawable.blankprofile)
        }

        fn(holder, blocked)
    }

}