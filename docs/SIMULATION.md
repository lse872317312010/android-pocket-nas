# 双手机软件仿真 / Two-phone software simulation

家庭端代表 1 TB 存储机，主力端代表 256 GB 客户端。Ubuntu 在回环网络上运行真实服务进程，每次运行使用临时目录、临时身份和合成文件。两个场景独立运行，无需手机或家庭账户。

The home role represents the 1 TB storage phone and the primary role the 256 GB client. Ubuntu runs real services on loopback with disposable directories, identities and synthetic files. The two scenarios run independently without phones or household accounts.

| 场景 / Scenario | 操作与判据 / Operations and pass criteria |
|---|---|
| access | rclone 经 SSH 密钥认证连接 OpenSSH，核对主机密钥、目录内容及四处读取的数据，覆盖前跳、回跳与文件末尾。 / rclone uses authenticated SFTP with a pinned host key. The listing must include the fixture and four reads must match the reference bytes, including forward, backward and end-of-file reads. |
| sync | 两个 Syncthing 实例同步相机样本与热文件。家庭端停止时读热文件；重启后观察源端误删传播，再从同步目录外的副本恢复并核对内容。 / Two Syncthing instances transfer a camera sample and a hot document. Read the cached document while home is stopped, reconnect after source deletion, observe deletion propagation, then restore and verify the independent copy. |

## 运行 / Run

Ubuntu 24.04，普通用户运行测试，安装依赖需要管理员权限。 / Run the tests as an ordinary user on Ubuntu 24.04. Package installation requires administrator privileges.

```bash
sudo apt-get update
sudo apt-get install -y openssh-client openssh-server rclone syncthing python3
sudo install -d -m 0755 /run/sshd
python3 simulation/run.py --report simulation-report.json
```

单独运行一个场景可加 `--scenario access` 或 `--scenario sync`。报告记录各场景的结果、退出码和耗时，任何场景失败都会使总命令返回非零。GitHub Actions 上传 JSON 报告，日志提供具体断言结果。 / Select a scenario with `--scenario access` or `--scenario sync`. The JSON report records results, exit codes and elapsed time. Any failed scenario makes the command exit nonzero. Actions uploads the JSON; the job log contains individual checks.

## 验证范围 / Coverage

字节范围读取用于验证寻址正确性。播放器解码、实际网络流量、SAF 应用兼容性、Android 存储隔离、跨公网 VPN、后台保活和温控需要独立测试。同机独立目录可演练恢复流程，实际备份还需位于独立故障域。

Range reads verify addressing. Decoder behavior, wire traffic, SAF compatibility, Android storage isolation, WAN VPN, background operation and thermal behavior require separate tests. The recovery drill uses a separate local directory; production backups need an independent failure domain.
