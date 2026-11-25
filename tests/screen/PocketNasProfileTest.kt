package com.scrcpy.remote

import com.scrcpy.remote.data.ConfigurationSnapshot
import com.scrcpy.remote.data.MirrorSettings
import com.scrcpy.remote.data.ProfileBackupCodec
import com.scrcpy.remote.data.SavedDevice
import com.scrcpy.remote.data.planImport
import org.junit.Assert.*
import org.junit.Test

class PocketNasProfileTest {
    private fun template() = ProfileBackupCodec.decode(
        requireNotNull(javaClass.getResourceAsStream("/screen-control.json")).use { it.readBytes() },
    )

    @Test fun addsOneDeviceWithScreenControlsAndPreservesExistingDefaults() {
        val existing = SavedDevice("other", "Other", "192.0.2.2", 38000)
        val before = ConfigurationSnapshot(listOf(existing), MirrorSettings(maxFps = 30))
        val imported = planImport(before, template())
        assertEquals(1, imported.added)
        assertEquals(listOf(existing), imported.after.devices.filter { it.id == existing.id })
        assertEquals(before.settings, imported.after.settings)

        val home = imported.after.devices.single { it.id == "android-pocket-nas-screen" }
        assertEquals("192.0.2.1", home.host)
        val settings = requireNotNull(home.mirroringSettings).applyTo(imported.after.settings)
        assertEquals(0, settings.displayId)
        assertNull(settings.camera)
        assertNull(settings.virtualDisplay)
        assertTrue(settings.turnScreenOff)
        val args = settings.toOptions().toServerArgs()
        assertTrue("stay_awake=true" in args)
        assertTrue("power_off_on_close=true" in args)
    }

    @Test fun importingAgainKeepsTheOwnersEditedAddressAndPort() {
        val home = template().devices.single().copy(host = "192.0.2.35", port = 39001)
        val before = ConfigurationSnapshot(listOf(home), MirrorSettings())
        assertEquals(before, planImport(before, template()).after)
    }
}
