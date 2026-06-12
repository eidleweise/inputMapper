#!/usr/bin/env python3
import os
import sys
import select
from evdev import list_devices, InputDevice, ecodes

def select_devices():
    """Scans and presents a multi-selection menu for available input devices."""
    devices = [InputDevice(path) for path in list_devices()]
    if not devices:
        print("[-] No input devices found. Did you run with 'sudo'?")
        sys.exit(1)

    print("\n=== Available Input Devices ===")
    for i, dev in enumerate(devices):
        print(f"[{i}] {dev.path} - {dev.name}")

    print("\nEnter the numbers you want to monitor (e.g., '0' or '0,1' for multiple):")
    selection = input(">> ").strip()
    
    selected_devices = []
    try:
        indices = [int(x.strip()) for x in selection.split(",")]
        for idx in indices:
            selected_devices.append(devices[idx])
    except (ValueError, IndexError):
        print("[-] Invalid device selection.")
        sys.exit(1)
        
    return selected_devices

def main():
    # 1. Choose the devices to look at
    monitored_devices = select_devices()
    
    # 2. Toggle option to mute Axis data
    print("\n--- Filter Options ---")
    print("Do you want to ignore Axis/Analog stick movements? (y/n)")
    ignore_axes = input(">> ").lower().strip() == 'y'

    print("\n[+] Monitoring inputs. Press Ctrl+C to exit.")
    if ignore_axes:
        print("[!] Axis movements are MUTED. Only displaying button clicks.")
    print("-" * 65)

    # Structure our devices so the 'select' module can monitor them simultaneously
    device_dict = {dev.fd: dev for dev in monitored_devices}

    try:
        while True:
            # select() waits until one of the hardware file descriptors has data ready
            r, w, x = select.select(device_dict.keys(), [], [])
            for fd in r:
                for event in device_dict[fd].read():
                    
                    # Target button presses (EV_KEY)
                    if event.type == ecodes.EV_KEY:
                        # Translate Linux event code to traditional Windows DirectInput count
                        # Linux trigger/joystick block starts at 288 (BTN_TRIGGER)
                        di_button = event.code - 287 if event.code >= 288 else "N/A"
                        
                        # Fetch the clean human name (e.g. BTN_TRIGGER, KEY_A)
                        native_name = ecodes.KEY.get(event.code, f"UNKNOWN_KEY_{event.code}")
                        
                        # Determine event state text
                        if event.value == 1:
                            state = "PRESSED"
                        elif event.value == 0:
                            state = "RELEASED"
                        else:
                            state = "HOLDING"

                        print(f"[{device_dict[fd].name}] BUTTON | Native: {native_name:<12} -> AceCombat ID: Button{di_button:<3} | [{state}]")

                    # Target axis movements (EV_ABS) - Skip if user requested to filter them out
                    elif event.type == ecodes.EV_ABS and not ignore_axes:
                        axis_name = ecodes.ABS.get(event.code, f"UNKNOWN_AXIS_{event.code}")
                        print(f"[{device_dict[fd].name}] AXIS   | Native: {axis_name:<12} -> Position Value: {event.value}")

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped cleanly.")

if __name__ == "__main__":
    # Quick sanity check for root privileges
    if os.geteuid() != 0:
        print("[-] Error: This script must be run with 'sudo' to access physical hardware events.")
        sys.exit(1)
    main()
