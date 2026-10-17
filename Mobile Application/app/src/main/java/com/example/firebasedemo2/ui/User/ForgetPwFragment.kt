package com.example.firebasedemo2.ui.User

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.R
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.data.ApiPasswordResetRequest
import com.example.firebasedemo2.databinding.FragmentForgetpwBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class ForgetPwFragment : Fragment() {

    private lateinit var binding: FragmentForgetpwBinding
    private val nav by lazy { findNavController() }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentForgetpwBinding.inflate(inflater, container, false)
        binding.btnAddCardPayment.setOnClickListener { requestReset() }
        binding.btnReset.setOnClickListener { reset() }
        binding.btnClose.setOnClickListener { nav.navigateUp() }
        return binding.root
    }

    private fun reset() {
        binding.edtUserID.text.clear()
        binding.edtPw.text.clear()
        binding.edtPw2.text.clear()
        binding.edtUserID.requestFocus()
    }

    private fun requestReset() {
        val userId = binding.edtUserID.text.toString().trim()
        val password = binding.edtPw2.text.toString()
        val confirmation = binding.edtPw.text.toString()
        if (userId.isBlank() || password.isBlank() || confirmation.isBlank()) {
            toast("Please fill in all fields.")
            return
        }
        if (password != confirmation) {
            toast("The passwords do not match.")
            return
        }
        if (password.length < 8) {
            toast("The new password must contain at least 8 characters.")
            return
        }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                ApiClient.api.requestPasswordReset(ApiPasswordResetRequest(userId))
                toast("If the account is eligible, a verification code has been sent.")
                nav.navigate(R.id.verifyFragment, bundleOf("id" to userId, "password" to password))
            } catch (error: HttpException) {
                toast("Could not request a password reset (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }

    private fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}
