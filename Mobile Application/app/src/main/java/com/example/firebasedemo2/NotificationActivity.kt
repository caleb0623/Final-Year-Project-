package com.example.firebasedemo2

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.fragment.findNavController
import androidx.navigation.ui.AppBarConfiguration
import androidx.navigation.ui.navigateUp
import androidx.navigation.ui.setupActionBarWithNavController
import androidx.navigation.ui.setupWithNavController
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.databinding.ActivityNotificationBinding



class NotificationActivity : AppCompatActivity() {

    private lateinit var binding: ActivityNotificationBinding
    private lateinit var abc: AppBarConfiguration
    private val nav by lazy {
        supportFragmentManager.findFragmentById(R.id.navHost)!!.findNavController()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNotificationBinding.inflate(layoutInflater)
        setContentView(binding.root)

        abc = AppBarConfiguration(
            setOf(
                // Top-level pages
                R.id.notificationFragment,
                R.id.todayBlockedFragment,
                R.id.lecturerdetailFragment,
                R.id.homeFragment
            ),
            binding.drawerLayout2
        )
        setupActionBarWithNavController(nav, abc)
        binding.navView.setupWithNavController(nav)

        binding.navView.menu.findItem(R.id.homeFragment)?.setOnMenuItemClickListener { logout() }

    }

    private fun logout(): Boolean {
        ApiClient.signOut(this)
        binding.navView.menu.clear()
        val h = binding.navView.getHeaderView(0)
        binding.navView.removeHeaderView(h)
        //nav.popBackStack(R.id.homeFragment,false)
        val intent = Intent(this@NotificationActivity, UserActivity::class.java)
        startActivity(intent)
        binding.drawerLayout2.close()
        return true
    }

    override fun onSupportNavigateUp(): Boolean {
        return nav.navigateUp(abc) || super.onSupportNavigateUp()
    }

}

