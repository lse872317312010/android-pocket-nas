# 真机验收清单 / Acceptance test matrix (blank until real devices tested)

| ID | 测试 / Test | 通过条件 / Pass criterion | 实测 / Actual | 证据 / Evidence |
|---|---|---|---|---|
| SFTP-01 | 局域网列目录、读取 100 MB 文件 / LAN list/read 100 MB file | 哈希与原文件一致 / Hash matches original | 未测试 / Not tested | 待补 / TBD |
| SFTP-02 | 临时目录上传、重命名和删除 / Upload/rename/delete in temp folder | 操作正确，访问限于授权根目录 / Correct results, restricted root | 未测试 / Not tested | 待补 / TBD |
| SAF-01 | 从 Android 选择器打开文档 / Open document from Android picker | 无需手动预下载 / File opens without manual pre-download | 未测试 / Not tested | 待补 / TBD |
| SAF-02 | 视频随机跳转 / Video random seek | 跳转成功，缓冲时间可接受 / Can seek; reasonable buffering | 未测试 / Not tested | 待补 / TBD |
| SYNC-01 | 相机文件单向接收 / Camera send-only ingestion | 原件到达，未经有损转换 / Original arrives without lossy conversion | 未测试 / Not tested | 待补 / TBD |
| SYNC-02 | 离线访问热文件 / Offline hot file | 断网时可打开 / Open while disconnected | 未测试 / Not tested | 待补 / TBD |
| SAFE-01 | 误删后恢复 / Accidental deletion and recovery | 能从独立保留的副本还原 / Restore independently retained copy | 未测试 / Not tested | 待补 / TBD |
| WAN-01 | 移动网络私有访问 / Private mobile data access | 家庭端连接 Wi-Fi，无需端口映射 / Works with home Wi-Fi and no port forward | 未测试 / Not tested | 待补 / TBD |
| WAN-02 | 主力机切移动数据，断开 Tailscale 再刷新 / Drop the VPN on mobile data, then refresh | 新请求失败，重新连接后可恢复。测试传输时断线，核对家庭机上的文件回执 / Requests fail while offline and recover over VPN. Check upload outcome separately. | 未测试 / Not tested | 待补 / TBD |
| WAN-03 | 家庭机重启后从外网重试 / Reconnect remotely after a home reboot | 若调试公钥改变，应用拒绝连接，回家重新输入配对码后恢复 / A changed debugging key blocks the session until trusted Wi-Fi pairing is repeated. | 未测试 / Not tested | 待补 / TBD |
| VPN-01 | 与 Clash 共存 / Clash coexistence | 记录已成功验证且受支持的配置 / Document successful supported configuration | 未测试 / Not tested | 待补 / TBD |
| REL-01 | 息屏 24 小时 / Screen off 24 hours | 全程可访问 / Service accessible throughout | 未测试 / Not tested | 待补 / TBD |
| REL-02 | 连续运行 72 小时 / 72-hour continuous operation | 记录故障及恢复过程 / Failures and recovery recorded | 未测试 / Not tested | 待补 / TBD |
| REL-03 | 重启或 Wi-Fi 中断 / Reboot / Wi-Fi interruption | 测得恢复服务的耗时 / Service recovers within measured time | 未测试 / Not tested | 待补 / TBD |
| SCR-01 | 局域网黑屏触控 / LAN screen control | 主力机可启停秒表，家庭机面板保持黑屏 / Operate stopwatch with home panel dark | 未测试 / Not tested | 待补 / TBD |
| SCR-02 | 黑屏连续会话 24 h / 24 h continuous mirror | 全程保持连接，起止时均可触控，记录掉线和亮屏事件 / Session survives with working input at start and end. Record drops and panel wakeups. | 未测试 / Not tested | 待补 / TBD |
| SCR-03 | 退出后闲置 24 h 再跨网连接 / 24 h idle then mobile reconnect | 断开时面板灭，文件仍可读，从移动网重连并操作，无闪屏或现场确认 / Dark panel on exit, SFTP readable and mobile control resumes without a panel flash or local approval | 未测试 / Not tested | 待补 / TBD |
| SCR-04 | Wi-Fi 中断、重启分别测试 / Separate Wi-Fi loss and reboot drills | 分别记录端口变化、亮屏、现场解锁和恢复时间；仅两种情况都无需现场操作才算无人恢复 / Record port changes, flashes, local unlock and recovery times for each. Unattended recovery requires both to succeed without local input. | 未测试 / Not tested | 待补 / TBD |
| SAFETY-01 | 充电与温控 / Charge/thermal safety | 无异常发热，记录保护配置 / No abnormal heat; protections documented | 未测试 / Not tested | 待补 / TBD |

记录机型、系统、应用版本、网络条件、命令、截图或日志路径、实测指标和测试备注。仅填写实际观察到的结果。

Record: device/OS, exact application version, network conditions, commands, screenshots/log paths, observed metrics and tester notes. Never invent successful test outcomes.
