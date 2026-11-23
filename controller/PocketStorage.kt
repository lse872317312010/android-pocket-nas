package com.scrcpy.remote.ui

internal data class PocketStorage(val totalBytes: Long, val availableBytes: Long) {
    companion object {
        // Toybox df -k uses KiB and a percentage column. A long filesystem name may wrap.
        private val row = Regex("""(?:^|\s)(\d+)\s+\d+\s+(\d+)\s+\d+%\s+/.*$""")

        fun fromDf(output: String): PocketStorage? {
            for (line in output.lineSequence()) {
                val match = row.find(line.trim()) ?: continue
                val total = match.groupValues[1].toLongOrNull() ?: continue
                val available = match.groupValues[2].toLongOrNull() ?: continue
                if (total in 1..Long.MAX_VALUE / 1024 && available in 0..total) {
                    return PocketStorage(total * 1024, available * 1024)
                }
            }
            return null
        }
    }
}
