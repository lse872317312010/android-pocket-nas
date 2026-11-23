# 家庭机黑屏远控 / Home phone screen control

## 一键测试版 / One-APK test build

**256 GB 主力机**安装 `pocket-nas-home.apk`，打开「家庭机」。**1 TB 家庭机**与主力机连同一 Wi-Fi，在「开发者选项 → 无线调试 → 使用配对码配对设备」显示六位码。主力机点选家庭机并输入该码，之后应用记住设备、发现连接端口并载入远控设置。新版使用独立包名 `io.github.pocketnas.home`，可与旧测试版共存，首次需单独配对。

| 主力机首页 | 如何验证 |
|---|---|
| 刷新存储空间 | 显示家庭机共享存储的可用和总容量。断开家庭机网络后刷新，应显示读取失败。 |
| 发送文件到家庭机 | 选一份小文档或照片，完成时看实际目标路径。家庭机文件管理器打开内部存储的 Download。再发一次，检查两个副本。每次选一个文件，上限 512 MiB。上传期间保持此页打开。 |
| 打开家庭机屏幕 | 在家庭机打开秒表，主力机点启动与暂停，同时观察现场面板。 |

文件上传复用已配对的无线调试连接及客户端的文件传输实现，可以独立于投屏运行。完整远程目录浏览继续使用现有 SFTP 方案。文件页显示的完成表示家庭机已应答。若在最后一步断网，先检查 Download 再重试。应用记录最近一次传输的结果，供再次打开时核对。24 小时运行、实体屏幕与这两台手机的兼容性待实测。

**异地测试**复用两机已连接的 Tailscale。将家中节点在 tailnet 中命名为 `pocket-nas` 并启用 MagicDNS。应用用名称和上次局域网发现的连接端口访问。无线调试重启后端口可能改变，此时需要回到家庭 Wi-Fi 刷新。

Install `pocket-nas-home.apk` on the 256 GB controller. On trusted home Wi-Fi, open Wireless debugging → Pair device with pairing code on the home phone. Select the home phone and enter the six digits on the controller. This build has its own identity and can coexist with the earlier screen-only build. Its home page shows shared-storage capacity and offers an Android document picker for one upload of up to 512 MiB. Leave the page open during the transfer. Repeat with the same file, check both names in the remote Download folder, and check that loss of network produces an error. If the acknowledgement was lost, inspect Download before retrying. Open screen control separately to exercise the stopwatch test. Remote directory browsing remains available through the project's SFTP setup. Cellular access uses an existing Tailscale network, home peer name `pocket-nas`, MagicDNS and the last known debugging port.

Build with JDK 17 and the upstream Android SDK using `bash controller/build.sh`. The script runs the storage parser and upstream transfer unit tests before assembling the APK.

## 两台手机怎么配（原版客户端）

Android Pocket NAS 用 Scrcpy Android 的设备配置启动可选的整屏远控服务。家庭机继续提供 SFTP，主力机按需串流画面和触控。需要家庭机 Android 11+ 的无线调试功能。第一次配对时两台手机都在同一个可信 Wi-Fi 上。

