# Author: KKV9
# This is a ranger plugin for mounting MTP devices in ranger
# Requires Gio

import subprocess
import curses
import curses.ascii
import os
from ranger.api.commands import Command


class mtpy(Command):
    """:mtpy

    Show menu to mount and unmount MTP devices
    """

    def execute(self):
        # Default key bindings
        keys_string = "q: Quit | m: Select | enter: cd"
        help_string = "Use :mtp to display the menu"

        # Initialize curses
        stdscr = curses.initscr()
        curses.curs_set(0)
        curses.cbreak()
        curses.init_pair(98, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # Define Device class
        class Device:
            bus = ""
            id = ""
            name = ""
            path = ""
            unmount = ""
            uri = ""
            mount_directory = ""
            mounted = False

        def get_device_path(bus, id):
            """Get the path of the device at bus and id
            used for mounting the device
            return path as string"""
            formatted_bus = str(bus).zfill(3)
            formatted_id = str(id).zfill(3)
            path = f"/dev/bus/usb/{formatted_bus}/{formatted_id}"
            return path

        def get_mount_directory(uri):
            uid = os.getuid()
            mount_path = f"/run/user/{uid}/gvfs/{uri}/"
            return mount_path

        def is_device_mounted(mount_path):
            if os.path.exists(mount_path):
                return True
            else:
                return False

        def unmount_device(index):
            try:
                subprocess.run(
                    ["gio", "mount", "-u", get_devices()[index].unmount],
                    text=True,
                    check=True,
                    capture_output=True,
                )
                return True
            except subprocess.CalledProcessError:
                return False

        def mount_device(index):
            try:
                subprocess.run(
                    ["gio", "mount", "-d", get_devices()[index].path],
                    text=True,
                    check=True,
                    capture_output=True,
                )
                return True
            except subprocess.CalledProcessError:
                return False

        def get_device_numbers(index=-1, data=""):
            """Get the number of devices connected to the system
            optionally get the bus and id of the device at index
            return 0 if no devices found
            always return int"""
            p1 = subprocess.Popen(["lsusb"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(
                ["grep", "MTP"],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            p1.stdout.close()
            lines = p2.communicate()[0]
            formatted_lines = str(lines).replace("\\n", "\n")
            formatted_lines = formatted_lines.replace("b'", "")
            formatted_lines = formatted_lines.splitlines()
            formatted_lines.pop()
            if index == -1:
                return len(formatted_lines)
            elif index > -1:
                if data == "bus":
                    return int(formatted_lines[index][4:7])
                elif data == "id":
                    return int(formatted_lines[index][15:18])
            return 0

        def get_device_strings(path, data="model"):
            """Get the model or serial number of the device at path
            The serial can be returned in two formats
            the unmount format is for unmounting the device
            The uri format is used to find the mount path"""
            if data == "model":
                grep_info = "ID_MODEL="
            else:
                grep_info = "ID_USB_SERIAL="

            p1 = subprocess.Popen(
                ["udevadm", "info", f"--name={path}"], stdout=subprocess.PIPE
            )
            p2 = subprocess.Popen(
                ["grep", grep_info],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            p1.stdout.close()
            lines = p2.communicate()[0]
            if data == "model":
                name = str(lines).split("=")[1].replace("_", " ").rstrip("\\n'")
            else:
                name = str(lines).split("=")[1].split("\\n")[0]

            if data == "unmount":
                name = f"mtp://{name}"
            elif data == "uri":
                name = f"mtp:host={name}"

            return name

        def get_devices():
            """Get a list of devices connected to the system
            return a list of Device objects"""
            devices = []
            for volume in range(get_device_numbers()):
                device = Device()
                device.bus = str(get_device_numbers(volume, "bus"))
                device.id = str(get_device_numbers(volume, "id"))
                device.path = get_device_path(device.bus, device.id)
                device.name = get_device_strings(device.path)
                device.unmount = get_device_strings(device.path, "unmount")
                device.uri = get_device_strings(device.path, "uri")
                device.mount_directory = get_mount_directory(device.uri)
                device.mounted = is_device_mounted(device.mount_directory)
                devices.append(device)

            return devices

        def print_menu(stdscr, selected_row_idx):
            """Display the menu"""
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            w = w // 2

            for idx, option in enumerate(get_devices()):
                menu_item = f"{idx + 1}. {option.name}"
                if option.mounted:
                    menu_item += " - Mounted"
                else:
                    menu_item += " - Available"
                x = 1
                y = 1 + idx
                if idx == selected_row_idx:
                    stdscr.attron(curses.color_pair(98))
                    stdscr.addstr(y, x, menu_item.ljust(w - 2))
                    stdscr.attroff(curses.color_pair(98))
                else:
                    stdscr.addstr(y, x, menu_item.ljust(w - 2))

            stdscr.addstr(
                h - 1, (w // 2) - len(keys_string) // 2, keys_string, curses.A_BOLD
            )
            stdscr.refresh()

        def selection(stdscr):
            """Handle key presses"""
            key = 0
            current_row = 0
            devices = get_devices()  # Get the initial list of devices
            # Quit if pressed q or ESC
            while key not in (
                ord("q"),
                curses.ascii.ESC,
                10,
            ):
                print_menu(stdscr, current_row)
                key = stdscr.getch()
                if key in (curses.KEY_UP, ord("k")) and current_row > 0:
                    current_row -= 1
                elif (
                    key in (curses.KEY_DOWN, ord("j"))
                    and current_row < len(devices) - 1
                ):
                    current_row += 1
                elif key == ord("m"):
                    stdscr.erase()
                    stdscr.addstr(
                        0,
                        0,
                        f"Selected device: {devices[current_row].name}",
                    )
                    if devices[current_row].mounted is False:
                        if mount_device(current_row):
                            stdscr.addstr(
                                2,
                                0,
                                f"device {devices[current_row].name} mounted successfully",
                            )
                        else:
                            stdscr.addstr(
                                2,
                                0,
                                f"device {devices[current_row].name} failed to mount",
                            )

                    elif devices[current_row].mounted is True:
                        if unmount_device(current_row):
                            stdscr.addstr(
                                1,
                                0,
                                f"device {devices[current_row].name} unmounted successfully",
                            )
                        else:
                            stdscr.addstr(
                                1,
                                0,
                                f"device {devices[current_row].name} failed to unmount",
                            )
                    devices = get_devices()  # Refresh the list of devices
                    stdscr.addstr(3, 0, "Press any key to continue...")
                    stdscr.getch()
            curses.endwin()
            self.fm.redraw_window()
            if key == 10:
                if devices[current_row].mounted:
                    self.fm.cd(devices[current_row].mount_directory)
                else:
                    self.fm.notify("Sorry, not mounted", bad=True)
            return

        if self.arg(1):
            if self.arg(1) == "help":
                self.fm.notify(help_string, bad=False)
                return
            else:
                self.fm.notify("Type ':mtpy help' for help", bad=True)
                return

        if get_devices():
            selection(stdscr)
        else:
            self.fm.notify("No devices found", bad=True)
            return
