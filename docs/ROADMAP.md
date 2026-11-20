# Roadmap

## M0 — Review and selection (current)
- [x] Initial set of existing component candidates documented.
- [x] Proposed architecture, constraints and test matrix drafted.
- [ ] User approves chosen components and device-specific constraints.

## M1 — Local file service proof
- [ ] SshDaemon SFTP read/write on LAN.
- [ ] RSAF document picker browse/read/write tests on primary phone.
- [ ] Video seeks and remote download behavior verified.

## M2 — Data tiering and safety
- [ ] Syncthing-Fork selected hot folders.
- [ ] Camera ingest without destructive mirroring.
- [ ] Independent recovery copy and deleted-file restore test.

## M3 — Secure remote access
- [ ] Private reachability from mobile network.
- [ ] Clash VPN conflict resolved or workaround documented.
- [ ] Access-control review and no public open port.

## M4 — Reliability / user acceptance
- [ ] 72-hour unattended power and background test.
- [ ] Reboot, network drop and storage-full drills.
- [ ] Performance, energy/thermal and recovery results recorded.

## M5 — Optional Personal OS adapter
- [ ] Only design a thin interface if real workflows require orchestration.
- [ ] No duplicate server, synchronization, browsing or VPN implementation.
