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
import com.example.firebasedemo2.data.ApiClient
import com.example.firebasedemo2.data.Security
import com.example.firebasedemo2.data.SecurityViewModel
import com.example.firebasedemo2.databinding.FragmentAddsgBinding
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

class AddSGFragment : Fragment() {

    private lateinit var binding: FragmentAddsgBinding
    private val nav by lazy { findNavController() }
    private val viewModel: SecurityViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        binding = FragmentAddsgBinding.inflate(inflater, container, false)
        binding.btnAddSe.setOnClickListener { add() }
        binding.btnReset.setOnClickListener { reset() }
        binding.btnClose.setOnClickListener { nav.navigateUp() }
        return binding.root
    }

    private fun reset() {
        binding.edtName.text.clear()
        binding.edtPw.text.clear()
        binding.edtPhoneNum.text.clear()
        binding.edtName.requestFocus()
    }

    private fun add() {
        val context = requireContext()
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val guards = ApiClient.listRecords("security", Security::class.java)
                val nextNumber = (guards.mapNotNull {
                    it.guardID.filter(Char::isDigit).toIntOrNull()
                }.maxOrNull() ?: 0) + 1
                val guard = Security(
                    guardID = "SG${nextNumber.toString().padStart(5, '0')}",
                    guardName = binding.edtName.text.toString().trim(),
                    guardPhoneNo = binding.edtPhoneNum.text.toString().trim(),
                    guardPassword = binding.edtPw.text.toString().trim(),
                    adminID = ApiClient.accountId(context).orEmpty(),
                )
                val validationError = viewModel.validate(guard)
                if (validationError.isNotEmpty()) {
                    toast(validationError)
                    return@launch
                }
                ApiClient.api.createRecord("security", ApiClient.toMap(guard))
                viewModel.init()
                nav.navigateUp()
            } catch (error: HttpException) {
                toast("Could not add security guard (${error.code()}).")
            } catch (error: IOException) {
                toast("Cannot connect to the PostgreSQL API.")
            }
        }
    }

    private fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }
}
