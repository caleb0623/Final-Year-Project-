package com.example.firebasedemo2.data

import android.content.Context
import android.content.SharedPreferences
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

import com.google.firebase.firestore.ListenerRegistration
import com.google.firebase.firestore.ktx.toObject
import com.google.firebase.firestore.ktx.toObjects
import kotlinx.coroutines.tasks.await

class Auth1ViewModel : ViewModel() {

    private val lecturerLiveData = MutableLiveData<Lecturer?>()
    private var listener: ListenerRegistration? = null

    // Remove snapshot listener when view model is destroyed
    override fun onCleared() {
        super.onCleared()
        listener?.remove()
    }

    // Return observable live data
    fun getLecturerLiveData(): LiveData<Lecturer?> {
        return lecturerLiveData
    }

    // Return customer from live data
    fun getLecturer(): Lecturer? {
        return lecturerLiveData.value
    }

    // TODO(1): Login
    suspend fun login(ctx: Context, id: String, password: String, remember: Boolean = false): Boolean {
        // TODO(1A): Get the customer record with matching email + password
        //           Return false is no matching found
        val lecturer = LECTURER
            .whereEqualTo("lecturerID", id)
            .whereEqualTo("lecturerPw", password)
            .get()
            .await()
            .toObjects<Lecturer>()
            .firstOrNull() ?: return false

        // TODO(1B): Setup snapshot listener
        //           Update live data -> customer
        listener?.remove()
        listener = LECTURER.document(lecturer.lecturerID).addSnapshotListener{doc, _->
            lecturerLiveData.value = doc?.toObject()
        }

        // TODO(6A): Handle remember-me -> add shared preferences
        if (remember){
            getPreferences(ctx)
                .edit()
                .putString("id", id)
                .putString("password", password)
                .apply()
        }

        return true
    }

    // TODO(2): Logout
    fun logout(ctx: Context) {
        // TODO(2A): Remove snapshot listener
        //           Update live data -> null
        listener?.remove()
        lecturerLiveData.value = null

        // TODO(6B): Handle remember-me -> clear shared preferences
        getPreferences(ctx).edit().clear().apply()
    }

    // TODO(6): Get shared preferences
    private fun getPreferences(ctx: Context): SharedPreferences {
        return ctx.getSharedPreferences("AUTH", Context.MODE_PRIVATE)

    }

    // TODO(7): Auto login from shared preferences
    suspend fun loginFromPreferences(ctx: Context) {
        val pref = getPreferences(ctx)
        val id = pref.getString("id", null)
        val password = pref.getString("password", null)

        if (id != null && password != null){
            login(ctx, id, password)
        }
    }

}