package com.scrcpy.remote.ui

import java.net.InetAddress
import java.security.MessageDigest
import java.security.cert.CertificateException
import java.util.Base64

internal object PocketPeer {
    fun fingerprint(key: ByteArray): String =
        Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-256").digest(key))

    fun requireMatch(stored: String?, key: ByteArray) {
        if (stored == null || stored != fingerprint(key)) {
            throw CertificateException("Family phone identity could not be verified")
        }
    }

    fun isTailnet(address: InetAddress): Boolean {
        val bytes = address.address
        return bytes.size == 4 && bytes[0].toInt() == 100 && (bytes[1].toInt() and 255) in 64..127
    }

    fun isLan(address: InetAddress): Boolean {
        val bytes = address.address
        return address.isSiteLocalAddress || address.isLinkLocalAddress ||
            (bytes.size == 16 && (bytes[0].toInt() and 254) == 252)
    }
}
