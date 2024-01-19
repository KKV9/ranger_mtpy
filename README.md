# ranger_mtpy
This script is a ranger plugin that draws a menu to mount and unmount MTP devices using gio.

# Requirements
- python3.8 or newer
- gio

# How to install
Clone this repo to the plugins directory of ranger

```Bash
cd ~/.config/ranger/plugins
git clone https://github.com/KKV9/ranger_mtpy
```
# How to use
 Type `:mtp` in ranger to show the mount menu. In this menu you can press:

- `j` or `arrow down` to move selection down
- `k` or `arrow up` to move selection up
- `Esc` or `q` to quit
- `m` to mount or unmount selected device
- `ENTER` to cd selected mount-point. If device is not mounted you will receive an error.

# Issues
- There are issues with renaming files on devices. You may have to move the file from the device and rewrite to do so.
- You may have to press `R` periodically to refresh directories within ranger.
