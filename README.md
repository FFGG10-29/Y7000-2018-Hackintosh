# Lenovo 拯救者 Y7000 2018 — OpenCore EFI（macOS Sequoia 15.5+ / Tahoe 26）

针对本机实测硬件定制，非通用模板。生成日期 2026-10-28。

> **📦 归档说明（2026-10-28）**：本项目已停止推进，转向 Linux。原因：GTX 1060（Pascal 移动版）在 macOS 上硬件层面无解（详见第二节）。本仓库保留为存档，配置已通过 `ocvalidate` 校验零错误，若日后需要仍可直接取用。
>
> ⚠️ **仓库内的序列号 / MLB / UUID / ROM 均为占位值**，使用前请用 [GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) 生成自己的三码，否则 iMessage / FaceTime 无法激活。

---

## 一、本机实测硬件

| 部件 | 实测型号 | ID | 状态 |
|---|---|---|---|
| CPU | i5-8300H 4核8线程 2.3GHz | Coffee Lake-H | ✅ |
| 主板 | LENOVO LNVNB161216 | HM370 / Cannon Point PCH | ✅ |
| BIOS | Insyde 9VCN22WW (2020/11/30) | — | ⚠️ 需改设置 |
| 核显 | Intel UHD Graphics 630 | `8086:3E9B` | ✅ 原生 |
| 独显 | NVIDIA GeForce GTX 1060 6G | `10DE:1C20` | ❌ **硬件无解** |
| 内存 | 16GB (2×8G) DDR4-2667 Samsung | — | ✅ |
| NVMe | WDC PC SN720 512G | — | ✅ 非三星，NVMeFix 优化 |
| 声卡 | Realtek **ALC236** | `10EC:0236` | ✅ AppleALC |
| 触控板 | Synaptics (I2C-HID) | `ACPI\SYNA2B46` | ✅ VoodooI2CHID |
| 无线 | Intel Wireless-AC 9560 | `8086:A370` | ✅ Wi-Fi 可用，⚠️ 无 AirDrop |
| 有线 | Realtek RTL8168 | `10EC:8168` | ✅ |
| SMBIOS | MacBookPro16,1 | — | ✅ 15.x 与 26.x 均支持 |

---

## 二、关于 GTX 1060 —— 为什么驱动不了（重要）

这不是配置水平问题，是三重硬性阻断，请勿再在这上面耗时间：

1. **架构被排除**：NVIDIA 官方 Web Driver 最高只支持到 macOS 10.13.6。
2. **移动版无支持**：Web Driver 的设备表只含桌面版 Pascal，`1C20`（GP106 移动版）从未列入。
3. **Optimus 硬件死结**：本机 HDMI / miniDP / DP 硬连线到独显，macOS 不支持 Optimus 显示切换。

关于你提到的 **NullMoth**（`nullmoth/nvidia-macos-driver`），我核对过官方仓库原文：

> Supported cards are **Turing and newer**: GTX 16, RTX 20, 30, 40 and 50...

`docs/CARD-SUPPORT.md` 中更明确：

> **Pascal, Maxwell, Kepler, and earlier cards... They are outside the present GSP-based driver.**
> A laptop also needs a display/output route the NVIDIA card can drive; accepting its PCI ID **does not implement an Optimus display mux**.

即：Pascal 不在支持范围，且明确声明不实现 Optimus 显示多路复用。此外它还有笔记本无法满足的门槛（BIOS 需开 Above 4G Decoding、关 CSM——Insyde 笔记本 BIOS 没有这两项；官方测试机型是台式机 `iMacPro1,1`）。

**结论**：1060 必须保持屏蔽（`SSDT-DDGPU.aml` 已处理），代价是外接 HDMI/DP 无输出。

**如果确实需要外接显示器**，可行的是这两条路：
- **DisplayLink USB 显示适配器**（USB3 → HDMI），免驱性质、办公够用，是最省事方案。
- **M.2 → PCIe 外接显卡坞**接一张 AMD 卡（RX 550/560/580 或 RX 6600），macOS 原生驱动，性能真实可用；需拆机占用 M.2 槽位。

---

## 三、网卡：能用，但有上限

你的 **Intel AC 9560 确实能驱动 Wi-Fi**（这点你是对的，我先前表述不准）。但要注意驱动来源：

- 官方 `OpenIntelWireless/AirportItlwm` 仓库**已不存在**（404），上游 `itlwm` 最后一版停在 **v2.3.0（2024-06）**，最高只支持到 **Sonoma 14.4** —— 官方版跑不了 Sequoia/Tahoe。
- 本 EFI 用的是社区接盘版 **AirportItlwm 2.4.0**（`laobamac/itlwm`），我验证过其设备表含有 `0xa3708086`（即 9560）。远景论坛有 AC-9560 成功驱动的实际反馈。
- **已按系统分别配置**：`AirportItlwm-Sequoia.kext`（macOS 15）与 `AirportItlwm-Tahoe.kext`（macOS 26），通过 MinKernel/MaxKernel 自动二选一，你装哪个版本都不会选错。

