package com.example.firebasedemo2.data

import android.content.Context
import android.net.Uri
import com.bumptech.glide.load.model.GlideUrl
import com.bumptech.glide.load.model.LazyHeaders
import com.example.firebasedemo2.BuildConfig
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName
import com.google.gson.reflect.TypeToken
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.QueryMap

data class ApiLoginRequest(
    val role: String,
    val id: String,
    val password: String
)

data class ApiLoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: Map<String, Any?>
)

data class ApiPasswordResetRequest(val id: String)
data class ApiPasswordResetConfirmation(val id: String, val code: String, val password: String)
data class ApiMessageResponse(val message: String)

data class ApiCurrentUserResponse(val user: Map<String, Any?>)
data class ApiRecordsResponse<T>(val records: List<T>)
data class ApiRecordResponse<T>(val record: T)

interface ApiService {
    @POST("api/auth/login")
    suspend fun login(@Body body: ApiLoginRequest): ApiLoginResponse

    @POST("api/auth/password-reset/request")
    suspend fun requestPasswordReset(@Body body: ApiPasswordResetRequest): ApiMessageResponse

    @POST("api/auth/password-reset/confirm")
    suspend fun confirmPasswordReset(@Body body: ApiPasswordResetConfirmation): ApiMessageResponse

    @GET("api/auth/me")
    suspend fun currentUser(): ApiCurrentUserResponse

    @GET("api/records/{resource}")
    suspend fun listRecords(
        @Path("resource") resource: String,
        @QueryMap filters: Map<String, String> = emptyMap()
    ): ApiRecordsResponse<Map<String, Any?>>

    @GET("api/records/{resource}/{recordId}")
    suspend fun getRecord(
        @Path("resource") resource: String,
        @Path("recordId") recordId: String
    ): ApiRecordResponse<Map<String, Any?>>

    @POST("api/records/{resource}")
    suspend fun createRecord(
        @Path("resource") resource: String,
        @Body record: Map<String, Any?>
    ): ApiRecordResponse<Map<String, Any?>>

    @PUT("api/records/{resource}/{recordId}")
    suspend fun replaceRecord(
        @Path("resource") resource: String,
        @Path("recordId") recordId: String,
        @Body record: Map<String, Any?>
    ): ApiRecordResponse<Map<String, Any?>>

    @PATCH("api/records/{resource}/{recordId}")
    suspend fun updateRecord(
        @Path("resource") resource: String,
        @Path("recordId") recordId: String,
        @Body record: Map<String, Any?>
    ): ApiRecordResponse<Map<String, Any?>>

    @DELETE("api/records/{resource}/{recordId}")
    suspend fun deleteRecord(
        @Path("resource") resource: String,
        @Path("recordId") recordId: String
    )
}

object ApiClient {
    private const val PREFERENCES = "POSTGRES_API_AUTH"
    private const val ACCESS_TOKEN = "access_token"
    private const val ACCOUNT_ID = "account_id"
    private const val ACCOUNT_ROLE = "account_role"

    @Volatile
    private var applicationContext: Context? = null

    private val service: ApiService by lazy {
        val tokenInterceptor = Interceptor { chain ->
            val request = chain.request().newBuilder().apply {
                val context = applicationContext
                val token = context
                    ?.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
                    ?.getString(ACCESS_TOKEN, null)
                if (!token.isNullOrBlank()) {
                    header("Authorization", "Bearer $token")
                }
            }.build()
            chain.proceed(request)
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(tokenInterceptor)
            .build()
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }

    fun initialize(context: Context) {
        applicationContext = context.applicationContext
    }

    suspend fun signIn(context: Context, role: String, id: String, password: String): Map<String, Any?> {
        initialize(context)
        val response = service.login(ApiLoginRequest(role, id, password))
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
            .edit()
            .putString(ACCESS_TOKEN, response.accessToken)
            .putString(ACCOUNT_ID, id)
            .putString(ACCOUNT_ROLE, role)
            .apply()
        return response.user
    }

    suspend fun restoreSession(context: Context): Map<String, Any?>? {
        initialize(context)
        val preferences = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
        if (preferences.getString(ACCESS_TOKEN, null).isNullOrBlank()) return null
        return try {
            service.currentUser().user
        } catch (_: retrofit2.HttpException) {
            signOut(context)
            null
        }
    }

    fun signOut(context: Context) {
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE).edit().clear().apply()
    }

    fun accountId(context: Context): String? =
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE).getString(ACCOUNT_ID, null)

    fun accountRole(context: Context): String? =
        context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE).getString(ACCOUNT_ROLE, null)

    fun <T> decode(value: Map<String, Any?>, type: Class<T>): T =
        Gson().fromJson(Gson().toJson(value), type)

    fun toMap(value: Any): Map<String, Any?> =
        Gson().fromJson(
            Gson().toJson(value),
            object : TypeToken<Map<String, Any?>>() {}.type
        )

    suspend fun <T> listRecords(
        resource: String,
        type: Class<T>,
        filters: Map<String, String> = emptyMap()
    ): List<T> = service.listRecords(resource, filters).records.map { decode(it, type) }

    /** Violation evidence photo (stored in private Supabase Storage, served by the API). */
    fun blockedPhoto(context: Context, blockedId: String): GlideUrl {
        val token = context.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
            .getString(ACCESS_TOKEN, null).orEmpty()
        val url = "${BuildConfig.API_BASE_URL.trimEnd('/')}/api/blocked/${Uri.encode(blockedId)}/photo"
        return GlideUrl(url, LazyHeaders.Builder().addHeader("Authorization", "Bearer $token").build())
    }

    val api: ApiService
        get() = service
}
