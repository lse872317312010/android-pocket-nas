package com.scrcpy.remote.ui

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PocketStorageTest {
    @Test fun parsesToyboxAndWrappedRowsInKiB() {
        val expected = PocketStorage(1_024_000_000_000L, 250_000L * 1024)
        val row = "1000000000 999750000 250000 99% /storage/emulated"
        assertEquals(expected, PocketStorage.fromDf("Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/fuse  $row"))
        assertEquals(expected, PocketStorage.fromDf("/dev/fuse\n    $row"))
        assertEquals(PocketStorage(1024, 0), PocketStorage.fromDf("dev 1 1 0 100% /sdcard"))
    }

    @Test fun rejectsErrorsOverflowAndImpossibleValues() {
        for (bad in listOf("Permission denied", "", "dev 5 1 6 20% /mnt", "dev 9223372036854775807 0 0 0% /mnt")) {
            assertNull(PocketStorage.fromDf(bad))
        }
    }
}
