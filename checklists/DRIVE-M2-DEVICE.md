# 首次网盘真机验收 / First physical-device drive test

所有项目初始为待测。使用合成数据和可信局域网。在发布公开报告前删除私钥、配置文件、家庭 IP、设备标识及账户信息。

All checks start pending. Use synthetic data and a trusted LAN. Redact private keys, configs, home addresses, device identifiers and accounts before publishing evidence.

### 1. 准备测试环境 / Prepare

- [ ] 记录两机型号、系统与应用版本，注明客户端是 Redmi、Ubuntu 或 WSL。选用现有服务：具备 Python、rclone 和 OpenSSH 的 Termux 环境是可测试组合；其他 SFTP 应用需要确认能与提交程序共享目录。 / Record both models, OS and app versions, and the exact client (Redmi, Ubuntu or WSL). A Termux environment with Python, rclone and OpenSSH is a candidate. Other SFTP apps must demonstrate directory access from the publisher.
- [ ] 家庭端选择一个测试父目录。避免 DCIM、下载归档等现有数据目录。以即将运行 worker 的 Android 应用身份执行以下命令，并在每个候选卷重复。 / Pick a test parent away from existing collections such as DCIM. Run under the worker's actual Android app identity. Repeat on each candidate volume.

```sh
# Point this at the chosen existing parent. / 设置为已选的现有父目录。
TEST_PARENT="$HOME"
export DRIVE_TEST_ROOT="$(mktemp -d "$TEST_PARENT/pocket-nas-device.XXXXXX")"
test -d "$DRIVE_TEST_ROOT" || exit 1
printf '%s\n' "$DRIVE_TEST_ROOT"
```

### 2. 实测发布原语 / Probe publication primitives

在同一测试根目录运行。发生异常时记录具体操作、errno、目录类型。此探针检测能力；断电一致性与 Android 后台运行另测。

Run in that same root. On failure record the specific operation, errno and volume type. This probes capabilities; crash durability and Android background operation need separate tests.

```sh
python3 - <<'PY'
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(os.environ["DRIVE_TEST_ROOT"])
with tempfile.TemporaryDirectory(dir=root) as temp:
    p = Path(temp)
    d = os.open(p, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(d, fcntl.LOCK_EX | fcntl.LOCK_NB)
        child = """
import fcntl, os, sys
fd = os.open(sys.argv[1], os.O_RDONLY | os.O_DIRECTORY)
try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(0)
sys.exit(1)
"""
        subprocess.run([sys.executable, "-c", child, str(p)], check=True)
        print("PASS directory flock excludes another process")
        src, dst = p / "new", p / "published"
        with src.open("wb") as f:
            f.write(b"verified fixture")
            f.flush()
            os.fsync(f.fileno())
        print("PASS file fsync")
        os.link(src, dst)
        assert src.samefile(dst)
        print("PASS same-directory hard link")
        other = p / "replacement"
        other.write_bytes(b"next")
        os.replace(other, dst)
        assert dst.read_bytes() == b"next" and src.read_bytes() == b"verified fixture"
        print("PASS same-directory replacing rename")
        os.fsync(d)
        print("PASS directory fsync")
    finally:
        os.close(d)
PY
```

- [ ] 任一操作失败：先在候选应用自己的私有 POSIX 目录复测；服务和 worker 同时能访问该目录方可继续。报告私有目录和共享目录各自结论。 / If a primitive fails, test an app-private POSIX directory. Continue only where both service and worker can operate. Report private/shared storage outcomes separately.

### 3. 文件系统与远端的同一性 / Verify the remote mapping

- [ ] 在客户端 rclone 配置中为测试 SFTP 服务设置专用别名和已独立核对的服务器主机密钥。客户端只记录测试远端路径；不同应用的路径命名或根目录可能不同。 / Create an rclone SFTP alias with a verified home host key. Determine the client-visible test path; app sandboxing and exported roots may differ.
- [ ] 家庭端在测试根创建标记；客户端列目录并读标记，然后上传一个唯一的小文件；家庭端在相同根确认收到。路径映射不成立时先修复路径或权限。 / Write a marker on home. List and read it remotely, then upload a unique small file and confirm its arrival on home. Resolve any path or permission discrepancy first.

