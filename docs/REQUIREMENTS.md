# Requirements and constraints

## Hardware
- **Home node:** Snapdragon 7+ Gen-series Android phone, 1 TB internal storage; exact model/OS to confirm.
- **Primary:** Snapdragon 8 Elite-class Android phone, 256 GB storage; exact model/OS to confirm.
- Both devices assumed non-rooted until confirmed otherwise.

## Functional requirements
- Browsing remote directories, opening compatible files on demand from the primary phone.
- Streaming long videos without full pre-download, with seeking.
- Bi-directional sync for explicitly selected folders and one-way camera upload to a receiving/archiving destination.
- Secure LAN and mobile-data access with no unsolicited public exposure.
- Unattended home-node operations after screen off and connectivity changes.

## Nonfunctional requirements
- Minimal new code and minimal monthly cost.
- Prioritize security, battery health, recovery and data integrity over features.
- No accidental destructive mirror sync of the sole photo backup.
- Clear cache size limits on primary phone; offline hot files remain usable.

## Acceptance evidence
See ../checklists/ACCEPTANCE.md. Record phone model, OS build, app versions, setup steps, test timestamps, actual outcomes, screenshots/logs and connectivity conditions.

## Constraints to investigate
- Android single-VPN limitation (Tailscale vs Clash VPN mode).
- OEM power management, foreground service availability and reboot behavior.
- Android scoped-storage and SAF application compatibility.
- Android background server behavior; thermal and charge management.
- WAN throughput limited by home uplink, mobile downlink, latency and possible relay routing.
