# 家庭机黑屏远控 / Home phone screen control

## 两台手机怎么配

Android Pocket NAS 用 Scrcpy Android 的设备配置启动可选的整屏远控服务。家庭机继续提供 SFTP，主力机按需串流画面和触控。需要家庭机 Android 11+ 的无线调试功能。第一次配对时两台手机都在同一个可信 Wi-Fi 上。

1. **1 TB 家庭机**接上充电器，在开发者选项中打开「无线调试」，点「使用配对码配对设备」。如果小米设备连接后能看不能点，按 scrcpy 的小米说明检查「USB 调试（安全设置）」。
2. **256 GB 主力机**使用 [Scrcpy Android](https://github.com/dhun2666/scrcpy-client-for-android)，点 **Pair new device**，输入家庭机显示的 IP、配对端口和六位码。完成后记下家庭机无线调试**主页面**的连接端口。
3. 在主力机上下载[设备配置 JSON](../profiles/screen-control.json)（GitHub 文件页可点 Download raw file）。打开 **Profile tools → Restore profiles** 导入，保留默认的合并选项。编辑新增的 **Pocket NAS · Screen**，把示例地址和端口换成家庭机的 Wi-Fi IP 和实际连接端口。用 **Add to home screen** 把它放到桌面。
4. 首次从桌面连接，打开家庭机的秒表。在主力机上启动、暂停，同时现场观察家庭机面板。配置选择主显示屏，开启连接时关闭物理屏幕、充电时保持唤醒和断开时关屏。实际锁屏认证仍由系统处理。
5. **出门使用**前先在两机上连接已有 Tailscale 私网。在客户端用 **Duplicate device** 复制已配置的设备，改名、把主机改为家庭机的 tailnet 地址，填写当前无线调试连接端口。将主力机切到移动数据独立验证。若文件可访问但画面连不上，检查无线调试开关、当前端口和私网访问规则。端口可能在无线调试重启后变化，局域网自动发现也可能无法跨私网使用。保持路由器的公网 ADB 端口映射关闭。
6. 平时可以退出投屏，只保留所需的文件服务。要撤销远控，在家庭机的无线调试中忘记该主力机并关闭无线调试。

**全天候验收**请执行 [SCR-01 至 SCR-04](../checklists/ACCEPTANCE.md)。关面板和保持唤醒是会话设置。正常断开、异常掉线、重连和重启需要分别测试，特别是连接瞬间是否闪屏、是否需要家庭机现场解锁。记录手机与系统版本、客户端版本、断线时长及现场确认情况。当前没有这两台手机的实测结果。

## Two-phone setup

The optional screen service uses the Scrcpy Android client's native device profile. SFTP can run independently while screen and touch streaming starts on demand. Pair on trusted home Wi-Fi with Android 11+ Wireless debugging on the home phone.

1. Plug the **1 TB home phone** into its charger. Open Developer options → Wireless debugging → Pair device with pairing code. If touch fails on a Xiaomi device, check the additional security debugging setting in the scrcpy device prerequisites.
2. On the **256 GB controller**, open Scrcpy Android → **Pair new device** and enter the pairing IP, port and six-digit code. After pairing, read the connection port from the main Wireless debugging screen.
3. Download the profile JSON linked above using **Download raw file**, then use **Profile tools → Restore profiles** with the default merge options. Edit **Pocket NAS · Screen**, replace the example host and port with the home Wi-Fi IP and current connection port, and choose **Add to home screen**.
4. Connect and operate a stopwatch while watching the physical panel. The profile mirrors the main display, blanks the panel during control, keeps the phone awake while charging and requests screen-off on disconnect. Android still enforces lock-screen authentication.
5. For away access, connect both devices to the existing Tailscale network. Duplicate the working profile, rename it, set the home's tailnet address and current connection port, then test over mobile data. If SFTP works but control fails, check the debugging listener, port and tailnet access rules. The port can rotate and LAN discovery may be unavailable across the VPN. Keep public ADB port forwarding disabled.
6. End mirroring when idle. To revoke control, forget the paired controller on the home phone and turn off Wireless debugging.

Run SCR-01 through SCR-04 in the acceptance matrix. Record versions, outage duration, physical flashes and any local confirmation after normal disconnect, network loss, reconnect and reboot. Continuous streaming and reconnecting after 24 idle hours require separate observations. Both await hardware testing.

### 上游依据 / Upstream references

- [Scrcpy Android profile format and import behavior, 3.5.7](https://github.com/dhun2666/scrcpy-client-for-android/blob/48886d9a633179a64c0c10cc95b9df1bac046efa/app/src/main/java/com/scrcpy/remote/data/ProfileBackup.kt)
- [Wireless debugging pairing and port changes](https://github.com/dhun2666/scrcpy-client-for-android/blob/48886d9a633179a64c0c10cc95b9df1bac046efa/README.md)
- [Display power and session cleanup](https://github.com/Genymobile/scrcpy/blob/master/doc/device.md)
- [Xiaomi input prerequisites](https://github.com/Genymobile/scrcpy#prerequisites)
