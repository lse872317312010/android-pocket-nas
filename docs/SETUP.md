# 无 Root 部署指南 / Setup runbook — no root baseline

## 中文部署步骤

先确认两部手机的型号与系统版本，从官方渠道更新应用。重要数据另做备份，首次测试使用同一 Wi-Fi 和不含私人数据的目录。

1. **局域网 SFTP**：在 1 TB 手机上安装 SshDaemon 或选定的备选组件，授予必要的共享存储权限，配置认证与端口，仅在局域网或私有 VPN 使用。客户端连接家庭手机的 Wi-Fi 地址，在临时目录测试列目录、读写、重命名和删除，并单独验证越界访问被拒绝。息屏 30、60 分钟后分别复测。
2. **主力机按需访问**：在 256 GB 手机上安装 RSAF，按实际版本说明配置 rclone SFTP 后端。在两到三个常用应用中打开系统文件选择器，验证浏览、预览和写入。用大视频测试跳转，观察下载量和缓存占用。
3. **指定目录同步**：两机安装 Syncthing-Fork，通过设备 ID 或二维码配对。相机接收、双向工作目录、离线热文件分别配置。为重要文件设置独立版本备份或快照，验证离线打开和误删恢复。
4. **异地访问**：两机加入同一私有 Tailscale 网络，RSAF 使用服务端私网地址或名称。关闭主力机 Wi-Fi，以移动网络测试访问与视频跳转延迟。开启 Clash VPN 时须验证并记录可用配置。
5. **无人值守**：按系统支持情况配置自启动、前台服务、后台电池策略及充电保护，保持通风。进行 72 小时息屏运行、Wi-Fi 中断及有人看护的重启恢复演练。记录可用性、功耗、温度、恢复文件的大小和哈希，以及故障次数。

### 可重复的 M1 传输测试

在装有 OpenSSH 客户端及 SFTP 服务端子系统的 Ubuntu 或 WSL 环境中运行 `bash scripts/check-sftp.sh --local`。CI 使用此模式验证协议操作。

测试家庭手机时，在私有 SSH 配置中设置别名、地址、端口、用户和密钥。先与服务端核对主机密钥，再保存至 known_hosts。账户起始目录须可写，至少预留 100 MB。运行 `bash scripts/check-sftp.sh pocket-nas`（替换为实际别名）。脚本上传 100 MB 随机文件，重命名、列出、下载、删除远端测试目录，最后核对 SHA-256 和逐字节内容。若中断，核对终端打印的目录名后手动清理该次测试目录。

分别记录 CI 和真机结果。文件选择器兼容性与目录权限隔离另行验证。公开日志和提交须移除密码、私钥、私网身份、家庭 IP、照片及恢复资料。

## English

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

### Repeatable M1 transfer check

On Ubuntu or WSL with OpenSSH installed, run `bash scripts/check-sftp.sh --local` to exercise the SFTP batch against a temporary local OpenSSH subsystem. CI runs this mode. It covers protocol operations only.

For the LAN test, configure an SSH alias with the home phone's address, port, user and key in your private SSH config. Verify the host key against the server before recording it in known_hosts. Point the account's starting directory at a writable test area with at least 100 MB free. Run `bash scripts/check-sftp.sh pocket-nas` using your alias. The script uploads a random 100 MB file, renames and lists it, downloads it, removes the remote test directory and compares the bytes and SHA-256 digests. On interruption, inspect the printed directory name and clean up that test directory manually. Keep connection details out of public logs.

Record the LAN result separately from CI. Android picker behavior and denial outside the allowed storage root require separate device tests.

### 相片历史版本与恢复 / Camera history and recovery

在家庭端等待相机同步完成，再运行一次备份。以私有、专用、已存在的 POSIX 目录作为备份库。真实部署请将备份库置于独立存储设备或故障域，确认已挂载且有空间；两个路径必须彼此独立，备份库应在所有同步和 SFTP 写入目录之外。此命令只捕获运行时可见的版本。修改期间的一次目录复制不具备原子快照语义。

After camera synchronization settles on home, run one capture. Use an existing dedicated private POSIX backup directory. For deployment, verify that the separate backup device or failure domain is mounted and has free space. Keep source and vault disjoint, and keep the vault outside synced folders and writable SFTP exports. Capture each revision you need to retain. A directory copy during active edits is not an atomic snapshot.

```sh
python3 scripts/backup_camera.py "$home_camera" "$vault"
```

工具复用 rclone 的内容校验和历史目录。最新备份在 `current/`；同名文件被替换前，其旧内容移到 `history/<本次运行编号>/` 下的原相对路径。源端删除不删除已备份副本。一次成功捕获有旧版时打印其历史目录。目录锁串行化同一库的捕获。失败可能留下部分更新和历史文件；保留两者，检查错误，在源端稳定后重试。历史文件占用空间，工具不会自动裁剪。

The tool uses rclone checksum comparison and a per-run backup directory. Latest captured files live under `current/`. A replaced file moves to its original relative path under `history/<capture ID>/`. Source deletion leaves captured files in place. A successful capture prints its history directory when it archived a revision. A directory lock serializes captures to the same vault. A failed copy may leave a partial update and archived files. Keep both, inspect the error and retry against a settled source. History consumes storage and has no automatic pruning.

恢复时按运行编号和相对路径选择版本，将其复制到同步范围以外的新建目录，并与已知原版 SHA-256 比对。练习结束只需移除该次恢复副本。停止备份只需停止运行捕获命令，保留备份库供后续恢复。

Select a capture ID and relative path, restore into a fresh directory outside synchronization, and compare the SHA-256 with the known digest of that revision. Undo the drill by removing the restored test copy. To stop captures, stop invoking the command and keep the vault for recovery.

```sh
restore_dir=$(mktemp -d)
cp -- "$vault/history/$capture_id/$relative_path" "$restore_dir/recovered-photo"
sha256sum "$restore_dir/recovered-photo"
```

`python3 simulation/run.py --scenario sync` 运行两个 Syncthing 实例，传送三份同名等长内容，演练离线、重连和误删，恢复中间版并核对 SHA-256。仿真的备份库位于同机独立目录。 / The sync scenario transfers three equal-size revisions using two Syncthing instances, exercises an offline read and a deletion after reconnect, then verifies the restored middle revision by SHA-256. Its vault is a separate directory on the same host.
