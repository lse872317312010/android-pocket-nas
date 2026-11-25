package com.scrcpy.remote.ui

import java.net.InetAddress
import java.security.cert.CertificateException
import org.junit.Assert.*
import org.junit.Test

class PocketPeerTest {
    @Test fun checkedKeyCannotBeMissingOrReplaced() {
        val key = "paired public key".toByteArray()
        val stored = PocketPeer.fingerprint(key)
        PocketPeer.requireMatch(stored, key)
        assertThrows(CertificateException::class.java) { PocketPeer.requireMatch(null, key) }
        assertThrows(CertificateException::class.java) { PocketPeer.requireMatch(stored, byteArrayOf(1, 2)) }
    }

    @Test fun onlyOverlayAddressesAreEligibleForRemoteResolution() {
        for (ip in listOf("100.64.0.1", "100.127.255.254")) assertTrue(PocketPeer.isTailnet(InetAddress.getByName(ip)))
        for (ip in listOf("100.63.255.255", "100.128.0.1", "192.168.1.1", "8.8.8.8", "::1")) {
            assertFalse(PocketPeer.isTailnet(InetAddress.getByName(ip)))
        }
    }

    @Test fun enrollmentIsLimitedToLocalAddressFamilies() {
        for (ip in listOf("192.168.0.9", "10.1.2.3", "172.31.1.1", "fd00::2", "fe80::3"))
            assertTrue(PocketPeer.isLan(InetAddress.getByName(ip)))
        for (ip in listOf("100.64.1.1", "8.8.8.8", "127.0.0.1", "::1", "2001:db8::2"))
            assertFalse(PocketPeer.isLan(InetAddress.getByName(ip)))
    }
}
