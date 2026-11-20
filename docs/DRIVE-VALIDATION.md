# 网盘组件实测 / File drive component results

运行 / Run: `python3 scripts/sim-access.py` (Linux, OpenSSH, rclone).

Debian 本地回环实测 rclone v1.60.1-DEV、OpenSSH 10.0p2。服务端启用 internal-sftp，客户端固定主机密钥，关闭远端 shell 哈希。 / Local Debian loopback, rclone v1.60.1-DEV and OpenSSH 10.0p2, internal-sftp, pinned host key and no remote shell hashing.

| 测试 / Test | 观察 / Observation |
|---|---|
| 合成 APK 下载、ZIP 上传 / Synthetic APK download and ZIP upload | 字节一致；未测试安装 / Bytes matched; installation untested |
| 同名、同大小、同修改时间、不同内容 / Same path, size and mtime, distinct bytes | 默认复制跳过，远端仍为旧内容 / Default copy skipped the change |
| 同名、不同大小 / Same path, different size | 默认复制覆盖；ignore-existing 跳过 / Default copy overwrote; ignore-existing skipped |
| 暂存文件少 11 字节 / Staging payload truncated by 11 bytes | 测试程序校验失败并清理暂存，原文件完整 / Harness verification rejected staging and preserved original |

结论：当前配置默认行为不足以实现按内容判重和自动保留两份。后续先评估已有客户端或配置，验证显式替换时的真实断网、写满和并发冲突。 / This configuration alone does not provide content-based collision handling and automatic keep-both. Evaluate existing client options and test real interruption, full storage and concurrent commits before selecting a solution.
