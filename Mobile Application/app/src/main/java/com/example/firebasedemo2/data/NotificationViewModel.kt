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
import java.text.SimpleDateFormat
import java.util.Locale

class NotificationViewModel : ViewModel() {

    private var notifications = emptyList<Notification>()
    private val result = MutableLiveData<List<Notification>>(emptyList())
    private val errors = MutableLiveData<String?>()
    var list = notifications
        private set
    private var startDate = 0L
    private var endDate = Long.MAX_VALUE
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.US)

    init {
        refresh()
        viewModelScope.launch {
            while (isActive) {
                delay(15_000)
                refresh()
            }
        }
    }

    suspend fun getAll(): List<Notification> =
        ApiClient.listRecords("notification", Notification::class.java)

    fun getResult(): LiveData<List<Notification>> = result
    fun getErrors(): LiveData<String?> = errors

    fun init() = refresh()

    fun search(startdate: Long, enddate: Long) {
        this.startDate = startdate
        this.endDate = enddate
        updateResult()
    }

    fun get(startdate: String): Notification? = notifications.find { it.date == startdate }

    fun delete(startdate: String) {
        viewModelScope.launch {
            try {
                ApiClient.api.deleteRecord("notification", startdate)
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not delete report (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not delete report: network unavailable."
            }
        }
    }

    fun set(record: Notification) {
        viewModelScope.launch {
            try {
                ApiClient.api.createRecord("notification", ApiClient.toMap(record))
                refresh()
            } catch (error: HttpException) {
                errors.value = "Could not save report (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not save report: network unavailable."
            }
        }
    }

    private fun refresh() {
        viewModelScope.launch {
            try {
                notifications = ApiClient.listRecords("notification", Notification::class.java)
                updateResult()
                errors.value = null
            } catch (error: HttpException) {
                errors.value = "Could not load reports (${error.code()})."
            } catch (error: IOException) {
                errors.value = "Could not load reports: network unavailable."
            }
        }
    }

    private fun updateResult() {
        list = notifications.filter { notification ->
            val date = dateFormat.parse(notification.date)?.time ?: return@filter false
            date >= startDate && date <= endDate
        }
        result.value = list
    }
}
