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

class SecurityViewModel : ViewModel() {

    private var security = emptyList<Security>()
    private val result = MutableLiveData<List<Security>>(emptyList())
    private val errors = MutableLiveData<String?>()
    private var guardName = ""

    init {
        refresh()
        viewModelScope.launch {
            while (isActive) {
                delay(15_000)
                refresh()
            }
        }
    }

    fun init() = refresh()
    fun getResult(): LiveData<List<Security>> = result
    fun getErrors(): LiveData<String?> = errors
    fun get(guardID: String): Security? = security.find { it.guardID == guardID }

    fun search(guardName: String) {
        this.guardName = guardName
        updateResult()
    }

    fun delete(guardID: String) {
        viewModelScope.launch {
            try {
                ApiClient.api.deleteRecord("security", guardID)
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not delete security guard (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not delete security guard: network unavailable."
            }
        }
    }

    fun set(record: Security) {
        viewModelScope.launch {
            try {
                if (get(record.guardID) == null) {
                    ApiClient.api.createRecord("security", ApiClient.toMap(record))
                } else {
                    ApiClient.api.replaceRecord(
                        "security",
                        record.guardID,
                        ApiClient.toMap(record)
                    )
                }
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not save security guard (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not save security guard: network unavailable."
            }
        }
    }

    fun update(record: Security) {
        viewModelScope.launch {
            try {
                ApiClient.api.updateRecord(
                    "security",
                    record.guardID,
                    ApiClient.toMap(record)
                )
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not update security guard (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not update security guard: network unavailable."
            }
        }
    }

    fun validate(record: Security, insert: Boolean = true): String {
        val errors = StringBuilder()
        if (record.guardName.isBlank()) errors.append("- Name is required.\n")
        if (record.guardPhoneNo.isBlank()) errors.append("- Phone Number is required.\n")
        else if (!record.guardPhoneNo.matches(Regex("^01\\d{8,9}$"))) {
            errors.append("- Phone Number format is wrong.\n")
        }
        if (insert && record.guardPassword.isBlank()) errors.append("- Password is required.\n")
        if (record.adminID.isBlank()) errors.append("- AdminID is required.\n")
        return errors.toString()
    }

    private fun refresh() {
        viewModelScope.launch {
            try {
                security = ApiClient.listRecords("security", Security::class.java)
                updateResult()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not load security guards (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not load security guards: network unavailable."
            }
        }
    }

    private fun updateResult() {
        result.value = security.filter { it.guardName.contains(guardName, true) }
    }
}
