package com.example.firebasedemo2.ui.Security

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.data.Security
import com.example.firebasedemo2.data.SecurityViewModel
import com.example.firebasedemo2.databinding.FragmentSecurityeditBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class SecurityEditFragment : Fragment() {

    private lateinit var binding: FragmentSecurityeditBinding
    private val args: SecurityEditFragmentArgs by navArgs()
    private val nav by lazy { findNavController() }
    private val viewModel: SecurityViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentSecurityeditBinding.inflate(inflater, container, false)
        val guard = viewModel.get(args.guardID)
        if (guard == null) {
            toast("Security guard is no longer available.")
            nav.navigateUp()
            return binding.root
        }
        binding.edtName.setText(guard.guardName)
        binding.edtPw.setText(guard.guardPassword)
        binding.edtPhoneNum.setText(guard.guardPhoneNo)
        binding.btnSaveSe.setOnClickListener { save(guard) }
        binding.btnClose.setOnClickListener { nav.navigateUp() }
        return binding.root
    }

    private fun save(original: Security) {
        val updated = original.copy(
            guardName = binding.edtName.text.toString().trim(),
            guardPhoneNo = binding.edtPhoneNum.text.toString().trim(),
            guardPassword = binding.edtPw.text.toString().trim(),
        )
        val validationError = viewModel.validate(updated, insert = false)
        if (validationError.isNotEmpty()) {
            toast(validationError)
            return
        }

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val payload = ApiClient.toMap(updated).toMutableMap()
                if (updated.guardPassword.isBlank()) {
                    payload.remove("guardPassword")
                }
                ApiClient.api.updateRecord("security", original.guardID, payload)
                viewModel.init()
                nav.navigateUp()
            } catch (error: HttpException) {
                toast("Could not update security guard (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }

    private fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}
