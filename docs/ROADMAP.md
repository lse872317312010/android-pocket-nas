# 首版交付路线图 / First release roadmap

## 已确认的范围 / Agreed scope

单人使用两部手机。1 TB 家庭机保存原件，256 GB 主力机浏览统一媒体时间线并按需使用网盘。可在家庭端另行配置云备份。首版允许家庭机保存唯一原件。默认无 Root，文档中英双语。优先复用已有传输与访问组件。Personal OS 接入按后续需求独立评估。

One owner uses a 1 TB home phone for originals and a 256 GB primary phone for the media timeline and personal file drive. Cloud backup is an optional future home-side decision. A verified home copy may become the only original. Assume unrooted devices, maintain bilingual documentation and reuse existing transport and access components. Revisit Personal OS integration only for a concrete later workflow.

## 起点 / Starting point

[双节点回归 / Two-node regression](https://github.com/lse872317312010/android-pocket-nas/actions/runs/44678730104) · [100 MB 往返 / Round trip](https://github.com/lse872317312010/android-pocket-nas/actions/runs/44678730080)

已验证 Linux 回环 SFTP、分段读取、Syncthing 同步及独立目录恢复。同步删除传播的实验说明家庭归档需要独立控制删除。以下是待实现和验收的产品行为。

Linux loopback tests cover SFTP, byte ranges, Syncthing replication and restore from a separate directory. Observed deletion propagation motivates explicit control of archive deletion. The following product milestones await implementation and acceptance.

## 交付顺序 / Delivery sequence

1. **普通文件网盘 / Personal file drive**  
   用已有 SFTP 后端提供列表、指定文件下载、上传到指定目录和手动清理。用 APK、ZIP、无扩展名二进制文件验证两端产生的文件。校验字节内容；同目录同名同内容跳过，不同内容保留两份，明确替换时验证新文件后提交。注入中断、重试、目标写满和同名并发；旧文件完整，本地清理不传播。  
   Use SFTP for listing, selected downloads, uploads and manual cleanup. Exercise APK, ZIP and extensionless fixtures originating on either endpoint. Verify byte equality, skip identical collisions, keep distinct copies and commit explicit replacements only after verification. Test interrupted and concurrent uploads, retry and full storage. Preserve existing files and keep local cleanup local.

2. **媒体归档与时间线 / Media archive and timeline**  
   默认相机目录，可选其他目录。首次导入先展示数量、大小、预计释放量及历史照片移动流量选项，默认 Wi-Fi。日常照片可用流量，视频等待 Wi-Fi。用可控时钟跨越拍摄后 7 天，验证收到并校验后才释放本机原件；保留照片清晰预览、视频封面和拍摄日期。新机拉取完整时间线和小缩略图，按需加载历史清晰预览。  
   Default to the camera directory with opt-in folders. Preview import counts, sizes and reclaimable space; default historical imports to Wi-Fi with a per-import cellular override for photos. New photos may use cellular; videos wait for Wi-Fi. Advance a test clock across day seven and verify local eviction waits for confirmed home integrity. Retain previews, covers and capture dates. New devices load the full timeline and thumbnails, with larger historical previews on demand.

3. **整理、恢复与换机 / Curation, recovery and migration**  
   本机移除立即隐藏，未上传的继续排队；可恢复显示，换机继承隐藏。全局删除明确确认一次，离线可撤销，重试只执行一次。回收站从家庭机实际接收删除起计 30 天，写满时用户选择是否提前清理。相同内容保留来源，编辑保存可还原，另存副本独立管理。当面扫码配对，新机接管，旧机限补传、可立即撤销，校验完成后解绑。验证离线、重启、重放和旧机积压的删除请求。  
   Hide locally immediately, keep pending uploads, allow unhide and carry visibility to the next phone. Confirm global deletion once, support offline cancellation and idempotent retries. Start 30-day retention on home-side trash entry; require a user choice for early purges under storage pressure. Retain duplicate sources, reversible edits and independent saved copies. Pair in person; grant the outgoing device revocable upload-only access until pending files verify. Test offline operation, restart, replay and stale deletions.

4. **播放与分享 / Playback and sharing**  
   先用模拟播放器和分享接收端验收。移动网络每次打开归档视频先确认，退出停止读取。照片默认分享预览，可取当前编辑版全分辨率文件。视频显示大小、网络、可用空间，确认后完整取回。Wi-Fi 中断保留进度，用户可批准剩余流量，否则待 Wi-Fi 续传。接收端读完后视频缓存默认 24 小时，空间不足可提前回收。  
   Test first with simulated playback and share consumers. Confirm each cellular playback session and stop reads on exit. Share photo previews by default, with optional retrieval of the full current edit. Show video size, network and available space before full retrieval. Preserve progress across disconnection and obtain consent to resume over cellular. Cache shared video for 24 hours after the recipient finishes reading, allowing earlier reclaim under pressure.

5. **Android 真机验收 / Device acceptance**  
   最后适配 Redmi K100 原生相册、文件管理器及系统分享至微信。验证原生时间线、实际预读流量、私有 VPN 及 Clash、无公网映射、存储权限、重启与掉线恢复；息屏 24 小时及连续 72 小时记录可用性、电池和温度。原生入口可行性以真机证据为准。  
   Integrate the Redmi K100 stock gallery, file manager and system share to WeChat last. Verify timeline integration, actual read-ahead traffic, private VPN and Clash behavior, no public port forwarding, storage permissions and reboot or link recovery. Record availability, battery and thermal observations during 24-hour screen-off and 72-hour continuous tests. Confirm native entry points on devices.

各软件阶段均在 CI 使用临时身份与合成文件，保留回归结果。 / Run software milestones in CI with temporary identities and synthetic files and retain regression results.
