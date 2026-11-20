# Reuse-first solution evaluation

Status is **research**, not practical validation. Before installation, independently check releases, maintainers, licensing and platform support.

| Component | Role | Strength | Key question / limitation |
|---|---|---|---|
| SshDaemon | Native Android SSH/SFTP server | Small service surface, minimal setup | Background longevity, SAF/shared-storage permissions, security settings |
| Primitive FTPd | Native FTP/SFTP service | Alternative with Android UI | Startup behavior, SFTP and performance on target OS |
| Termux + OpenSSH | Scriptable SSH/SFTP server | Flexible and extensible | Doze/OEM kills, storage permission, maintenance burden |
| RSAF | SAF document provider backed by rclone | Can open remote files in SAF-compatible apps | App-specific compatibility, random access, write semantics, cache |
| Syncthing-Fork | Hot-file syncing | Decentralized syncing and offline copies | Delete propagation, storage/battery use, platform lifecycle |
| Tailscale | Encrypted private reachability | No router port forwarding in normal design | VPN coexistence with Clash, relay performance |
| copyparty | Web file server | Web browser interface, advanced transfers | Complexity, Termux runtime, auth and exposure hardening |
| OpenList | Consolidated web file frontend | Multi-backend access | Mobile edition maturity and provider details |
| Homedroid | All-in-one Android server | Potential rapid setup | Beta maturity, app provenance, operations/security validation |
| NOVA Video Player | Network media client | Network-streaming media usage | Actual SFTP playback/seek on phone and file types |

## Evaluation order
1. SshDaemon + local SFTP test.
2. RSAF + SFTP on LAN (SAF and random-seek tests).
3. Syncthing-Fork restricted-directory transfer and deletion recovery.
4. Tailscale remote network / Clash conflict.
5. Only if needed: OpenList, copyparty or Homedroid. Do not install all servers at once.

## Decision criteria
- Operational stability (most important)
- Minimal attack surface and trusted maintenance
- Data correctness and recovery
- SAF client compatibility
- Setup and ongoing maintenance cost
- Optional Personal OS extensibility
