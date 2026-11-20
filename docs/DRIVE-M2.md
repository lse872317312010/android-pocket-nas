# 网盘 M2：从上传到回执 / Drive M2: upload through receipt

**交付边界 / Deliverable.** 用真实 SFTP 将单个普通文件从主力端上传到家庭端，家庭端校验、处理重名并发布，客户端得到结果。初版以命令行复现；文件管理器能否把上传动作直接交给该流程是单独的集成项。

Send one ordinary file from the primary to the home over real SFTP. The home verifies and publishes it with collision handling, then the client receives the result. The CLI provides the reproducible entry point. A file manager's ability to initiate this workflow requires separate integration testing.

| 职责 / Role | 入口 / Entry point |
|---|---|
| 家庭端 / Home | `python3 scripts/drive_inbox.py ROOT`。提供家庭端可访问的专用测试根目录。 / Supply a dedicated test root writable by the home process. |
| 主力端或替身 / Primary or desktop stand-in | `python3 scripts/drive_upload.py SOURCE REMOTE_ROOT --config PATH`。REMOTE_ROOT 采用已配置的 rclone SFTP 远端路径，映射同一个测试根目录。 / Use the configured rclone SFTP path to the same test root. |
| 数据传输 / Transport | OpenSSH SFTP + rclone；身份、端口、监听与可信主机密钥按实际测试环境配置。 / Configure credentials, port, listener and verified host key for the actual test deployment. |
| 发布 / Publication | 家庭端复用 M1 提交程序；目标文件系统、进程权限与锁协作必须实测。 / Home reuses the M1 publisher. Verify filesystem capabilities, process permissions and lock cooperation. |

## 开发与验收约定 / Development agreement

优先配置已有软件，出现可复现缺口才写薄适配；仿真测试、故障复现和可修复失败持续推进，Android 用户交互留到目标系统验收。Linux CI 结果、电脑到家庭机、两部 Android 手机三类证据分别记录。待真机验证的项目单独记录；同时继续所有可独立推进的软件工作。仅当这些工作全部完成，且下一步确实依赖真机反馈时才暂停，并写明需要哪台设备、哪项操作和哪条观测结果。

Configure existing components first and write small adapters for reproducible gaps. Continue simulation, fault testing and recovery of fixable failures. Validate Android interactions on the target platform. Record Linux CI, desktop-to-home and Android-to-Android evidence separately. Track pending device checks while continuing every independent software task. Pause only after those tasks are exhausted and further progress requires physical-device feedback. Record the device, action and observation needed to resume.

**通过条件 / Pass conditions.** 输入和发布内容的 SHA-256 相同；相同内容重试返回同一目标，异内容冲突不覆盖原件。只有经过家庭端确认才显示发布成功。中断、重复请求及客户端超时不应破坏原文件。无回执时将结果记录为未确认，检查家庭端状态后再判定。

Input and published SHA-256 values match. Identical-content retries return the same target and distinct collisions preserve the original. Success requires home-side confirmation. Interruptions, repeats and client timeouts must preserve the original. Record missing receipts as unconfirmed and reconcile against home state.

## 真机阻塞和证据 / Device dependencies and evidence

查看[首次真机清单](../checklists/DRIVE-M2-DEVICE.md)。需要能运行提交进程的家庭端、SFTP 服务与提交进程共同可访问的目录、以及该目录对锁/硬链接/fsync/重命名的支持。仅能通过 URI 访问的存储需要原生接口适配或改用通过探针的目录。原生文件管理器或 SAF 的兼容性、后台与机型性能分别以实测为准。使用用户数据之前先在专用目录验证。

Use the [first-device checklist](../checklists/DRIVE-M2-DEVICE.md). The home must run the publisher and expose a directory shared with the SFTP service whose lock, hard-link, fsync and rename behavior passes the probe. URI-only storage requires an adapter or a tested alternative directory. Qualify native file manager/SAF, background behavior and device performance independently. Use a dedicated directory for first-device validation.

## 超时后查询原回执 / Recover a lost acknowledgement

保留首次上传在标准错误输出中打印的 32 位编号，以及名称和内容均未改变的源文件。在原客户端使用相同的远端根目录和配置运行以下命令。查询只读取该编号的回执，复用原上传的 SHA-256 和目标名校验。成功时输出家庭端实际文件名，包括重名时的编号。

Keep the 32-character ID printed to stderr during the original upload and the source file with its original name and contents. On the original client, use the same remote root and config. This read-only lookup verifies the receipt against the source digest and allowed destination names, then prints the published name on success.

```sh
python3 scripts/drive_upload.py "$source" "$remote" --config "$cfg" --check-attempt "$id" --timeout 30
```

家庭端仍在处理时可以稍后用同一编号再查。超时表示发布状态仍未确认。若客户端在请求提交前断开，家庭端可能永远不会生成该回执。收到拒绝回执或源文件不匹配时，命令以非零状态退出。查询验证的是当时的发布记录；要核实当前远端内容，可下载并校验。

If the home worker is still processing, repeat the lookup later with the same ID. A timeout leaves publication unconfirmed. An interruption before request submission can leave the attempt without a receipt indefinitely. A rejection receipt or source mismatch exits nonzero. The receipt records publication at the time of upload. Download and hash the remote object to verify its current contents.

### 提交前中断与空间回收 / Interrupted staging and space recovery

客户端为每次普通上传创建独立编号。若载荷或临时请求的复制在提交前报错或被 Ctrl-C 中断，客户端等待传输子进程退出，用 rclone 尝试清除本次编号的暂存目录。清理最多额外等待 5 秒，客户端保留最初的失败结果。其他编号、已发布文件和回执保持原状。

Each normal upload owns a fresh attempt ID. If copying the payload or temporary request fails or is interrupted by Ctrl-C before submission, the client waits for the transfer subprocess to exit, then uses rclone to reclaim that attempt's staging directory. This best-effort step allows up to five extra seconds and preserves the original failure. Other attempts, published files and receipts remain available.

一旦开始将临时请求重命名为 `request.json`，家庭端就可能已经接受提交。此后若断线，保留编号，按上文查询原回执。若进程被强杀或家庭端一直离线，暂存文件可能留存。仅凭目录的年龄、大小或缺少提交标记无法认定上传已停止。

Once the rename to `request.json` begins, home may have accepted the request even if the reply is lost. Keep the ID and use the receipt lookup above. A killed process or an unreachable home can leave staged data behind. Directory age, size or a missing request marker alone cannot establish that a sender has stopped.

**旧暂存目录的人工恢复 / Manual recovery of older staging.** 如确需回收空间，先停止该测试根的所有上传端、SFTP 写入会话及家庭端 worker，并核对准确的上传编号。已有回执或 `request.json` 的任务交给 worker 恢复。对确认已放弃且两者均不存在的编号，可先将该单个目录移到同卷、收件箱之外的隔离目录。检查后再删除以释放空间。撤销隔离时保持写入停止，将目录移回原编号位置，确认该位置空闲后再操作。恢复服务后用新编号重试上传。

If space is needed, quiesce all uploaders, SFTP write sessions and the home worker for this root and verify the exact attempt ID. Let the worker recover attempts with a receipt or a ready request. For a confirmed abandoned ID with neither, move only its directory to quarantine outside the inbox on the same volume. Inspect it before deleting it to release space. To undo quarantine, keep writers stopped, verify the original location is free and move the directory back. Resume services and use a fresh ID to retry the transfer.
