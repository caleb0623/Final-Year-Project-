package com.example.firebasedemo2

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.databinding.ActivityUserBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class UserActivity : AppCompatActivity() {

    private lateinit var binding: ActivityUserBinding
    private val nav by lazy {
        supportFragmentManager.findFragmentById(R.id.host)!!.findNavController()
    }
    private lateinit var appBarConfiguration: AppBarConfiguration

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUserBinding.inflate(layoutInflater)
        setContentView(binding.root)
        appBarConfiguration = AppBarConfiguration(emptySet())

        lifecycleScope.launch {
            try {
                val user = ApiClient.restoreSession(this@UserActivity) ?: return@launch
                when (user["role"] as? String) {
                    "admin" -> startActivity(Intent(this@UserActivity, SecurityActivity::class.java))
                    "lecturer" -> startActivity(Intent(this@UserActivity, NotificationActivity::class.java))
                    else -> ApiClient.signOut(this@UserActivity)
                }
            } catch (error: HttpException) {
                toast("Could not restore sign-in (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        return nav.navigateUp(appBarConfiguration) || super.onSupportNavigateUp()
    }

    private fun toast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
}
