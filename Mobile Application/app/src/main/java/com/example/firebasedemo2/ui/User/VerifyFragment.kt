package com.example.firebasedemo2.ui.User

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.data.ApiPasswordResetConfirmation
import com.example.firebasedemo2.databinding.FragmentVerifyBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class VerifyFragment : Fragment() {

    private lateinit var binding: FragmentVerifyBinding
    private val nav by lazy { findNavController() }
    private val id by lazy { arguments?.getString("id").orEmpty() }
    private val password by lazy { arguments?.getString("password").orEmpty() }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentVerifyBinding.inflate(inflater, container, false)
        binding.btnAdd.setOnClickListener { verify() }
        binding.btnClose.setOnClickListener { nav.navigateUp() }
        return binding.root
    }

    private fun verify() {
        val code = listOf(
            binding.edt1.text.toString().trim(),
            binding.edt2.text.toString().trim(),
            binding.edt3.text.toString().trim(),
            binding.edt4.text.toString().trim(),
            binding.edt5.text.toString().trim(),
            binding.edt6.text.toString().trim(),
        ).joinToString("")
        if (!code.matches(Regex("\\d{6}"))) {
            toast("Enter the 6-digit verification code.")
            return
        }
        if (id.isBlank() || password.isBlank()) {
            toast("Password reset details are missing. Start the process again.")
            nav.navigateUp()
            return
        }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val response = ApiClient.api.confirmPasswordReset(
                    ApiPasswordResetConfirmation(id, code, password)
                )
                toast(response.message)
                nav.navigate(R.id.homeFragment)
            } catch (error: HttpException) {
                toast("The verification code is invalid or expired.")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }

    private fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}
