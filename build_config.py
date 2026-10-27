#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 Lenovo Y7000 2018 (i5-8300H / HM370 / UHD630 / GTX1060 / ALC236 / Intel AC9560)
生成 OpenCore config.plist —— 目标 macOS Sequoia 15.5+ 与 Tahoe 26 双版本
"""
import os, plistlib, uuid, random, string

BASE = r"D:\WorkBuddy\新建文件夹\Y7000-2018-Hackintosh"
OC = os.path.join(BASE, "EFI", "OC")
KEXTS = os.path.join(OC, "Kexts")
SAMPLE = os.path.join(BASE, "_downloads", "_x_OpenCore", "Docs", "Sample.plist")
ROM = bytes.fromhex("84fdd1fc86c2")   # Intel AC 9560 真实 MAC

cfg = plistlib.load(open(SAMPLE, "rb"))

def setv(d, path, val):
    cur = d
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = val

# ---------------------------------------------------------------- 通用工具
def rnd(n, alpha=True):
    pool = string.ascii_uppercase + string.digits if alpha else string.digits
    return "".join(random.choice(pool) for _ in range(n))

def kext_entry(bundle, enabled=True, min_k=None, max_k=None, comment=""):
    """bundle 相对 KEXTS 的路径，自动读取 Executable"""
    ip = os.path.join(KEXTS, bundle, "Contents", "Info.plist")
    exe = ""
    if os.path.exists(ip):
        info = plistlib.load(open(ip, "rb"))
        exe = info.get("CFBundleExecutable", "")
    e = {
        "Arch": "x86_64",
        "BundlePath": bundle,
        "Comment": comment or bundle,
        "Enabled": enabled,
        "ExecutablePath": f"Contents/MacOS/{exe}" if exe else "",
        "MaxKernel": max_k or "",
        "MinKernel": min_k or "",
        "PlistPath": "Contents/Info.plist",
    }
    return e

# ---------------------------------------------------------------- ACPI
ACPI_ADD = [
    ("SSDT-PLUG.aml",      "CPU plugin-type for XCPM"),
    ("SSDT-EC.aml",        "Embedded Controller"),
    ("SSDT-USBX.aml",      "USB power properties"),
    ("SSDT-AWAC.aml",      "300-series PCH clock AWAC to RTC"),
    ("SSDT-PMCR.aml",      "Cannon Lake PMC device"),
    ("SSDT-PNLFCFL.aml",   "Coffee Lake backlight PNLF"),
    ("SSDT-DDGPU.aml",     "Disable GTX1060 dGPU no Optimus output"),
    ("SSDT-I2C.aml",       "I2C trackpad GPIO custom"),
    ("SSDT-PS2K.aml",      "PS2 keyboard numpad custom"),
    ("SSDT-PTSWAK.aml",    "Sleep wake PTS WAK fix"),
    ("SSDT-GPRW.aml",      "Instant wake GPRW fix"),
    ("SSDT-XCPM.aml",      "ALT legacy XCPM injection pick either with PLUG", False),
]
cfg["ACPI"]["Add"] = []
for item in ACPI_ADD:
    path, comment = item[0], item[1]
    enabled = item[2] if len(item) > 2 else True
    cfg["ACPI"]["Add"].append({"Comment": comment, "Enabled": enabled, "Path": path})

def patch_entry(comment, find, replace):
    return {
        "Base": "", "BaseSkip": 0, "Comment": comment, "Count": 0, "Enabled": True,
        "Find": find, "Limit": 0, "Mask": b"", "OemTableId": b"", "Replace": replace,
        "ReplaceMask": b"", "Skip": 0, "TableLength": 0, "TableSignature": b"",
    }

cfg["ACPI"]["Patch"] = [
    patch_entry("GPRW to XPRW instant wake", b"GPRW\x02", b"XPRW\x02"),
    patch_entry("PTS to ZPTS for PTSWAK",    b"_PTS\x01", b"ZPTS\x01"),
    patch_entry("WAK to ZWAK for PTSWAK",    b"_WAK\x01", b"ZWAK\x01"),
]
def del_entry(comment, oem):
    return {"All": False, "Comment": comment, "Enabled": False, "OemTableId": oem,
            "TableLength": 0, "TableSignature": b"SSDT"}
cfg["ACPI"]["Delete"] = [
    del_entry("Delete CpuPm",   b"CpuPm\x00\x00\x00"),
    del_entry("Delete Cpu0Ist", b"Cpu0Ist\x00"),
]
cfg["ACPI"]["Quirks"].update({"FadtEnableReset": True})

# ---------------------------------------------------------------- Booter
cfg["Booter"]["Quirks"].update({
    "AvoidRuntimeDefrag": True,
    "DevirtualiseMmio": False,
    "EnableSafeModeSlide": True,
    "EnableWriteUnprotector": True,
    "ProtectUefiServices": False,
    "ProvideCustomSlide": True,
    "RebuildAppleMemoryMap": False,
    "SetupVirtualMap": True,
    "SyncRuntimePermissions": True,
})

# ---------------------------------------------------------------- Kernel
KERNEL_ADD = [
    # 基础补丁引擎必须最先
    ("Lilu.kext",                                                     True, None, None, "Patch engine must be first"),
    ("AMFIPass.kext",                                                 True, None, None, "Bypass AMFI for third-party kexts"),
    ("VirtualSMC.kext",                                               True, None, None, "SMC emulation"),
    ("SMCProcessor.kext",                                             True, None, None, "CPU temperature and power"),
    ("SMCSuperIO.kext",                                               True, None, None, "Fan monitoring"),
    ("SMCBatteryManager.kext",                                        True, None, None, "Battery status"),
    ("WhateverGreen.kext",                                            True, None, None, "iGPU patches"),
    ("AppleALC.kext",                                                 True, None, None, "ALC236 audio"),
    # 触控板 I2C
    ("VoodooI2C.kext/Contents/PlugIns/VoodooGPIO.kext",               True, None, None, "GPIO pins required by trackpad"),
    ("VoodooI2C.kext/Contents/PlugIns/VoodooI2CServices.kext",        True, None, None, "I2C services"),
    ("VoodooI2C.kext",                                                True, None, None, "I2C bus"),
    ("VoodooI2C.kext/Contents/PlugIns/VoodooInput.kext",              True, None, None, "Input bridge load once only"),
    ("VoodooI2CHID.kext",                                             True, None, None, "I2C-HID trackpad SYNA2B46"),
    ("VoodooI2CSynaptics.kext",                                       False, None, None, "ALT Synaptics trackpad if I2CHID fails"),
    # 键盘
    ("VoodooPS2Controller.kext",                                      True, None, None, "PS2 controller"),
    ("VoodooPS2Controller.kext/Contents/PlugIns/VoodooPS2Keyboard.kext", True, None, None, "Keyboard and numpad"),
    # USB
    ("USBToolBox.kext",                                               True, None, None, "USB mapping support"),
    # Wi-Fi：Sequoia / Tahoe 分别加载对应版本
    ("AirportItlwm-Sequoia.kext",                                     True, "24.0.0", "24.99.99", "Intel AC9560 WiFi macOS 15"),
    ("AirportItlwm-Tahoe.kext",                                       True, "25.0.0", "",          "Intel AC9560 WiFi macOS 26"),
    # 蓝牙
    ("IntelBluetoothFirmware.kext",                                   True, None, None, "Intel Bluetooth firmware"),
    ("IntelBluetoothInjector.kext",                                   True, None, None, "Intel Bluetooth injector"),
    ("BlueToolFixup.kext",                                            True, "21.0.0", None, "Bluetooth stack fix macOS 12 plus"),
    # 有线
    ("RealtekRTL8111.kext",                                           True, None, None, "RTL8168 ethernet"),
    # 杂项
    ("RestrictEvents.kext",                                           True, None, None, "CPU name and restriction"),
    ("NVMeFix.kext",                                                  True, None, None, "NVMe power management SN720"),
    ("HibernationFixup.kext",                                         True, None, None, "Hibernation fix"),
    ("RTCMemoryFixup.kext",                                           True, None, None, "RTC memory fix"),
    ("CpuTscSync.kext",                                               True, None, None, "TSC sync wake stability"),
    ("BrightnessKeys.kext",                                           True, None, None, "Brightness keys"),
    # 备用：换博通卡后启用下面这些，并禁用 AirportItlwm / IntelBluetooth*
    ("AirportBrcmFixup.kext",                                         False, None, None, "ALT Broadcom WiFi enable after card swap"),
    ("AirPortBrcmNIC_Injector.kext",                                  False, None, None, "ALT Broadcom injector"),
    ("BrcmPatchRAM3.kext",                                            False, None, None, "ALT Broadcom BT firmware upload"),
    ("BrcmFirmwareData.kext",                                         False, None, None, "ALT Broadcom firmware data"),
    ("BrcmBluetoothInjector.kext",                                    False, None, None, "ALT Broadcom BT injector"),
    ("CPUFriend.kext",                                                False, None, None, "OPT needs CPUFriendDataProvider"),
]
cfg["Kernel"]["Add"] = [kext_entry(*a) for a in KERNEL_ADD]

cfg["Kernel"]["Quirks"].update({
    "AppleCpuPmCfgLock": False,       # 需 BIOS 解锁 CFG Lock
    "AppleXcpmCfgLock": False,        # 需 BIOS 解锁 CFG Lock (MSR 0xE2)
    "CustomSMBIOSGuid": False,
    "DisableIoMapper": True,          # VT-d
    "DisableLinkeditJettison": True,
    "ExtendBTFeatureFlags": True,     # Intel 蓝牙
    "LapicKernelPanic": False,
    "PanicNoKextDump": True,
    "PowerTimeoutKernelPanic": True,
    "ProvideCurrentCpuInfo": False,
    "XhciPortLimit": True,            # 临时，做完 USB 映射后改 False
})

# ---------------------------------------------------------------- DeviceProperties
IG = "PciRoot(0x0)/Pci(0x2,0x0)"
HDA = "PciRoot(0x0)/Pci(0x1f,0x3)"
cfg["DeviceProperties"]["Add"] = {
    IG: {
        "AAPL,ig-platform-id": bytes.fromhex("0900a53e"),   # 0x3EA50009 Coffee Lake
        "AAPL,slot-name": "Internal@0,2,0",
        "device-id": bytes.fromhex("9b3e0000"),             # 0x3E9B UHD630
        "disable-external-gpu": bytes.fromhex("01000000"),
        "enable-backlight-registers-fix": bytes.fromhex("01000000"),
        "framebuffer-patch-enable": bytes.fromhex("01000000"),
        "framebuffer-unifiedmem": bytes.fromhex("00000080"),  # 2048MB DVMT
        "hda-gfx": "onboard-1",
        "model": "Intel UHD Graphics 630 (Mobile)",
    },
    HDA: {
        "AAPL,slot-name": "Internal@0,31,3",
        "alc-delay": 600,
        "device_type": "Audio device",
        "hda-gfx": "onboard-1",
        "layout-id": bytes.fromhex("0b000000"),             # 11 (ALC236)
        "model": "Realtek ALC236",
    },
}

# ---------------------------------------------------------------- NVRAM
GUID = "7C436110-AB2A-4BBB-A880-FE41995C9F82"
BOOT_ARGS = "-v keepsyms=1 alcid=11 igfxrpsc=1 -igfxblr rtcfx_exclude=80-FF vsmcgen=1 revpatch=auto"
cfg["NVRAM"]["Add"][GUID]["boot-args"] = BOOT_ARGS
cfg["NVRAM"]["Add"][GUID]["csr-active-config"] = bytes.fromhex("03080000")  # 部分关闭：允许三方 kext
cfg["NVRAM"]["Delete"][GUID] = ["boot-args", "csr-active-config"]

# ---------------------------------------------------------------- Misc
cfg["Misc"]["Boot"].update({
    "Timeout": 5,
    "ShowPicker": True,
    "HideAuxiliary": False,
    "PickerMode": "Builtin",   # 内置文本菜单，不依赖 OcBinaryData/Resources
})
cfg["Misc"]["Security"].update({
    "AllowSetDefault": True,
    "ScanPolicy": 0,
    "SecureBootModel": "Disabled",
    "Vault": "Optional",
})

# ---------------------------------------------------------------- PlatformInfo
# 固定三码（与 README 保持一致；建议装机后用 GenSMBIOS 重新生成）
SERIAL = "C02VT9XYW1O8"
MLB = "C02IW38NK475LUF6V"
FIXED_UUID = "686AA1C1-0702-45B6-9CD5-37916ACD3EC4"
cfg["PlatformInfo"]["Automatic"] = True
cfg["PlatformInfo"]["UpdateSMBIOSMode"] = "Create"
cfg["PlatformInfo"]["Generic"].update({
    "AdviseFeatures": False,
    "MLB": MLB,
    "ROM": ROM,
    "SpoofVendor": True,
    "SystemProductName": "MacBookPro16,1",
    "SystemSerialNumber": SERIAL,
    "SystemUUID": FIXED_UUID,
})

# ---------------------------------------------------------------- UEFI
def drv(path):
    return {"Arguments": "", "Comment": "", "Enabled": True, "HideVerbose": False,
            "LoadEarly": False, "Path": path}
cfg["UEFI"]["Drivers"] = [
    drv("OpenRuntime.efi"),
    drv("OpenHfsPlus.efi"),
    drv("ResetNvramEntry.efi"),
    drv("ToggleSipEntry.efi"),
]
cfg["UEFI"]["Input"].update({
    "KeySupport": True,        # PS2 键盘在引导菜单可用
    "KeyForgetThreshold": 5,
    "PointerSupport": True,
})
cfg["UEFI"]["Output"].update({
    "ClearScreenOnModeSwitch": False,
    "ProvideConsoleGop": True,
    "Resolution": "1920x1080",
})
cfg["UEFI"]["Quirks"].update({
    "ReleaseUsbOwnership": False,
    "RequestBootVarRouting": True,
    "UnblockFsConnect": False,
})

# ---------------------------------------------------------------- 写出
out = os.path.join(OC, "config.plist")
plistlib.dump(cfg, open(out, "wb"), sort_keys=False)
print("[OK] 已生成:", out)
print()
print("序列号 Serial :", SERIAL)
print("主板号  MLB   :", MLB)
print("UUID          :", cfg["PlatformInfo"]["Generic"]["SystemUUID"])
print("ROM (网卡 MAC):", ROM.hex())
print()
print("kernel kext 数量:", len(cfg["Kernel"]["Add"]), "| 启用:", sum(1 for k in cfg["Kernel"]["Add"] if k["Enabled"]))
missing = [k["BundlePath"] for k in cfg["Kernel"]["Add"] if not os.path.exists(os.path.join(KEXTS, k["BundlePath"]))]
print("缺失的 kext:", missing or "无")
missing_aml = [a["Path"] for a in cfg["ACPI"]["Add"] if not os.path.exists(os.path.join(OC, "ACPI", a["Path"]))]
print("缺失的 SSDT :", missing_aml or "无")
