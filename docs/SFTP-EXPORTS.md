# SFTP 上传和只读发布 / Writable inbox and read-only publication

适用于单个可信上传者。家庭端 worker 通过本地路径写入正式文件和回执。SFTP 客户端获得两个入口，写入口只指向 `incoming/`，读入口只列出 `files/` 和 `receipts/`。读入口由服务端强制只读。多个客户端共享同一写凭据时，也共享收件箱的写权限。部署时应将该测试根目录从其他可写共享中移除。

This profile assumes one trusted uploader. The home worker publishes through local paths. The writable SFTP export points to `incoming/`. The server enforces read-only access on a second export containing `files/` and `receipts/`. Clients sharing the staging credential share write access to staging. Exclude the test root from other writable exports when using this profile.

## 家庭端 / Home

使用独立测试目录。以下示例中的绝对路径、服务地址和密钥路径均需替换。先用仓库中的 worker 初始化目录，再启动常驻 worker。两条 SFTP 命令分别在独立终端运行。同机仿真使用回环地址；局域网测试时使用家庭端的私有局域网地址。

Use a dedicated test root and replace the example absolute paths, address and key paths. Initialize with the existing worker, then run it continuously. Start each SFTP process in its own terminal. Use loopback for a single-host test or the home's private interface for a LAN test.

```sh
python3 scripts/drive_inbox.py /absolute/test-drive --once
python3 scripts/drive_inbox.py /absolute/test-drive
```

家庭端专用 rclone 配置 / Dedicated home rclone config:

```ini
[public]
type = combine
upstreams = "files=:local:/absolute/test-drive/files" "receipts=:local:/absolute/test-drive/receipts"
```

```sh
rclone --config "$home_cfg" serve sftp /absolute/test-drive/incoming \
  --addr "$bind_addr:2022" --key "$host_key" --authorized-keys "$client_pubkeys" --dir-cache-time 0s
rclone --config "$home_cfg" serve sftp public: --read-only \
  --addr "$bind_addr:2023" --key "$host_key" --authorized-keys "$client_pubkeys" --dir-cache-time 0s
```

目录缓存设为零，以便读入口立即观察 worker 在本地创建的回执。主机私钥和允许的公钥文件保存在共享路径之外。 / Zero directory-cache time lets the reader observe receipts created locally by the worker. Keep host keys and the authorized-keys file outside all exports.

## 上传端 / Upload client

在客户端的专用 rclone 配置中创建两个 SFTP 别名，均配置家庭端地址、客户端私钥及经独立核对的 `known_hosts_file`。`stage` 使用 2022 端口，`view` 使用 2023 端口。按实际地址及端口为两者分别固定主机密钥。仿真使用 `shell_type = none` 和 `disable_hashcheck = true`，发布时仍由 worker 核验 SHA-256。添加以下逻辑目录后使用已有上传命令。

Configure two SFTP aliases in the dedicated client config with the home's address, client key and independently verified `known_hosts_file`. Use port 2022 for `stage` and 2023 for `view`. Pin the host key for each address and port. The simulation uses `shell_type = none` and `disable_hashcheck = true`. The worker still verifies the payload SHA-256. Add this logical root and run the existing uploader:

```ini
[drive]
type = combine
upstreams = incoming=stage: files=view:files receipts=view:receipts
```

```sh
python3 scripts/drive_upload.py "$sample" drive: --config "$client_cfg"
rclone --config "$client_cfg" lsf view:files
```

仅需浏览或下载时，文件管理器可直接使用只读入口。 / A file manager can use the read-only export directly for browsing or downloading.

## 验证和撤销 / Verification and rollback

运行 `python3 simulation/run.py --scenario permissions`。Linux 回环仿真自动生成临时密钥，启动两个真实 SFTP 服务，经原上传命令提交合成文件，并通过独立的只读连接尝试新建、覆盖、改名和删除。验证结束时核对原文件和回执内容。Android 应用沙箱、密钥支持和后台运行仍需真机验证。

Run `python3 simulation/run.py --scenario permissions`. The Linux loopback scenario generates ephemeral keys, starts both SFTP servers, publishes synthetic data through the original upload CLI and attempts create, overwrite, rename and delete through the direct read-only connection. It rechecks published bytes and receipt contents. Android app isolation, key support and background operation require separate device evidence.

撤销测试时，先结束上传，再停止两个 SFTP 进程和专用 worker。移除客户端测试别名及专用密钥授权。已发布数据和回执留在原目录；确认不再需要后再移除测试目录。

To undo the test, finish uploads, stop both SFTP processes and the dedicated worker, then remove the test aliases and key authorization. Published data and receipts remain in their original directories until you choose to remove the test root.

[rclone SFTP 服务 / SFTP server](https://rclone.org/commands/rclone_serve_sftp/) · [rclone combine](https://rclone.org/combine/)
