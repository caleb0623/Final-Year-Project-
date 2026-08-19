package com.example.firebasedemo2

import android.os.Bundle
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.ActivityUserBinding
import com.google.firebase.firestore.ktx.firestore
import com.google.firebase.ktx.Firebase
import kotlinx.coroutines.launch


class UserActivity : AppCompatActivity() {

    private lateinit var binding: ActivityUserBinding
    private val nav by lazy {
        supportFragmentManager.findFragmentById(R.id.host)!!.findNavController()
    }

    private val auth: AuthViewModel by viewModels()
    private var db = Firebase.firestore

    // AppBarConfiguration
    private lateinit var abc: AppBarConfiguration
    var status = ""
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityUserBinding.inflate(layoutInflater)
        setContentView(binding.root)

        LECTURER
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    doc.reference.update("status", "")
                    doc.reference.update("loginDate", "")
                }
            }
        ADMIN
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    doc.reference.update("status", "")
                    doc.reference.update("loginDate", "")
                }
            }

        BLOCKED
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    doc.reference.update("status", "")

                }
            }
        RETURN
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    doc.reference.update("status", "")

                }
            }

        // -----------------------------------------------------------------------------------------

        // TODO(5): Observe login status -> customerLiveData
        auth.getAdminLiveData().observe(this) {


            // TODO(8): Auto login -> auth.loginFromPreferences(...)
            lifecycleScope.launch { auth.loginFromPreferences(this@UserActivity) }

        }
    }


    /*private fun logout(): Boolean {
        // TODO(4): Logout -> auth.logout(...)
        //          Clear navigation backstack
        auth.logout(this)
        nav.popBackStack(R.id.homeFragment,false)
        nav.navigateUp()
        CUSTOMERS
            .get()
            .addOnSuccessListener {
                for (doc in it.documents) {
                    doc.reference.update("status", "")
                }
            }
        binding.drawerLayout.close()
        return true
    }*/

    override fun onSupportNavigateUp(): Boolean {
        return nav.navigateUp(abc) || super.onSupportNavigateUp()
    }

    private fun toast(s: String) {
        Toast.makeText(this,s, Toast.LENGTH_SHORT).show()

    }
}