1. **1 TB 家庭机**接上充电器，在开发者选项中打开「无线调试」，点「使用配对码配对设备」。如果小米设备连接后能看不能点，按 scrcpy 的小米说明检查「USB 调试（安全设置）」。
2. **256 GB 主力机**安装[上游 v3.5.7 通用 APK](https://github.com/dhun2666/scrcpy-client-for-android/releases/download/v3.5.7/scrcpy-client-for-android-v3.5.7-universal.apk)。只需在主力机安装这个客户端。打开后点 **Pair new device**，输入家庭机显示的 IP、配对端口和六位码。完成后记下家庭机无线调试**主页面**的连接端口。
3. 在主力机上下载[设备配置 JSON](../profiles/screen-control.json)（GitHub 文件页可点 Download raw file）。打开 **Profile tools → Restore profiles** 导入，保留默认的合并选项。确认预览中新增一台设备并点 **Import selected changes**。编辑新增的 **Pocket NAS · Screen**，把示例地址和端口换成家庭机的 Wi-Fi IP 和实际连接端口。首次接通后用 **Add to home screen** 把它放到桌面。
4. 首次从桌面连接，打开家庭机的秒表。在主力机上启动、暂停，同时现场观察家庭机面板。配置选择主显示屏，开启连接时关闭物理屏幕、充电时保持唤醒和断开时关屏。实际锁屏认证仍由系统处理。
5. **出门使用**前先在两机上连接已有 Tailscale 私网。在客户端用 **Duplicate device** 复制已配置的设备，改名、把主机改为家庭机的 tailnet 地址，填写当前无线调试连接端口。将主力机切到移动数据独立验证。若文件可访问但画面连不上，检查无线调试开关、当前端口和私网访问规则。端口可能在无线调试重启后变化，局域网自动发现也可能无法跨私网使用。保持路由器的公网 ADB 端口映射关闭。
6. 平时可以退出投屏，只保留所需的文件服务。要撤销远控，在家庭机的无线调试中忘记该主力机并关闭无线调试。

**全天候验收**请执行 [SCR-01 至 SCR-04](../checklists/ACCEPTANCE.md)。关面板和保持唤醒是会话设置。正常断开、异常掉线、重连和重启需要分别测试，特别是连接瞬间是否闪屏、是否需要家庭机现场解锁。记录手机与系统版本、客户端版本、断线时长及现场确认情况。当前没有这两台手机的实测结果。

## Two-phone setup

The optional screen service uses the Scrcpy Android client's native device profile. SFTP can run independently while screen and touch streaming starts on demand. Pair on trusted home Wi-Fi with Android 11+ Wireless debugging on the home phone.

1. Plug the **1 TB home phone** into its charger. Open Developer options → Wireless debugging → Pair device with pairing code. If touch fails on a Xiaomi device, check the additional security debugging setting in the scrcpy device prerequisites.
2. Install the [upstream v3.5.7 universal APK](https://github.com/dhun2666/scrcpy-client-for-android/releases/download/v3.5.7/scrcpy-client-for-android-v3.5.7-universal.apk) on the **256 GB controller** only. Open **Pair new device** and enter the pairing IP, port and six-digit code. After pairing, read the connection port from the main Wireless debugging screen.
3. Download the profile JSON linked above using **Download raw file**, then use **Profile tools → Restore profiles** with the default merge options. Confirm one new device in the preview and tap **Import selected changes**. Edit **Pocket NAS · Screen**, replace the example host and port with the home Wi-Fi IP and current connection port, and choose **Add to home screen**.
4. Connect and operate a stopwatch while watching the physical panel. The profile mirrors the main display, blanks the panel during control, keeps the phone awake while charging and requests screen-off on disconnect. Android still enforces lock-screen authentication.
5. For away access, connect both devices to the existing Tailscale network. Duplicate the working profile, rename it, set the home's tailnet address and current connection port, then test over mobile data. If SFTP works but control fails, check the debugging listener, port and tailnet access rules. The port can rotate and LAN discovery may be unavailable across the VPN. Keep public ADB port forwarding disabled.
6. End mirroring when idle. To revoke control, forget the paired controller on the home phone and turn off Wireless debugging.

Run SCR-01 through SCR-04 in the acceptance matrix. Record versions, outage duration, physical flashes and any local confirmation after normal disconnect, network loss, reconnect and reboot. Continuous streaming and reconnecting after 24 idle hours require separate observations. Both await hardware testing.

## 连接故障与恢复 / Troubleshooting

| 观察 / Observation | 操作 / Action |
|---|---|
| 局域网首次配对成功，连接超时 / Paired on Wi-Fi but connection times out | 设备配置中填无线调试主页面的连接端口。配对弹窗的端口只用于交换密钥。 / Use the connection port from the main Wireless debugging page in the profile. The pairing dialog port is for key exchange. |
| 移动网络上 SFTP 也不通 / SFTP is also unreachable on mobile data | 先在主力机确认 Tailscale 在线且家庭机在设备列表中可达，再重试文件服务。 / Check the mobile VPN and home peer reachability before retrying SFTP. |
| SFTP 可用，远控超时 / SFTP works but screen control times out | 在外可检查已保存的目标和私网规则；如果家庭机无线调试已关闭或端口已变且无法从可信渠道获知，需回家在系统设置里确认。 / Check the saved endpoint and tailnet rules remotely. If debugging stopped or its new port is unknown, check the home phone locally. |
| 连上时家中面板短暂亮起 / The panel flashes on connect | 3.5.7 在控制通道建立后才发送关屏指令，服务启动默认允许唤醒。记录闪屏；对“全程不亮”的要求，此项判失败。 / The client sends display-off after the control stream opens and uses the server's default power-on behavior at startup. Count a flash as a failure for the always-dark requirement. |

### 已核对的安装包 / Verified download

上游发布 APK 的包名为 `com.scrcpy.remote`，版本为 `3.5.7 (86)`。下载文件 SHA-256 与上游校验文件一致。APK 通过 Android 签名校验，证书指纹与上游公布的 `localRelease` 侧载签名一致。 / The upstream APK identifies as `com.scrcpy.remote`, version `3.5.7 (86)`. Its SHA-256 matches the release checksum. Android signature verification succeeds with the fingerprint published for the upstream `localRelease` sideload key. [Release and checksum](https://github.com/dhun2666/scrcpy-client-for-android/releases/tag/v3.5.7)

```text
99fc33261daa876eec25b6e5cb8b91252cd560a6b3006ab38ed066969359d19c
```

### 复查配置导入 / Reproduce the import test

已在 JVM 上运行 v3.5.7 的原生配置解码与导入合并：首次导入和编辑地址后重复导入共两项通过。Android 界面导入、面板与网络行为待真机验收。

在本仓库根目录下执行。需要上游构建所用的 JDK、Android SDK 36 和 Gradle 依赖。该测试调用发行版本身的解码器与合并逻辑。 / Both JVM tests passed against the v3.5.7 decoder and import planner. Android UI import, physical panel and network behavior await device testing. Run from this repository root with the upstream Android SDK 36, JDK and Gradle prerequisites. The tests call the release's decoder and merge planner.

```bash
client_dir=$(mktemp -d)
git clone --quiet --branch v3.5.7 --depth 1 https://github.com/dhun2666/scrcpy-client-for-android.git "$client_dir"
test "$(git -C "$client_dir" rev-parse HEAD)" = 889bae6a92172f4fb8fa19ca173e330ef64e2abf || exit 1
install -D tests/screen/PocketNasProfileTest.kt "$client_dir/app/src/test/java/com/scrcpy/remote/PocketNasProfileTest.kt"
install -D profiles/screen-control.json "$client_dir/app/src/test/resources/screen-control.json"
(cd "$client_dir" && bash gradlew :app:testDebugUnitTest --tests com.scrcpy.remote.PocketNasProfileTest)
```

### 上游依据 / Upstream references

- [Scrcpy Android profile format and import behavior, 3.5.7](https://github.com/dhun2666/scrcpy-client-for-android/blob/889bae6a92172f4fb8fa19ca173e330ef64e2abf/app/src/main/java/com/scrcpy/remote/data/ProfileBackup.kt)
- [Wireless debugging pairing and port changes](https://github.com/dhun2666/scrcpy-client-for-android/blob/889bae6a92172f4fb8fa19ca173e330ef64e2abf/README.md)
- [Display power and session cleanup](https://github.com/Genymobile/scrcpy/blob/master/doc/device.md)
- [Xiaomi input prerequisites](https://github.com/Genymobile/scrcpy#prerequisites)