**上限（这是硬件决定的，不是驱动问题）**：Intel 网卡不支持 Apple 的 AWDL 协议，因此 **AirDrop、Handoff、随航、Universal Clipboard、Apple Watch 解锁均不可用**。iMessage/FaceTime 也可能受影响。

**想要完整生态**：换博通卡即可，本机无 Wi-Fi 白名单。推荐 `BCM94352Z / DW1560`（M.2 2230，几十元）或 `BCM94360NG`（免驱度最高）。换卡后按第五节操作。

---

## 四、安装前必做：BIOS 设置

本机是 Insyde BIOS，大部分高级选项被隐藏。Y7000 系列可用
`xiaoMGitHub/LEGION_Y7000Series_Insyde_Advanced_Settings_Tools` 解锁。

必须满足以下条件：

| 项目 | 要求 | 不改的后果 |
|---|---|---|
| **CFG Lock (MSR 0xE2)** | **必须解锁** | CPU 无法变频，全程最低频、发热大 |
| DVMT Pre-Allocated | 64MB（1080p 足够） | 显存不足黑屏 |
| Secure Boot | Disabled | 无法引导 |
| SATA Mode | AHCI | 磁盘不识别 |
| Fast Boot | Disabled | 可能无法进入引导菜单 |
| VT-d | 建议关闭 | 已用 DisableIoMapper 兜底 |
| CSM | Disabled（纯 UEFI） | 引导异常 |

> 如果无法解锁 CFG Lock：把 `config.plist` 里 `Kernel → Quirks → AppleXcpmCfgLock` 改为 `True` 可开机，但代价是失去原生变频。

---

## 五、驱动清单

### 启用中（28 个）
Lilu、AMFIPass、VirtualSMC + SMCProcessor/SMCSuperIO/SMCBatteryManager、WhateverGreen、AppleALC、
VoodooI2C + VoodooGPIO/VoodooI2CServices/VoodooInput/VoodooI2CHID（触控板）、
VoodooPS2Controller + VoodooPS2Keyboard（键盘+小键盘）、USBToolBox、
AirportItlwm（Sequoia/Tahoe 二选一）、IntelBluetoothFirmware + IntelBluetoothInjector + BlueToolFixup、
RealtekRTL8111、RestrictEvents、NVMeFix、HibernationFixup、RTCMemoryFixup、CpuTscSync、BrightnessKeys

**触控板说明**：实测是 `ACPI\SYNA2B46`（Synaptics），在 Windows 下枚举为标准 I2C-HID 设备，
因此用通用的 `VoodooI2CHID.kext` 驱动（已启用）。若实际不工作，见第九节。

### 已备好但禁用（换博通卡时启用）
`AirportBrcmFixup`、`AirPortBrcmNIC_Injector`、`BrcmPatchRAM3`、`BrcmFirmwareData`、`BrcmBluetoothInjector`

换卡操作：启用上面 5 个 → 禁用 `AirportItlwm-Sequoia/Tahoe`、`IntelBluetoothFirmware`、`IntelBluetoothInjector`
→ Wi-Fi 部分还需从 OCLP 取 `IOSkywalkFamily.kext` + `IO80211FamilyLegacy.kext`（Sonoma+ 必需）。
博通蓝牙还需 NVRAM 项 `bluetoothInternalControllerInfo`（14 字节）与 `bluetoothExternalDongleFailed`。

### ACPI 补丁
PLUG、EC、USBX、AWAC、PMCR、PNLFCFL(背光)、DDGPU(屏蔽1060)、I2C、PS2K、PTSWAK、GPRW
+ 三条改名：GPRW→XPRW、_PTS→ZPTS、_WAK→ZWAK（旧 EFI 里这三条改名没启用，补丁其实没生效，这里已修正）

---

## 六、安装步骤（概要）

