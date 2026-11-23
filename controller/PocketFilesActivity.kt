package com.scrcpy.remote.ui

import android.app.AlertDialog
import android.net.Uri
import android.os.Bundle
import android.os.CancellationSignal
import android.os.SystemClock
import android.text.format.Formatter
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.lifecycle.lifecycleScope
import com.scrcpy.remote.adb.AdbDeviceConnection
import com.scrcpy.remote.adb.AdbStreamChannel
import com.scrcpy.remote.adb.AdbSync
import com.scrcpy.remote.data.DeviceRepository
import com.scrcpy.remote.data.SavedDevice
import com.scrcpy.remote.scrcpy.ScrcpySession
import com.scrcpy.remote.session.FileTransfers
import com.scrcpy.remote.session.ResourceHandoff
import java.io.Closeable
import kotlin.concurrent.thread
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class PocketFilesActivity : ComponentActivity() {
    private lateinit var device: SavedDevice
    private lateinit var space: TextView
    private lateinit var status: TextView
    private lateinit var send: Button
    private lateinit var mirror: Button
    private lateinit var refresh: Button
    private var transfer: Transfer? = null
    private val prefs by lazy { getSharedPreferences("pocket-files", MODE_PRIVATE) }
    private val selectFile = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null && transfer == null) upload(uri)
    }

    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val id = intent.getStringExtra("deviceId")
        device = DeviceRepository.get(this).getDevices().firstOrNull { it.id == id }
            ?: run { finish(); return }
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val inset = (24 * resources.displayMetrics.density).toInt()
            setPadding(inset, 2 * inset, inset, inset)
        }
        fun label(value: String, size: Float): TextView = TextView(this).apply {
            text = value
            textSize = size
            panel.addView(this)
        }
        fun button(value: String, run: () -> Unit): Button = Button(this).apply {
            text = value
            setOnClickListener { run() }
            panel.addView(this)
        }
        label("家庭机", 26f)
        space = label("", 17f)
        refresh = button("刷新存储空间", ::refreshSpace)
        send = button("发送文件到家庭机") { selectFile.launch(arrayOf("*/*")) }
        mirror = button("打开家庭机屏幕") {
            startActivity(MirrorActivity.newIntent(this, device.host, device.port, device.id))
        }
        status = label(prefs.getString("last", null) ?: "所选文件将保存到家庭机的 Download 目录。", 16f)
        setContentView(ScrollView(this).apply { addView(panel) })
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (transfer == null) { finish(); return }
                AlertDialog.Builder(this@PocketFilesActivity)
                    .setMessage("正在发送文件，退出会中断传输。")
                    .setNegativeButton("继续发送", null)
                    .setPositiveButton("停止并退出") { _, _ -> finish() }
                    .show()
            }
        })
        refreshSpace()
    }

    private fun refreshSpace() {
        if (!refresh.isEnabled) return
        refresh.isEnabled = false
        space.text = "正在读取家庭机存储空间…"
        lifecycleScope.launch {
            try {
                val storage = withContext(Dispatchers.IO) {
                    withDevice { connection ->
                        PocketStorage.fromDf(connection.runShellCommand("df -k /sdcard")) ?: error("df")
                    }
                }
                fun format(bytes: Long) = Formatter.formatFileSize(this@PocketFilesActivity, bytes)
                space.text = "可用 " + format(storage.availableBytes) + "  /  共 " + format(storage.totalBytes)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                space.text = "未能读取空间。请确认家庭机在线且无线调试已开启，然后刷新。"
            } finally {
                refresh.isEnabled = true
            }
        }
    }

    private fun <T> withDevice(action: (AdbDeviceConnection) -> T): T {
        val connection = AdbDeviceConnection.create(applicationContext)
        try {
            check(connection.connect(device.host, device.port))
            return action(connection)
        } finally {
            runCatching { connection.disconnect() }
        }
    }

    private class Transfer {
        val signal = CancellationSignal()
        val sources = ResourceHandoff<Closeable>()
        val channels = ResourceHandoff<Closeable>()
        fun stop() {
            thread(name = "pocket-transfer-stop") {
                try { signal.cancel() } finally {
                    try { sources.close() } finally { channels.close() }
                }
            }
        }
    }

    private fun upload(uri: Uri) {
        val tx = Transfer()
        transfer = tx
        send.isEnabled = false
        mirror.isEnabled = false
        status.text = "正在读取所选文件…"
        lifecycleScope.launch {
            try {
                val path = withContext(Dispatchers.IO) {
                    val file = FileTransfers.describe(contentResolver, uri, tx.signal)
                    require(file.size <= FileTransfers.MAX_BYTES) { "size-limit" }
                    var lastUpdate = 0L
                    withDevice { connection ->
                        FileTransfers.withSource(contentResolver, uri, tx.signal, tx.sources::offer, tx.sources::release) { input ->
                            tx.signal.throwIfCanceled()
                            prefs.edit().putString("last", "上次发送结果待核对，请在家庭机 Download 中查看：" + file.name).apply()
                            ScrcpySession.pushFile(
                                openSync = { AdbStreamChannel(connection.openSync()) },
                                source = input, size = file.size, displayName = file.name,
                                onProgress = { bytes ->
                                    val now = SystemClock.elapsedRealtime()
                                    if (now - lastUpdate >= 250 || bytes == file.size) {
                                        lastUpdate = now
                                        runOnUiThread {
                                            if (transfer === tx) status.text = "正在发送 " + file.name + " · " +
                                                FileTransfers.formatSize(bytes) + " / " + FileTransfers.formatSize(file.size)
                                        }
                                    }
                                },
                                isCancelled = { tx.signal.isCanceled },
                                onChannelOpen = tx.channels::offer, onChannelClosed = tx.channels::release
                            )
                        }
                    }
                }
                val note = "已发送到家庭机：" + path
                prefs.edit().putString("last", note).apply()
                status.text = note
                refreshSpace()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: AdbSync.SyncCommitUnconfirmedException) {
                status.text = "家庭机的完成回执丢失。请先检查 Download，再决定是否重发。"
            } catch (error: Exception) {
                status.text = if (error is IllegalArgumentException && error.message == "size-limit")
                    "单个文件上限为 512 MiB，请选择较小的文件。"
                else "发送失败。请确认所选文件可读取、家庭机在线且存储空间充足。"
            } finally {
                transfer = null
                send.isEnabled = true
                mirror.isEnabled = true
            }
        }
    }

    override fun onDestroy() {
        transfer?.stop()
        super.onDestroy()
    }
}
