package com.example.firebasedemo2.data

import android.content.ContentValues.TAG
import android.util.Log
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.firestore.ktx.toObjects
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import java.text.ParseException
import java.text.SimpleDateFormat
import java.util.*

class NotificationViewModel : ViewModel() {

    suspend fun getAll(): List<Notification> {
        val notification = NOTIFICATION
            .get()
            .await()
            .toObjects<Notification>()
        return notification
    }

    private var notification = listOf<Notification>() // Original data
    private val result = MutableLiveData<List<Notification>>()
    var list = notification
    private var startdate :Long = 0       // Search
    private var enddate :Long = 0       // Search



    init {
        // TODO(14): Read all fruits -> launch block
        //           Populate [category] field
        viewModelScope.launch {
            NOTIFICATION.addSnapshotListener { value, _ ->
                if (value == null) return@addSnapshotListener

                notification = value.toObjects<Notification>()

                updateResult()
            }
        }

    }

    private fun updateResult() {
        val myFormat = "yyyy-MM-dd" // mention the format you need
        val sdf = SimpleDateFormat(myFormat, Locale.US)

        // TODO(23): Search + filter
        list = notification.filter { item ->
            try {
                val new = sdf.parse(item.date)
                val milliseconds = new.time
                val int1 = startdate.toDouble()
                val int2 = milliseconds.toDouble()
                int2 >= int1
            } catch (e: ParseException) {
                // Handle the case where the date string is invalid
                // For example, log an error message and skip this notification
                Log.e(TAG, "Failed to parse date: ${item.date}", e)
                false
            }
        }

        list = list.filter { item ->
            try {
                val new = sdf.parse(item.date)
                val milliseconds = new.time
                val int1 = enddate.toDouble()
                val int2 = milliseconds.toDouble()
                int2 <= int1
            } catch (e: ParseException) {
                // Handle the case where the date string is invalid
                // For example, log an error message and skip this notification
                Log.e(TAG, "Failed to parse date: ${item.date}", e)
                false
            }
        }

        result.value = list
    }
    // TODO: Initialization
    private val col = Firebase.firestore.collection("notification")

    // ---------------------------------------------------------------------------------------------

    fun init() = Unit // void

    fun getResult() = result // Live data

    fun search(startdate: Long,enddate:Long) {
        this.startdate = startdate
        this.enddate = enddate
        updateResult()
    }

    fun get(startdate: String) : Notification? {  return notification.find { it.date == startdate }}

    fun delete(startdate: String) {
        // TODO
        col.document(startdate).delete()

    }

    fun set(f: Notification) {
        // TODO
        col.document(f.date).set(f)
    }


}