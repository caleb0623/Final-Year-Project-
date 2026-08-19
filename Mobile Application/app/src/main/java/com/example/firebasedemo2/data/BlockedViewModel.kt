package com.example.firebasedemo2.data

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.firestore.ktx.toObjects
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

class BlockedViewModel : ViewModel() {

    suspend fun getAll(date: String): List<Blocked> {
        val blocked = BLOCKED
            .get()
            .await()
            .toObjects<Blocked>()
        return blocked
    }

    private val block = MutableLiveData<List<Blocked>>()
    private var blocked = listOf<Blocked>() // Original data
    var list = blocked
    private var date = ""       // Filter
    private var status = ""

    init {
        // TODO(14): Read all fruits -> launch block
        //           Populate [category] field
        viewModelScope.launch {
            BLOCKED.addSnapshotListener { value, _ ->
                if (value == null) return@addSnapshotListener

                blocked = value.toObjects<Blocked>()

                updateResult()
            }
        }

    }

    // TODO: Initialization
    private val col = Firebase.firestore.collection("blocked")


    // ---------------------------------------------------------------------------------------------

    fun init() = Unit // void

    fun get(studentID: String) = block.value?.find { it.studentID== studentID }

    fun getResult() = block // Live data

    private fun updateResult() {
        //var list = listOf<Blocked>()

        // TODO(23): Search + filter
        list = blocked.filter {
            it.date.contains(date, true)
            //it.studentID.contains(studentID,true)
        }

        list = list.filter {
            //it.date.contains(date, true)
            it.status.contains(status,true)
        }
        block.value = list
    }

    fun search(date: String,status :String) {
        this.date = date
        this.status = status
        updateResult()
    }



    fun delete(blockedID: String) {
        // TODO
        col.document(blockedID).delete()

    }

    fun set(f: Blocked) {
        // TODO
        col.document(f.blockedID).set(f)
    }

    //----------------------------------------------------------------------------------------------

    private fun idExists(blockedID: String)
            = block.value?.any { it.blockedID == blockedID} ?: false


}