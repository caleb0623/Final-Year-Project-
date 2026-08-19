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

class ReturnViewModel : ViewModel() {

    suspend fun getAll(date: String): List<Return> {
        val returns = RETURN
            .get()
            .await()
            .toObjects<Return>()
        return returns
    }

    private val block = MutableLiveData<List<Return>>()
    private var blocked = listOf<Return>() // Original data
    var list = blocked
    private var date = ""       // Filter
    private var status = ""

    init {
        // TODO(14): Read all fruits -> launch block
        //           Populate [category] field
        viewModelScope.launch {
            RETURN.addSnapshotListener { value, _ ->
                if (value == null) return@addSnapshotListener

                blocked = value.toObjects<Return>()

                updateResult()
            }
        }

    }

    // TODO: Initialization
    private val col = Firebase.firestore.collection("returns")


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



    fun delete(returnID: String) {
        // TODO
        col.document(returnID).delete()

    }

    fun set(f: Return) {
        // TODO
        col.document(f.returnID).set(f)
    }

    //----------------------------------------------------------------------------------------------

    private fun idExists(returnID: String)
            = block.value?.any { it.returnID == returnID} ?: false


}