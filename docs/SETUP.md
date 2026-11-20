# Setup runbook — no root baseline

**Prerequisites:** confirm target hardware/OS, update apps from official repositories, keep a separate backup of important data, and test first on Wi-Fi with a non-sensitive sample folder.

## Phase 1: LAN SFTP
1. Install SshDaemon (or selected alternative) on 1 TB phone.
2. Grant only required Android shared-storage permissions, set strong authentication, configure SFTP port and keep the port on the LAN/private VPN only.
3. Determine home's Wi-Fi IP, connect from a client on same LAN using an SFTP-capable file manager.
4. Test list, read, upload, rename and deletion under a dedicated temporary test directory. Verify denial outside intended roots.
5. Lock the screen for 30/60 minutes; retest and record service survival.

## Phase 2: Remote files in Android SAF
1. Install RSAF on the 256 GB phone from a trusted release channel.
2. Configure rclone SFTP backend against the home node's LAN address/port (match actual RSAF instructions).
3. Open Android document picker in 2–3 representative apps; confirm browsing, preview and write behavior.
4. Test large video seek and measure whether client caches/downloads excessively.

## Phase 3: Selected data sync
1. Install Syncthing-Fork on both devices and pair by device ID/QR.
2. Use separate folders for photos ingest, bidirectional working documents and offline hot files.
3. Avoid using bidirectional sync as the only backup. Set up independently versioned/snapshotted backup.
4. Test offline access and deliberate deleted-file recovery.

## Phase 4: Away-from-home access
1. Install Tailscale and connect both devices to a private tailnet.
2. Point RSAF/SFTP at the server's tailnet address or supported name.
3. Disable Wi-Fi on primary phone and test mobile network access and seek latency.
4. If Clash is active in VPN mode, document mutually compatible networking design before relying on it.

## Phase 5: Unattended reliability
1. Configure supported autostart, foreground service and power/battery optimizations on the home phone.
2. Use OEM-supported charge protection where available. Maintain airflow, avoid hot conditions.
3. Run a 72-hour test with screen off, Wi-Fi interruptions and supervised reboot/recovery drills.
4. Record availability, power and temperature, recovered bytes/checksums and failure count.

**Never commit** passwords, private keys, private VPN IDs, precise home IPs, photo samples or security recovery material.