```sh
# Home / 家庭端
printf 'pocket-nas device probe\n' > "$DRIVE_TEST_ROOT/device-marker.txt"
# Client / 客户端：set cfg and remote to actual config and remote path
rclone --config "$cfg" lsf "$remote"
rclone --config "$cfg" cat "$remote/device-marker.txt"
```

### 4. 网盘提交 / Publish through the drive workflow

- [ ] 在仓库根分别运行 `python3 scripts/drive_inbox.py --help` 和 `python3 scripts/drive_upload.py --help` 确认当前选项。家庭机运行 `python3 scripts/drive_inbox.py "$DRIVE_TEST_ROOT"`。客户端执行以下命令，记录回执的目标名及状态。若使用电脑客户端，只标记电脑到 Android 测试。 / Check current CLI options with both scripts' --help commands from the repository root. Run the home worker as shown and execute the following on the client. Record target names and results. Desktop clients qualify only the desktop-to-Android path.
- [ ] 同一份 ZIP 连续上传两次；修改内容但保留文件名后再次上传，家庭端核对旧、新两份的 SHA-256。 / Upload the ZIP twice, change the content while keeping the name and repeat. Verify both the original and changed SHA-256 values on home.

```sh
client_tmp="$(mktemp -d)"
python3 -m zipfile -c "$client_tmp/sample.zip" README.md
sha256sum "$client_tmp/sample.zip"
python3 scripts/drive_upload.py "$client_tmp/sample.zip" "$remote" --config "$cfg"
python3 scripts/drive_upload.py "$client_tmp/sample.zip" "$remote" --config "$cfg"
python3 -m zipfile -c "$client_tmp/sample.zip" docs/ROADMAP.md
sha256sum "$client_tmp/sample.zip"
python3 scripts/drive_upload.py "$client_tmp/sample.zip" "$remote" --config "$cfg"
```

### 5. Redmi 原生入口与按需下载 / Redmi on-demand download

- [ ] 在 Redmi 已有文件管理器里找网络/SFTP 连接功能。若当前版本没有可用入口，尝试已配置的 RSAF SFTP 文档提供器并从系统文件选择器进入。记录成功入口、应用名及版本；未呈现入口时记录实际观察。 / Check the installed file manager for an SFTP connection. If unavailable, test a configured RSAF SFTP document provider through the system picker. Record the actual entry point, app and version, including unavailable paths.
- [ ] 先浏览家庭机已发布文件目录，记录本机下载目录和可用空间；只选择测试 ZIP 下载到新的本机测试目录。核对 ZIP 可打开、离线可读取、本机与家庭机 SHA-256 相同，再仅删除下载副本；重连后家庭端文件仍在。同样流程可用于合成 APK 形态样本，安装不在本项范围。 / Record local download directory contents and free space, browse the published directory, then download only the selected ZIP into a fresh local directory. Open it offline, verify its SHA-256 against home, delete the downloaded copy, and reconnect to confirm home still retains it. Repeat with a synthetic APK-shaped file if desired; installation is outside this check.
- [ ] 记录普通浏览是否触发额外下载、下载进度及取消行为。没有流量计数时，只报告可见副本和观测结果，不据此断言网络字节数。确认正式目录在客户端只读，普通文件管理器不能绕过提交覆盖正式原件；当前测试账号若有更宽权限，将其登记为部署缺口。 / Record extra downloads, progress and cancellation. Without traffic measurements, report visible copies and observations only. Check the final published directory is read-only to the client. If test credentials allow direct overwrites, record that deployment gap.

测试完成后停止专用服务并仅清理新建的测试目录。 / Stop the dedicated services and remove only the newly created test directories.
