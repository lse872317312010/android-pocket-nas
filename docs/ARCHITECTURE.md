# Architecture and threat model

## Data roles
- **Cold data:** server-only video, archive, original files.
- **Hot data:** small whitelisted folders synced to primary device.
- **Camera ingest:** primary sends copies; server receives and snapshots/archives independently.
- **Recovery copy:** separately stored backup, not merely a two-way Syncthing mirror.

## Paths and isolation
- SFTP service listens only on trusted LAN/private tailnet when feasible.
- No public router port forwarding by default.
- Use unique service account and SSH keys when supported; disable unnecessary services.
- Maintain an inventory of exposed ports, credentials lifecycle and app versions (no secrets committed).

## Failure states
- Screen-off and Doze kill server: detect/recover and measure recovery time.
- Home Wi-Fi drop: reconnect; no silent file corruption.
- Phone reboot/power loss: check whether service resumes without manual action.
- VPN client conflicts: use a supported VPN configuration, never assume two Android VPN services coexist.
- Accidental delete propagated by sync: retention/snapshot or separate backup prevents permanent loss.
- Charger/battery thermal issue: prioritize safe charge limits and ventilation; stop at abnormal heat/swelling.

## Personal OS boundary
Current project owns device-level deployment and existing protocols. Personal OS remains an optional client/orchestrator, not an implementation dependency. See PERSONAL_OS_ADAPTER.md.
