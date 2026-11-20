# 普通网盘可靠上传 / Reliable file-drive uploads

家庭机集中处理文件发布。主力机可以按需下载任意二进制文件，或通过已有客户端把文件传到临时位置。首个里程碑要求同名同内容跳过、不同内容保留两份，显式替换在验证新文件后生效。

The home node controls publication. The primary downloads selected binary files or transfers uploads to staging with an existing client. This milestone requires skipping identical content, keeping both distinct colliding files and publishing explicit replacements only after verification.

## 已有工具评估 / Existing tools

| 组件与测试 / Candidate and test | 观察结果 / Observed result |
|---|---|
| rclone + OpenSSH SFTP | 已跑通文件列表、ZIP 上传和 APK 形态样本下载。默认比较可能跳过相同大小和时间戳的不同内容；详情见[传输实测](DRIVE-VALIDATION.md)。 / Listing, ZIP upload and APK-shaped fixture download worked. Default comparison can skip different content with equal size and timestamps; see the linked transport tests. |
| rclone copyto --checksum --suffix .previous | Debian 上的本地后端探针连续传入两个不同版本。指定路径变为最新内容，固定后缀保存前一个版本；第二次更改替换了第一次的备份。 / Two local-backend writes changed the destination to the incoming version; the second write reused the fixed suffix and displaced the first backup. |
| GNU cp --backup=numbered | 同一份内容再次复制仍生成编号备份，旧内容采用备份文件名。 / Recopying identical bytes still created a numbered backup; the old destination took a backup name. |

本地选项探针使用 rclone v1.60.1-DEV 和 GNU coreutils 9.7。命令行选项可能因版本、后端和可用哈希而有不同表现。运行同一组用例再选 Android 组件。

The local option probes used rclone v1.60.1-DEV and GNU coreutils 9.7. Option behavior depends on version, backend and available hashes. Repeat these cases on the candidate Android backend before selection.

## 实现边界与验收 / Implementation boundary and acceptance

保留 SFTP、rclone、OpenSSH 和现有文件系统。用小型家庭端提交程序处理单次已暂存文件的校验、同名决策与发布；生产使用还需要将完成上传的客户端操作接到该入口。临时写入中断后不得向客户端宣告完成。最终文件名只在校验成功后出现。发布和重试时，使用新文件的校验值核对内容。

Reuse SFTP, rclone, OpenSSH and the existing filesystem. A small home-side commit operation verifies a single staged upload, resolves the target name and publishes it. Production integration must invoke this operation after upload. An interrupted transfer must never generate a success receipt or expose a partial file at the final path. Check the expected digest during publication and retries.

| 验收场景 / Scenario | 判据 / Expected outcome |
|---|---|
| 相同内容重复提交 / Retry identical content | 保留一份 / One published copy |
| 同名异内容及并发写入 / Collision and concurrent writers | 原文件完整；不同内容各有独立名称 / Original intact and each distinct payload available |
| 显式替换、暂存损坏、中断和空间不足 / Replace, corruption, interruption and full storage | 验证成功才替换；发布前的失败保留旧版本 / Replacement only after verification; pre-publication failure preserves the old version |

Android 存储提供器的锁、重命名和持久性语义以及实际应用界面需要真机验证。 / Locking, rename and durability behavior on Android storage providers and the user-facing flow require device validation.

## 复现 / Reproduce

```sh
python3 simulation/run.py --scenario drive
python3 simulation/run.py --scenario access
```

在家机端运行以下命令。SHA256 使用发送端在上传前计算的值。命令成功时输出实际发布路径。 / Run on the home device with the digest calculated by the sender before uploading. Success prints the published path.

```sh
python3 scripts/drive_commit.py "$staged" "$destination" "$sha256"
```

仿真假设可信本地路径和协作写入的进程。暂存件保留，提交需要目标卷上的额外空间。进程被强制终止时可能留下隐藏临时文件。 / The simulation assumes trusted local paths and cooperating writers. The staged upload is retained and commit needs extra space on the destination volume. Killing the process can leave a hidden temporary file.
