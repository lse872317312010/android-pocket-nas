# Optional Personal OS adapter — boundary contract

This repository operates independently of Personal OS. Any integration should use a separate adapter consuming established protocols.

## Suggested read capabilities
- `storage.list` / `storage.stat` / `storage.read`: SFTP/WebDAV via existing client library.
- `storage.write`: controlled path and authorization; default off for automation.
- `device.health`: explicit status collector on server if justified, never assumed available from SFTP.
- `sync.status`: use Syncthing's supported existing API if available and authorized.

## Rules
- Do not expose filesystem roots directly to remote AI agents.
- Whitelist paths and permission scopes; keep sensitive logs/credentials outside source control.
- Do not couple app business logic to a particular Android server implementation.
- Prefer a CLI or conventional service API over a custom persistent agent where it adds no value.
- No autonomous deletion, archival or transfer without deliberate policy and recovery capability.
