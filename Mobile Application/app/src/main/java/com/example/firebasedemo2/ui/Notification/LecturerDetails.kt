package com.example.firebasedemo2.ui.Notification

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.databinding.FragmentLecturerDetailsBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class LecturerDetails : Fragment() {

    private lateinit var binding: FragmentLecturerDetailsBinding
    private val nav by lazy { findNavController() }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentLecturerDetailsBinding.inflate(inflater, container, false)
        binding.btnBack.setOnClickListener { nav.navigateUp() }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val user = ApiClient.restoreSession(requireContext())
                if (user?.get("role") != "lecturer") {
                    toast("Lecturer session expired. Sign in again.")
                    return@launch
                }
                binding.txtLecturerID.text = user["lecturerID"] as? String ?: ""
                binding.txtLecturerName.text = user["lecturerName"] as? String ?: ""
                binding.txtLecturerEmail.text = user["lecturerEmail"] as? String ?: ""
            } catch (error: HttpException) {
                toast("Could not load lecturer profile (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
        return binding.root
    }

    private fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}
