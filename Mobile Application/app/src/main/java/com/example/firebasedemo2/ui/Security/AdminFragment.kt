package com.example.firebasedemo2.ui.Security


import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.databinding.FragmentAdminProfileBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException


class AdminFragment : Fragment() {

    private lateinit var binding: FragmentAdminProfileBinding
    private val nav by lazy { findNavController() }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?,savedInstanceState: Bundle?): View {
        binding = FragmentAdminProfileBinding.inflate(inflater, container, false)
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val user = ApiClient.restoreSession(requireContext())
                if (user?.get("role") != "admin") {
                    toast("Administrator session expired. Sign in again.")
                    return@launch
                }
                binding.txtAdminID.text = user["adminID"] as? String ?: ""
                binding.txtAdminName.text = user["adminName"] as? String ?: ""
                binding.txtAdminEmail.text = user["adminEmail"] as? String ?: ""
                binding.txtAdminPhoneNum.text = user["adminPhoneNo"] as? String ?: ""
            } catch (error: HttpException) {
                toast("Could not load administrator profile (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }

        // -----------------------------------------------------------------------------------------

        binding.btnBack.setOnClickListener { nav.navigateUp() }

        // -----------------------------------------------------------------------------------------





        return binding.root
    }

    private fun toast(message: String) {
        android.widget.Toast.makeText(context, message, android.widget.Toast.LENGTH_SHORT).show()
    }
}