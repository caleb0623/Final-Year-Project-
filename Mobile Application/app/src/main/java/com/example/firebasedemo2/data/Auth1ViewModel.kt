package com.example.firebasedemo2.data

import android.content.Context
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import retrofit2.HttpException

class Auth1ViewModel : ViewModel() {

    private val lecturerLiveData = MutableLiveData<Lecturer?>()

    fun getLecturerLiveData(): LiveData<Lecturer?> = lecturerLiveData

    fun getLecturer(): Lecturer? = lecturerLiveData.value

    suspend fun login(
        ctx: Context,
        id: String,
        password: String,
        remember: Boolean = false
    ): Boolean {
        return try {
            val user = ApiClient.signIn(ctx, "lecturer", id.trim(), password)
            lecturerLiveData.value = ApiClient.decode(user, Lecturer::class.java)
            true
        } catch (error: HttpException) {
            if (error.code() == 401) false else throw error
        }
    }

    fun logout(ctx: Context) {
        ApiClient.signOut(ctx)
        lecturerLiveData.value = null
    }

    suspend fun loginFromPreferences(ctx: Context) {
        val user = ApiClient.restoreSession(ctx)
        if (user?.get("role") == "lecturer") {
            lecturerLiveData.value = ApiClient.decode(user, Lecturer::class.java)
        }
    }
}
