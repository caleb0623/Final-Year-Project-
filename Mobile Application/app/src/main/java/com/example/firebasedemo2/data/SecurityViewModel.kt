package com.example.firebasedemo2.data

import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.firestore.ktx.toObjects
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.launch

class SecurityViewModel : ViewModel() {

    private var security = listOf<Security>() // Original data
    private val result = MutableLiveData<List<Security>>()

    private var guardName = ""       // Search

    init {
        // TODO(14): Read all fruits -> launch block
        //           Populate [category] field
        viewModelScope.launch {
            SECURITY.addSnapshotListener { value, _ ->
                if (value == null) return@addSnapshotListener

                security = value.toObjects<Security>()

                updateResult()
            }
        }

    }

    private fun updateResult() {
        var list = security

        // TODO(23): Search + filter
        list = list.filter {
            it.guardName.contains(guardName, true)
        }

        result.value = list
    }
    // TODO: Initialization
    private val col = Firebase.firestore.collection("security")

    // ---------------------------------------------------------------------------------------------

    fun init() = Unit // void

    fun getResult() = result // Live data

    fun search(guardName: String) {
        this.guardName = guardName
        updateResult()
    }

    fun get(guardID: String) : Security? {  return security.find { it.guardID == guardID }}

    fun delete(guardID: String) {
        // TODO
        col.document(guardID).delete()

    }

    fun set(f: Security) {
        // TODO
        col.document(f.guardID).set(f)
    }

    fun validate(f: Security, insert: Boolean = true): String {
        var e = ""

        if (insert) {
            e += if (f.guardName == "" ) "- Name is empty.\n"
            else ""
        }

        e += if (f.guardName == "") "- Name is required.\n"
        else ""
        e += if (f.guardPhoneNo == "") "- Phone Number is required.\n"
        else ""
        e += if(!f.guardPhoneNo.matches(Regex("^01\\d{8,9}$"))) "- Phone Number format is wrong.\n"
        else ""
        e += if (f.guardPassword == "") "- Password is required.\n"
        else ""
        e += if (f.adminID == "" ) "- AdminID is required.\n"
        else ""

        return e
    }


    //----------------------------------------------------------------------------------------------



}