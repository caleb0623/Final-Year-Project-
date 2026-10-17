package com.example.firebasedemo2.data

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class ReturnViewModel : ViewModel() {

    private val result = MutableLiveData<List<Return>>(emptyList())
    private val errors = MutableLiveData<String?>()
    private var records = emptyList<Return>()
    private var date = ""
    private var status = ""
    var list = records
        private set

    init {
        refresh()
        viewModelScope.launch {
            while (isActive) {
                delay(15_000)
                refresh()
            }
        }
    }

    suspend fun getAll(date: String): List<Return> =
        ApiClient.listRecords("returns", Return::class.java, mapOf("date" to date))

    fun get(studentID: String): Return? = result.value?.find { it.studentID == studentID }

    fun getResult(): LiveData<List<Return>> = result
    fun getErrors(): LiveData<String?> = errors

    fun search(date: String, status: String) {
        this.date = date
        this.status = status
        updateResult()
    }

    fun refresh() {
        viewModelScope.launch {
            try {
                records = ApiClient.listRecords("returns", Return::class.java)
                updateResult()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not load return records (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not load return records: network unavailable."
            }
        }
    }

    fun delete(returnID: String) {
        viewModelScope.launch {
            try {
                ApiClient.api.deleteRecord("returns", returnID)
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not delete return record (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not delete return record: network unavailable."
            }
        }
    }

    fun set(record: Return) {
        viewModelScope.launch {
            try {
                ApiClient.api.createRecord("returns", ApiClient.toMap(record))
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not save return record (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not save return record: network unavailable."
            }
        }
    }

    private fun updateResult() {
        list = records.filter { it.date.contains(date, true) && it.status.contains(status, true) }
        result.value = list
    }
}
