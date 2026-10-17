package com.example.firebasedemo2.ui

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.*
import com.example.firebasedemo2.data.*
import com.example.firebasedemo2.databinding.FragmentHomeBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException

class HomeFragment : Fragment() {

    private lateinit var binding: FragmentHomeBinding
    private val nav by lazy { findNavController() }
    private val auth: AuthViewModel by activityViewModels()
    private val auth1: Auth1ViewModel by activityViewModels()
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentHomeBinding.inflate(inflater, container, false)
        binding.btnLogin.setOnClickListener { login1() }
        binding.btnForgetPassword.setOnClickListener {
            nav.navigate(R.id.forgetpwFragment) }

        return binding.root
    }

    private fun login1() {
        val ctx      = requireContext()
        val id = binding.edtID.text.toString().trim()
        val password = binding.edtPassword.text.toString()
        if (id.isBlank() || password.isBlank()) {
            toast("Enter your ID and password.")
            return
        }
        lifecycleScope.launch {
            try {
                if (auth1.login(ctx, id, password)) {
                    startActivity(Intent(ctx, NotificationActivity::class.java))
                    return@launch
                }
                if (auth.login(ctx, id, password)) {
                    startActivity(Intent(ctx, SecurityActivity::class.java))
                    return@launch
                }
                toast("Invalid Login Credentials")
            } catch (error: HttpException) {
                toast("Sign-in failed (${error.code()}).")
            } catch (error: java.io.IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }
    private fun toast(text: String) {
        Toast.makeText(context, text, Toast.LENGTH_SHORT).show()
    }
}