# 🛠️ AC7 Linux Input Mapper

A lightweight, zero-dependency, pure-Python tool designed to map and translate raw Linux input events (`/dev/input/`) directly into the format expected by *Ace Combat 7: Skies Unknown* running under Proton/Wine.

> **⚠️ Disclaimer:** This script is built for **personal use** and is held together with a healthy amount of enthusiast jank. It directly intercepts raw hardware bytes to bypass the immutable file systems on atomic Linux distributions (like Bazzite or SteamOS) where installing heavy compiler tools or system-level wrapper packages is a massive pain.

---

## 🚀 Why This Exists

*Ace Combat 7* was built primarily for standard console gamepads. When dealing with high-end, split-device flight hardware (like a VKB Gladiator stick paired with a Thrustmaster TWCS throttle), the game engine gets incredibly confused about device indexes. Furthermore, the game's `Input.ini` file uses Windows DirectInput labels (`X`, `Y`, `Rz`, `POV_U1`) instead of standard Linux naming conventions.

This script does two things:
1. **Auto-detects** your specific VKB Gladiator and TWCS hardware on startup (even though Linux dynamically scrambles their `/dev/input/eventX` numbers on every single reboot). It'll detect any hardware, but these are mine...
2. **Prints a dual-translation stream** in real-time, showing you exactly what physical button you just pressed alongside the precise string code you need to copy-paste into your `Input.ini` file.

---

## 📦 Prerequisites

* **Python 3.x** (Standard installation)
* **Zero external dependencies** (`pip install` is completely unnecessary).
* **Sudo privileges** (Required by Linux to safely read raw hardware event streams from `/dev/input/`).

---

## 🏃‍♂️ How to Run It

1. Make the script executable:
```bash
   chmod +x input_mapper_pro.py