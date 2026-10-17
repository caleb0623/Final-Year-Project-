package com.example.firebasedemo2.data

import android.content.Context
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import retrofit2.HttpException

class AuthViewModel : ViewModel() {

    private val adminLiveData = MutableLiveData<Admin?>()

    fun getAdminLiveData(): LiveData<Admin?> = adminLiveData

    fun getAdmin(): Admin? = adminLiveData.value

    suspend fun login(
        ctx: Context,
        id: String,
        password: String,
        remember: Boolean = false
    ): Boolean {
        return try {
            val user = ApiClient.signIn(ctx, "admin", id.trim(), password)
            adminLiveData.value = ApiClient.decode(user, Admin::class.java)
            true
        } catch (error: HttpException) {
            if (error.code() == 401) false else throw error
        }
    }

    fun logout(ctx: Context) {
        ApiClient.signOut(ctx)
        adminLiveData.value = null
    }

    suspend fun loginFromPreferences(ctx: Context) {
        val user = ApiClient.restoreSession(ctx)
        if (user?.get("role") == "admin") {
            adminLiveData.value = ApiClient.decode(user, Admin::class.java)
        }
    }
}
