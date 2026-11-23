package com.scrcpy.remote.ui

import android.content.Intent
import android.os.Bundle
import android.text.InputType
import android.widget.*
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.lifecycle.lifecycleScope
import com.scrcpy.remote.adb.*
import com.scrcpy.remote.data.*
import java.io.Closeable
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** A launcher for one owner-paired phone. Pairing, mirroring and key storage belong to Scrcpy Android. */
class PocketHomeActivity : ComponentActivity() {
    private val pairing: MainViewModel by viewModels()
    private val repository by lazy { DeviceRepository.get(this) }
    private val prefs by lazy { getSharedPreferences("pocket-home", MODE_PRIVATE) }
    private val discovery by lazy { NsdConnectionPortDiscovery(this) }
    private lateinit var box: LinearLayout
    private var browser: Closeable? = null
    private var generation = 0
    private var busy = false
    private val id = "android-pocket-nas-screen"
    private var pendingHost: String? = null

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val margin = (24 * resources.displayMetrics.density).toInt()
            setPadding(margin, margin * 2, margin, margin)
        }
        setContentView(ScrollView(this).also { it.addView(box) })
        pendingHost = state?.getString("pending")
        lifecycleScope.launch {
            pairing.pairingState.collect { result ->
                when (result) {
                    is PairingState.Success -> pendingHost?.let { host ->
                        prefs.edit().putString("paired", host).apply()
                        pendingHost = null
                        connect(host)
                    }
                    is PairingState.Failure -> {
                        pendingHost = null
                        message("配对失败。请在家庭机重新打开配对码，再重试。")
                        button("重新查找", ::findPhone)
                    }
                    else -> Unit
                }
            }
        }
        val host = prefs.getString("paired", null)
        when {
            pendingHost != null && pairing.pairingState.value != PairingState.Idle -> message("正在配对…")
            host != null && getSharedPreferences("pocket-security", MODE_PRIVATE).contains("spki") -> connect(host)
            else -> findPhone()
        }
    }

    private fun message(text: String) {
        closeBrowser()
        box.removeAllViews()
        box.addView(TextView(this).apply { this.text = text; textSize = 19f })
    }

    private fun button(label: String, action: () -> Unit) {
        box.addView(Button(this).apply { text = label; setOnClickListener { action() } })
    }

    private fun closeBrowser() {
        generation++
        browser?.close()
        browser = null
    }

    private fun findPhone() {
        message("两台手机连同一 Wi-Fi。在家庭机打开「无线调试 → 使用配对码配对设备」，然后点下面出现的家庭机。")
        val token = generation
        val listed = mutableMapOf<String, Button>()
        fun update(action: () -> Unit) = runOnUiThread { if (generation == token && !isDestroyed) action() }
        val listener = object : AdbServiceBrowser.Listener {
            override fun onFound(id: String) {}
            override fun onResolutionFailed(id: String) = onLost(id)
            override fun onLost(id: String) = update { listed.remove(id)?.let(box::removeView) }
            override fun onFailure(errorCode: Int?) = update {
                message("当前 Wi-Fi 无法发现设备。确认两台手机在同一局域网，并重新打开家庭机配对码。")
                button("重新查找", ::findPhone)
            }
            override fun onResolved(id: String, service: DiscoveredAdbService) {
                val host = service.hosts.firstOrNull { ':' !in it } ?: service.hosts.firstOrNull() ?: return
                update {
                    listed.remove(id)?.let(box::removeView)
                    val row = Button(this@PocketHomeActivity).apply {
                        text = "配对家庭机 · " + host
                        setOnClickListener { enterCode(host, service.port) }
                    }
                    listed[id] = row
                    box.addView(row)
                }
            }
        }
        button("重新查找", ::findPhone)
        try { browser = discovery.browse("_adb-tls-pairing._tcp.", listener) }
        catch (_: Exception) { listener.onFailure(null) }
    }

    private fun enterCode(host: String, port: Int) {
        message("输入家庭机此刻显示的六位配对码")
        val code = EditText(this).apply {
            inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_VARIATION_PASSWORD
            filters = arrayOf(android.text.InputFilter.LengthFilter(6))
            isSaveEnabled = false
        }
        box.addView(code)
        button("配对并连接") {
            val digits = code.text.toString()
            if (!digits.matches(Regex("[0-9]{6}"))) { code.error = "需要六位数字"; return@button }
            pendingHost = host
            code.text.clear()
            message("正在使用 Android 无线调试配对…")
            pairing.pair(host, port, digits)
        }
        button("返回选择设备", ::findPhone)
    }

    private fun connect(host: String) {
        if (busy) return
        busy = true
        message("正在连接已配对的家庭机…")
        lifecycleScope.launch {
            try {
                val saved = repository.getDevices().firstOrNull { it.id == id && it.host == host }
                val port = when (val found = discovery.resolveConnectionPort(host, saved?.port ?: 1, true)) {
                    is ConnectionPortResult.Updated -> found.port
                    is ConnectionPortResult.Unchanged -> found.port
                    ConnectionPortResult.NotFound, is ConnectionPortResult.Unavailable -> null
                    else -> null
                }
                if (port == null) {
                    if (saved != null) {
                        openAway(saved)
                        return@launch
                    }
                    message("已配对，但没有找到家庭机连接端口。请保持无线调试开启，回到家庭 Wi-Fi 再试。")
                } else {
                    val profile = requireNotNull(ProfileBackupCodec.decode(assets.open("pocket-screen.json").use { it.readBytes() }).devices.single().mirroringSettings)
                    val device = SavedDevice(id, "家庭机", host, port, mirroringSettings = profile)
                    if (!repository.mutate { saveDevice(device) }) error("save")
                    openHome(device)
                    message("已返回连接页。")
                }
            } catch (cancelled: kotlinx.coroutines.CancellationException) { throw cancelled }
            catch (_: Exception) { message("连接准备失败。请检查 Wi-Fi 和家庭机的无线调试。") }
            finally { busy = false }
            button("连接家庭机") { connect(host) }
            val saved = repository.getDevices().firstOrNull { it.id == id && it.host == host }
            if (saved != null) button("通过 Tailscale 连接") { connectAway(saved) }
            button("重新配对", ::findPhone)
        }
    }

    private fun connectAway(saved: SavedDevice) {
        if (busy) return
        lifecycleScope.launch { openAway(saved) }
    }

    private suspend fun openAway(saved: SavedDevice) {
        busy = true
        message("正在解析 Tailscale 中的 pocket-nas…")
        run {
            try {
                val addr = withContext(Dispatchers.IO) {
                    PocketTransport.awayAddress(this@PocketHomeActivity)
                }
                val copy = saved.copy(id = "$id-away", host = addr)
                if (!repository.mutate { saveDevice(copy) }) error("save")
                openHome(copy)
                message("已返回异地连接页。")
            } catch (cancelled: kotlinx.coroutines.CancellationException) { throw cancelled }
            catch (_: Exception) { message("请连接 Tailscale，并确认家庭机在私网中的名称为 pocket-nas。") }
            finally { busy = false }
            button("重试异地连接") { connectAway(saved) }
            button("家庭 Wi-Fi 连接") { connect(saved.host) }
            button("重新配对", ::findPhone)
        }
    }

    private fun openHome(device: SavedDevice) {
        startActivity(Intent(this, PocketFilesActivity::class.java).putExtra("deviceId", device.id))
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString("pending", pendingHost)
    }
    override fun onDestroy() {
        closeBrowser()
        super.onDestroy()
    }
}
