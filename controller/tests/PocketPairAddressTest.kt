package com.scrcpy.remote.ui

import org.junit.Assert.*
import org.junit.Test

class PocketPairAddressTest {
    @Test fun usesThePortFromTheHomePhone() {
        assertEquals(PocketPairAddress("192.168.0.108", 42119), PocketPairAddress.parse(" 192.168.0.108:42119 "))
        assertEquals(37865, PocketPairAddress.port("37865"))
    }

    @Test fun malformedEndpointsCannotBecomeAnotherDestination() {
        for (input in listOf("pocket-nas:1234", "192.168.1.2", "192.168.1.256:23", "010.0.0.1:80",
            "10.0.0.1:0", "10.0.0.1:65536", "10.0.0.1:12:34", "http://10.0.0.1:33", "10.0.0.1:+10")) {
            assertNull(input, PocketPairAddress.parse(input))
        }
    }
}
