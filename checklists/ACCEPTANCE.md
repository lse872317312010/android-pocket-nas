# Acceptance test matrix (blank until real devices tested)

| ID | Test | Pass criterion | Actual | Evidence |
|---|---|---|---|---|
| SFTP-01 | LAN list/read 100 MB file | Hash matches original | Not tested | TBD |
| SFTP-02 | Upload/rename/delete in temp folder | Correct results, restricted root | Not tested | TBD |
| SAF-01 | Open document from Android picker | File opens without manual pre-download | Not tested | TBD |
| SAF-02 | Video random seek | Can seek; reasonable buffering | Not tested | TBD |
| SYNC-01 | Camera send-only ingestion | Original arrives without lossy conversion | Not tested | TBD |
| SYNC-02 | Offline hot file | Open while disconnected | Not tested | TBD |
| SAFE-01 | Accidental deletion and recovery | Restore independently retained copy | Not tested | TBD |
| WAN-01 | Private mobile data access | Works with home Wi-Fi and no port forward | Not tested | TBD |
| VPN-01 | Clash coexistence | Document successful supported configuration | Not tested | TBD |
| REL-01 | Screen off 24 hours | Service accessible throughout | Not tested | TBD |
| REL-02 | 72-hour continuous operation | Failures and recovery recorded | Not tested | TBD |
| REL-03 | Reboot / Wi-Fi interruption | Service recovers within measured time | Not tested | TBD |
| SAFETY-01 | Charge/thermal safety | No abnormal heat; protections documented | Not tested | TBD |

Record: device/OS, exact application version, network conditions, commands, screenshots/log paths, observed metrics and tester notes. Never invent successful test outcomes.
