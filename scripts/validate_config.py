#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 make defconfig 后的 .config：核心功能必须全部命中，缺一即中止构建，
   产出一个"看似成功但缺功能"的固件。"""

import sys
from pathlib import Path

CFG = Path(".config").read_text(encoding="utf-8", errors="ignore")

REQUIRED = [
    ("CONFIG_TARGET_rockchip_armv8_DEVICE_hinlink_h68k=y", "H68K 设备支持（patch 未生效？）"),
    ("CONFIG_PACKAGE_luci=y",                               "LuCI 界面"),
    ("CONFIG_PACKAGE_samba4-server=y",                      "SMB 共享 (samba4)"),
    ("CONFIG_PACKAGE_luci-app-samba4=y",                    "SMB LuCI 界面"),
]

# run4 起 iStore 降级观察：luci-app-store 符号在 master apk 索引阶段不生成
# （构建依赖 csstidy/luasrcdiet host 包在 feed 里的解析断链），先出 14 项全绿固件，
# 商店走后续专项修复或官方 ipk 补装。
OPTIONAL = [
    ("CONFIG_PACKAGE_kmod-usb-printer=y",          "USB 打印机驱动(内核已内置usblp)"),
    ("CONFIG_PACKAGE_luci-app-upnp=y",               "UPnP"),
    ("CONFIG_PACKAGE_luci-app-ddns=y",               "DDNS"),
]

def diagnose(key_y: str):
    """对一个未命中项，给出它在 .config 里的真实状态"""
    base = key_y.rsplit("=", 1)[0]
    if base + "=y" in CFG:
        return "=y"
    if ("# " + base + " is not set") in CFG:
        return "显式 not set（依赖未满足被 kconfig 关闭，检查其 DEPENDS）"
    if base not in CFG:
        return "完全不存在（包不可见：feed 未安装 / 包名变更 / 该平台不提供）"
    linestart = CFG.find(base)
    return "存在但非 y: " + CFG[linestart:linestart + 80].split("\n")[0]

missing = [(c, name) for c, name in REQUIRED if c not in CFG]

print("=" * 62)
print("必需功能检查：")
for c, name in REQUIRED:
    print(f"  [{'x' if c in CFG else ' '}] {name:28s} {c}")
print("\n可选功能检查（缺失不阻断构建）：")
for c, name in OPTIONAL:
    print(f"  [{'x' if c in CFG else ' '}] {name:28s} {c}")
print("=" * 62)

if missing:
    print(f"\n[FATAL] 以下必需项未被选中（共 {len(missing)} 项）：")
    for c, name in missing:
        print(f"  - {name}: {c}")
        print(f"      ↳ 诊断: {diagnose(c)}")
    sys.exit(1)

print("\n[OK] 全部必需功能已进入固件配置，开始编译。")