1. 用 [gibMacOS](https://github.com/corpnewt/gibMacOS) 下载 Sequoia 15.5+ 或 Tahoe 26 安装镜像，制作安装盘。
2. 把本目录的 `EFI` 整个复制到安装盘 ESP 分区根目录。
3. BIOS 按第四节设置好。
4. U 盘启动 → 用磁盘工具把目标盘格式化为 **APFS（GUID 分区图）** → 安装。
5. 装完把 `EFI` 复制到**硬盘**的 ESP 分区，实现免 U 盘启动。
6. 首次进系统后执行 **Reset NVRAM**（引导菜单里有这个选项）。

**安装期排错**：boot-args 里有 `-v`（啰嗦模式）。如果卡住，把卡住位置记下来排查；稳定后可去掉 `-v`。

---

## 七、装机后待办（这两项必须做）

### 1. USB 端口映射（当前是临时方案）
现在靠 `XhciPortLimit=True` 临时放开端口限制。长期必须做映射，否则 USB 速度、休眠、蓝牙都会不稳。

做法：进 macOS 后用 [USBToolBox](https://github.com/USBToolBox/tool) 生成 `UTBMap.kext`，
放进 `EFI/OC/Kexts`，在 config 里添加该条目，**然后把 `XhciPortLimit` 改回 `False`**。

### 2. 声卡 layout 试错
当前注入的是 `layout-id = 11`。ALC236 在 AppleALC 中支持的 layout 有：
**3、11、12、13、14、15、16、18、54、99**。

如果没声音或耳机有杂音，改 boot-args 里的 `alcid=` 逐个试（同时改 DeviceProperties 里的 `layout-id`）。
优先试 **11 → 18 → 3**。联想 Y7000 社区反馈 3 和 11 命中率最高。
睡眠唤醒后没声音是 `coreaudiod` 卡住，在活动监视器里退出该进程即可自动恢复。

### 3. 三码
当前三码是我生成的占位值：

```
Serial : C02VT9XYW1O8
MLB    : C02IW38NK475LUF6V
UUID   : 686AA1C1-0702-45B6-9CD5-37916ACD3EC4
ROM    : 84fdd1fc86c2  (你的 9560 真实 MAC，已填对)
```

ROM 用网卡真实 MAC 是对的（利于 iServices）。但 Serial/MLB 建议用
[GenSMBIOS](https://github.com/corpnewt/GenSMBIOS) 重新生成，并到
https://checkcoverage.apple.com/ 确认"查不到该序列号"——查得到说明与别人的真机撞号，iMessage 会被拒。

---

## 八、已知限制（硬件层面，无解）

| 项目 | 状态 | 说明 |
|---|---|---|
| GTX 1060 | ❌ | Pascal 移动版，无驱动 |
| HDMI / miniDP / DP 输出 | ❌ | 端口硬连独显，随独显一起屏蔽 |
| AirDrop / Handoff / 随航 | ⚠️ | Intel 网卡无 AWDL，换博通卡可解 |
| 内屏 / 亮度 / 硬件解码 | ✅ | UHD 630 原生 |

---

## 九、遇到问题解决顺序

1. **卡在 PCI Configuration Begin** → 多半是 CFG Lock 没解；或加 `npci=0x2000`
2. **黑屏** → DVMT 设 64MB；检查 framebuffer 注入；试去掉 `-igfxblr`
3. **Wi-Fi 不可用** → 确认加载的是对应系统版本的 AirportItlwm；检查 AMFIPass 是否启用
4. **触控板不动** → 按顺序试：
   a. BIOS 里确认 GPIO pads 已解锁（`SSDT-I2C.aml` 依赖这个）
   b. 确认 VoodooGPIO / VoodooI2CServices / VoodooI2C / VoodooInput / VoodooI2CHID 五个都加载了
   c. boot-args 加 `-vi2c-force-polling`（强制轮询模式，Synaptics 机型常见解法）
   d. 换用备用的 `VoodooI2CSynaptics.kext`（config 里已备好，禁用 VoodooI2CHID 后启用它）
5. **蓝牙不稳** → 确认 `BlueToolFixup` 已启用；先做完 USB 映射

---

## 附：EFI 体积

当前整套 `EFI` 约 **64MB**，其中 AirportItlwm 单文件就占 16MB×2（内嵌了全部 Intel 网卡固件，无法拆分）。

你的 ESP 习惯是 500MB / 800MB，完全够用，所以**不需要精简**——我已经把 OpenCore 全套 52 个 Drivers
和博通换卡备用驱动都保留在里面了，方便日后排错和换卡时直接启用，不必重新下载。

---

## 十、关于 Tahoe 26 的特别提醒

Tahoe 是 Intel 平台的最后一个 macOS 版本，它**移除了 AppleHDA**，所以 AppleALC 在 Tahoe 上会失效。

- 若**只装 Sequoia 15.5+**：声卡完美，一切正常。
- 若**装 Tahoe 26**：板载模拟音频（扬声器/耳机）需要改用 VoodooHDA，或用 KDK 恢复 AppleHDA（后者每次系统更新都要重做一遍）。

**因此建议：主力系统装 Sequoia 15.5+。** 想尝鲜 Tahoe 时，同一套 EFI 直接升级即可（网卡会自动切到 Tahoe 版本驱动）。

SMBIOS 当前用 `MacBookPro16,1`，15.x 和 26.x 都支持。若确定只用 Sequoia，可改 `MacBookPro15,1`（8 代 CPU 匹配度更高）。
