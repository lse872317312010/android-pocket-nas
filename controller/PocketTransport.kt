package com.scrcpy.remote.ui

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.system.Os
import android.system.OsConstants
import com.scrcpy.remote.adb.AdbDeviceConnection
import com.scrcpy.remote.adb.ConnectionPortResult
import com.scrcpy.remote.adb.NsdConnectionPortDiscovery
import io.github.muntashirakon.adb.AdbConnection
import java.io.IOException
import java.net.InetAddress
import java.net.Socket
import java.security.PublicKey
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive

/** One policy per ADB manager. Only the manager performing local pairing can enroll a new key. */
class PocketTransport private constructor(
    context: Context,
    private val pairingNetwork: Network? = null,
    private val pairingHost: String? = null,
) : AdbConnection.HomeTransport {
    private val networks = requireNotNull(context.getSystemService(ConnectivityManager::class.java))
    private val prefs = context.getSharedPreferences("pocket-security", Context.MODE_PRIVATE)
    @Volatile private var observed: String? = null

    override fun openSocket(host: String): Socket {
        val address = numeric(host)
        val network = when {
            pairingNetwork != null -> {
                if (host != pairingHost || !onLink(networks, pairingNetwork, address)) throw IOException("Home Wi-Fi changed")
                pairingNetwork
            }
            PocketPeer.isTailnet(address) -> {
                val vpn = activeVpn(networks)
                if (address !in vpn.getAllByName(HOME_NAME)) throw IOException("Unknown VPN peer")
                vpn
            }
            else -> {
                if (host != prefs.getString("host", null)) throw IOException("Unknown LAN peer")
                wifiFor(networks, address)
            }
        }
        return network.socketFactory.createSocket()
    }

    override fun verifyPeer(key: PublicKey) {
        if (pairingNetwork != null) observed = PocketPeer.fingerprint(key.encoded)
        else PocketPeer.requireMatch(prefs.getString("spki", null), key.encoded)
    }

    /** Called only after the six-digit PAKE succeeded, on the same Wi-Fi network and IP. */
    internal suspend fun finishPairing(context: Context, host: String, manager: AdbDeviceConnection) {
        check(pairingNetwork != null && host == pairingHost)
        val result = NsdConnectionPortDiscovery(context).resolveConnectionPort(host, 1, true)
        val port = when (result) {
            is ConnectionPortResult.Updated -> result.port
            is ConnectionPortResult.Unchanged -> result.port
            else -> throw IOException("Home debugging service was not uniquely resolved")
        }
        currentCoroutineContext().ensureActive()
        if (!manager.connect(host, port)) throw IOException("Home TLS enrollment failed")
        currentCoroutineContext().ensureActive()
        val pin = observed ?: throw IOException("Home TLS key missing")
        if (!prefs.edit().putString("spki", pin).putString("host", host).commit()) throw IOException("Could not store peer")
    }

    companion object {
        private const val HOME_NAME = "pocket-nas"

        fun remembered(context: Context) = PocketTransport(context.applicationContext)

        fun enrollment(context: Context, host: String): PocketTransport {
            val networks = requireNotNull(context.getSystemService(ConnectivityManager::class.java))
            return PocketTransport(context.applicationContext, wifiFor(networks, numeric(host)), host)
        }

        fun awayAddress(context: Context): String {
            val vpn = activeVpn(requireNotNull(context.getSystemService(ConnectivityManager::class.java)))
            return vpn.getAllByName(HOME_NAME).distinct().filter(PocketPeer::isTailnet)
                .singleOrNull()?.hostAddress ?: throw IOException("Ambiguous or missing home VPN address")
        }

        private fun numeric(host: String): InetAddress =
            Os.inet_pton(OsConstants.AF_INET, host) ?: Os.inet_pton(OsConstants.AF_INET6, host.substringBefore('%'))
                ?: throw IOException("Numeric IP address required")

        private fun activeVpn(networks: ConnectivityManager): Network {
            val network = networks.activeNetwork ?: throw IOException("VPN offline")
            if (networks.getNetworkCapabilities(network)?.hasTransport(NetworkCapabilities.TRANSPORT_VPN) != true) {
                throw IOException("VPN not active for this application")
            }
            return network
        }

        private fun onLink(networks: ConnectivityManager, network: Network, address: InetAddress): Boolean {
            val caps = networks.getNetworkCapabilities(network) ?: return false
            if (!PocketPeer.isLan(address) || !caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) ||
                caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) return false
            return networks.getLinkProperties(network)?.routes?.any { route ->
                route.destination.prefixLength > 0 && route.gateway?.isAnyLocalAddress != false && route.destination.contains(address)
            } == true
        }

        @Suppress("DEPRECATION")
        private fun wifiFor(networks: ConnectivityManager, address: InetAddress): Network =
            networks.allNetworks.singleOrNull { onLink(networks, it, address) } ?: throw IOException("Home Wi-Fi required")
    }
}
