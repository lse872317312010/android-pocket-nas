package com.scrcpy.remote.ui

internal data class PocketPairAddress(val host: String, val port: Int) {
    companion object {
        fun port(text: String): Int? =
            text.trim().takeIf { it.length in 1..5 && it.all { digit -> digit in '0'..'9' } }
                ?.toIntOrNull()?.takeIf { it in 1..65535 }

        // Manual setup mirrors the IPv4 address and port Android shows on the main debugging page.
        fun parse(text: String): PocketPairAddress? {
            val parts = text.trim().split(':')
            if (parts.size != 2) return null
            val octets = parts[0].split('.')
            if (octets.size != 4 || octets.any { octet ->
                    val n = octet.toIntOrNull()
                    n == null || n !in 0..255 || n.toString() != octet
                }) return null
            return PocketPairAddress(parts[0], port(parts[1]) ?: return null)
        }
    }
}
