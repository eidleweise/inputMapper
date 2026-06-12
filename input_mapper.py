#!/usr/bin/env python3
import os
import sys
import struct
import select

# Translation layer for Joysticks: Linux Axis Code -> (Linux Name, Ace Combat 7 INI Name)
AXIS_TRANSLATION = {
    0x00: ("ABS_X", "X"),  # Main Stick Roll
    0x01: ("ABS_Y", "Y"),  # Main Stick Pitch
    0x02: ("ABS_Z", "Z"),  # Main Throttle Slider Rail
    0x03: ("ABS_RX", "Rx"),  # Mini-stick Horizontal / Camera
    0x04: ("ABS_Ry", "Ry"),  # Mini-stick Vertical / Camera
    0x05: ("ABS_RZ", "Rz"),  # Throttle Rocker Paddles (Yaw)
    0x06: ("ABS_THROTTLE", "Slider1"),  # Alternative slider layouts
    0x07: ("ABS_RUDDER", "Slider2"),  # Small dial/wheel on side of TWCS
}

# Translation layer for POV Hat Switches (Linux absolute values -> AC7 Hat directions)
HAT_TRANSLATION = {
    (16, -1): "POV_L1",
    (16, 1): "POV_R1",
    (17, -1): "POV_U1",
    (17, 1): "POV_D1",
}


def get_devices():
    """Scans /dev/input/ and finds human-readable names for joysticks/controllers."""
    devs = []
    for filename in sorted(os.listdir('/dev/input/')):
        if filename.startswith('event'):
            path = os.path.join('/dev/input/', filename)
            try:
                with open(f"/sys/class/input/{filename}/device/name", "r") as f:
                    name = f.read().strip()
                devs.append((path, name))
            except IOError:
                continue
    return devs


def main():
    if os.geteuid() != 0:
        print("[-] Error: This script must be run with 'sudo' to read raw hardware bytes.")
        sys.exit(1)

    all_devices = get_devices()
    fds = {}

    # Target keywords for your default hardware setup
    target_throttle = "TWCS"
    target_stick = "Gladiator"

    found_throttle = False
    found_stick = False

    print("=== Auto-Detecting Default Flight Hardware ===")
    for path, name in all_devices:
        clean_name = name.replace("© Alex Oz 2012-2019 ", "")

        # Auto-match devices based on our target keywords
        if target_throttle in clean_name or target_stick in clean_name:
            if target_throttle in clean_name:
                found_throttle = True
            if target_stick in clean_name:
                found_stick = True

            print(f"[+] Autoselect: {path} -> {clean_name}")
            file_obj = open(path, 'rb')
            fds[file_obj.fileno()] = (file_obj, clean_name)

    # Fallback to manual selection if one of your components is unplugged
    if not found_throttle or not found_stick:
        print("\n[!] Warning: Could not find both default devices automatically.")
        print("Reverting to standard manual selection menu...")
        fds.clear()  # Clear any partial matches

        print("\n=== Available Input Devices ===")
        for i, (path, name) in enumerate(all_devices):
            display_name = name.replace("© Alex Oz 2012-2019 ", "")
            print(f"[{i}] {path} -> {display_name}")

        print("\nEnter device numbers to track (e.g. '1,2'):")
        try:
            selection = input(">> ").strip()
            for idx in [int(x.strip()) for x in selection.split(",")]:
                path, name = all_devices[idx]
                clean_name = name.replace("© Alex Oz 2012-2019 ", "")
                file_obj = open(path, 'rb')
                fds[file_obj.fileno()] = (file_obj, clean_name)
        except (ValueError, IndexError):
            print("[-] Invalid selection. Exiting.")
            sys.exit(1)

    print("\nDo you want to ignore Analog/Axis movements? (y/n)")
    ignore_axes = input(">> ").lower().strip() == 'y'

    print("\n[+] Monitoring inputs. Press Ctrl+C to exit.")
    print("-" * 90)

    struct_format = 'QQHHi'
    struct_size = struct.calcsize(struct_format)

    try:
        while True:
            r, _, _ = select.select(fds.keys(), [], [])
            for fd in r:
                file_obj, dev_name = fds[fd]
                data = file_obj.read(struct_size)
                if not data:
                    continue

                _, _, ev_type, ev_code, ev_value = struct.unpack(struct_format, data)

                # 1. Handle Key/Button events (EV_KEY)
                if ev_type == 1:
                    state = "PRESSED" if ev_value == 1 else "RELEASED" if ev_value == 0 else "HOLDING"
                    if ev_code >= 288:
                        ac7_label = f"Button{ev_code - 287}"
                    else:
                        ac7_label = "N/A"
                    print(
                        f"[{dev_name:<25}] BUTTON | Linux Code: {ev_code:<3} -> Proton Layer: {ac7_label:<9} | [{state}]")

                # 2. Handle Axis/Analog/Hat movements (EV_ABS)
                elif ev_type == 3:
                    if ev_code in (16, 17):
                        hat_lookup = HAT_TRANSLATION.get((ev_code, ev_value))
                        if hat_lookup:
                            print(
                                f"[{dev_name:<25}] D-PAD  | Linux Code: {ev_code:<3} -> Proton Layer: {hat_lookup:<9} | [ACTIVE]")
                        elif ev_value == 0:
                            axis_meta = "Horizontal" if ev_code == 16 else "Vertical"
                            print(f"[{dev_name:<25}] D-PAD  | {axis_meta} Hat centered reset")
                    elif not ignore_axes:
                        linux_name, ac7_axis = AXIS_TRANSLATION.get(ev_code, (f"ABS_UNMAPPED_{ev_code}", "Unknown"))
                        print(
                            f"[{dev_name:<25}] AXIS   | Code: {ev_code:<2} ({linux_name:<12}) -> Proton Layer: {ac7_axis:<6} | Value: {ev_value}")

    except KeyboardInterrupt:
        print("\n[+] Monitoring stopped cleanly.")
        for file_obj, _ in fds.values():
            file_obj.close()


if __name__ == "__main__":
    main()