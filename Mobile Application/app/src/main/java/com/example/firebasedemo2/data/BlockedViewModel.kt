package com.example.firebasedemo2.data

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import retrofit2.HttpException
import java.io.IOException
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class BlockedViewModel : ViewModel() {

    private val result = MutableLiveData<List<Blocked>>(emptyList())
    private val errors = MutableLiveData<String?>()
    private var blocked = emptyList<Blocked>()
    private var date = ""
    private var status = ""

    init {
        refresh()
        viewModelScope.launch {
            while (isActive) {
                delay(15_000)
                refresh()
            }
        }
    }

    suspend fun getAll(date: String): List<Blocked> =
        ApiClient.listRecords("blocked", Blocked::class.java, mapOf("date" to date))

    fun get(studentID: String): Blocked? = result.value?.find { it.studentID == studentID }

    fun getResult(): LiveData<List<Blocked>> = result
    fun getErrors(): LiveData<String?> = errors

    fun init() = refresh()

    fun search(date: String, status: String) {
        this.date = date
        this.status = status
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            try {
                blocked = ApiClient.listRecords("blocked", Blocked::class.java)
                updateResult()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not load blocked records (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not load blocked records: network unavailable."
            }
        }
    }

    fun delete(blockedID: String) {
        viewModelScope.launch {
            try {
                ApiClient.api.deleteRecord("blocked", blockedID)
                refresh()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not delete blocked record (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not delete blocked record: network unavailable."
            }
        }
    }

    fun set(record: Blocked) {
        viewModelScope.launch {
            try {
                ApiClient.api.createRecord("blocked", ApiClient.toMap(record))
                refresh()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not save blocked record (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not save blocked record: network unavailable."
            }
        }
    }

    private fun updateResult() {
        result.value = blocked.filter {
            it.date.contains(date, true) && it.status.contains(status, true)
        }
    }
}
