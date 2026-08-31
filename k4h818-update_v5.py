#!/usr/bin/python3
# k4h818-update
#
# Updates a K4H818 radio module's firmware via avrdude. Replaces the two
# separate board-specific scripts (k4h818_usb0_fwu.sh for KHARI PiXX,
# k4h818_ama0_fwu.sh for KHARI PiHat) with one script that detects which
# board is present and does the right thing -- board-detection and GPIO
# tool selection logic reused from K4H818-prog.
#
# Usage:
#   k4h818-update.py            Always fetches K4H818_fw_latest.hex fresh
#                                from GitHub -- never cached, so this is
#                                never stale.
#   k4h818-update.py -1.5.13    Fetches K4H818_fw_1.5.13.hex once, caches
#                                it in this script's own directory, and
#                                reuses that cached copy on future runs
#                                with the same version -- a specific,
#                                already-published version's content
#                                never changes, so caching it is safe.
#
# Either way, the resulting .hex is flashed the same way: board is
# detected automatically, GPIO reset (PiHat) or nothing extra (PiXX) is
# handled the same as always, avrdude does the actual flash.

import os
import re
import sys
import glob
import time
import shutil
import subprocess
import urllib.request
import urllib.error

K4H818_RESET_GPIO = 19  # BCM numbering - K4H818 reset line on the KHARI PiHat
GPIOCHIP_NAME = 'gpiochip0'  # 'gpiochip4' on Pi 5 -- see note below if this fails

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Confirmed URL pattern -- org Kits4Hams, repo K4H818_firmware, branch main.
GITHUB_FIRMWARE_BASE_URL = "https://raw.githubusercontent.com/Kits4Hams/K4H818_firmware/main/"


def find_board():
    """Returns ('usb0', '/dev/ttyUSBx') for a PiXX, ('pihat', '/dev/ttyAMA0'
    or '/dev/ttyS0') for a PiHat, or (None, None) if neither is found.
    ttyUSB* is checked first, matching K4H818-prog's own device order --
    it only ever appears when a real USB-serial adapter is genuinely
    plugged in. /dev/ttyAMA0 (and ttyS0) can be permanently present on a
    Pi just because the onboard UART is enabled at the OS level,
    regardless of whether a PiHat is actually wired to it -- checking
    those first would wrongly prefer a PiHat path on a PiXX system."""
    usb_ports = sorted(glob.glob('/dev/ttyUSB*'))
    if usb_ports:
        return ('usb0', usb_ports[0])
    for path in ('/dev/ttyAMA0', '/dev/ttyS0'):
        if os.path.exists(path):
            return ('pihat', path)
    return (None, None)


def reset_pihat():
    # K4H818 reset (pin 4) is wired to GPIO19 through a 0.1uF coupling
    # capacitor. Because it's AC-coupled, only the falling edge actually
    # matters -- the cap blocks DC, so the GPIO's level after the pulse
    # doesn't hold the AVR in reset. This exact sequence (HIGH, settle,
    # LOW, flash while still nominally low, HIGH again afterward) matches
    # the original k4h818_ama0_fwu.sh, proven working on real hardware.
    #
    # Two different GPIO tools are used depending on what's actually
    # available, detected directly rather than guessed by OS/distro:
    #   - 'gpio' (WiringPi): still shipped and confirmed working on
    #     HamVOIP, preferred whenever present.
    #   - libgpiod (Python 'gpiod' module): fallback for systems where
    #     WiringPi has been dropped (e.g. ASL3). Its Python API changed
    #     completely between v1 and v2, so that's detected too rather
    #     than assumed. '/dev/gpiochip0' is correct on the Pi 3/4/5 (Pi
    #     5's RP1 southbridge still exposes it as a compatibility layer)
    #     -- if this fails to find GPIO19, run 'gpiodetect' to find the
    #     right chip name for this board and update GPIOCHIP_NAME above.
    print("Resetting K4H818 via GPIO19...")
    if shutil.which('gpio'):
        r1 = subprocess.call(['gpio', '-g', 'mode', str(K4H818_RESET_GPIO), 'out'])
        r2 = subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '1'])
        time.sleep(0.5)
        r3 = subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '0'])
        if r1 != 0 or r2 != 0 or r3 != 0:
            print("WARNING: 'gpio' command reported an error -- the K4H818 may not")
            print("have actually been reset. This often means a permissions issue")
            print("(GPIO access usually needs root or 'gpio' group membership) --")
            print("try running with sudo.\n")
        return lambda: subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '1'])
    else:
        import gpiod
        try:
            if hasattr(gpiod, 'LINE_REQ_DIR_OUT'):
                # v1 API
                chip = gpiod.Chip('/dev/' + GPIOCHIP_NAME)
                reset_line = chip.get_line(K4H818_RESET_GPIO)
                reset_line.request(consumer="k4h818-update", type=gpiod.LINE_REQ_DIR_OUT)
                reset_line.set_value(1)
                time.sleep(0.5)
                reset_line.set_value(0)
                def restore():
                    reset_line.set_value(1)
                    reset_line.release()
                    chip.close()
                return restore
            else:
                # v2 API
                from gpiod.line import Direction, Value
                request = gpiod.request_lines(
                    '/dev/' + GPIOCHIP_NAME,
                    consumer="k4h818-update",
                    config={
                        K4H818_RESET_GPIO: gpiod.LineSettings(
                            direction=Direction.OUTPUT, output_value=Value.ACTIVE
                        )
                    },
                )
                time.sleep(0.5)
                request.set_value(K4H818_RESET_GPIO, Value.INACTIVE)
                def restore():
                    request.set_value(K4H818_RESET_GPIO, Value.ACTIVE)
                    request.release()
                return restore
        except Exception as e:
            print("WARNING: GPIO reset failed (" + str(e) + ") -- the K4H818 may")
            print("not have actually been reset. This often means a permissions")
            print("issue (GPIO access usually needs root or 'gpio' group")
            print("membership) -- try running with sudo.\n")
            return lambda: None


def parse_requested_version():
    """Scans sys.argv for a version-number-style argument (e.g. '-1.5.13').
    Returns the version string (e.g. '1.5.13') or None if not specified
    (meaning: always fetch latest, fresh, every time)."""
    version_pattern = re.compile(r'^-(\d+\.\d+\.\d+)$')
    for arg in sys.argv[1:]:
        match = version_pattern.match(arg)
        if match:
            return match.group(1)
    return None


def download_firmware(url, dest_path):
    """Downloads url to dest_path. Returns True on success, False (with
    an error message already printed) on any failure."""
    print("Fetching " + url + " ...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True
    except urllib.error.HTTPError as e:
        print("Error: " + url + " returned HTTP " + str(e.code) + ".")
        if e.code == 404:
            print("Check that the version number is correct and that this")
            print("build was actually published to the K4H818_firmware repo.")
        return False
    except urllib.error.URLError as e:
        print("Error: could not reach " + url + " (" + str(e.reason) + ").")
        print("Check network connectivity and try again.")
        return False
    except Exception as e:
        print("Error downloading firmware: " + str(e))
        return False


def determine_firmware_path():
    """Returns the local path to the .hex file to flash, fetching it from
    GitHub first if needed. Returns None on any failure (already
    reported to the user)."""
    requested_version = parse_requested_version()

    if requested_version is not None:
        # Specific version requested: check the local cache first -- a
        # specific, already-published version's content never changes,
        # so a cached copy is always safe to reuse.
        local_path = os.path.join(SCRIPT_DIR, 'K4H818_fw_' + requested_version + '.hex')
        if os.path.isfile(local_path):
            print("Using cached " + local_path)
            return local_path
        url = GITHUB_FIRMWARE_BASE_URL + 'K4H818_fw_' + requested_version + '.hex'
        if download_firmware(url, local_path):
            return local_path
        return None
    else:
        # No version specified: always fetch latest, fresh, every time --
        # never cached, so this can never go stale the way a one-time
        # install-time copy would.
        local_path = os.path.join(SCRIPT_DIR, 'K4H818_fw_latest.hex')
        url = GITHUB_FIRMWARE_BASE_URL + 'K4H818_fw_latest.hex'
        if download_firmware(url, local_path):
            return local_path
        return None


def main():
    firmware_path = determine_firmware_path()
    if firmware_path is None:
        sys.exit(1)

    if not shutil.which('avrdude'):
        print("Error: avrdude is not installed.")
        print("Install it (e.g. 'sudo apt-get install avrdude' on ASL3, or")
        print("'pacman -S avrdude' on HamVOIP) and try again.\n")
        sys.exit(1)

    board, port = find_board()
    if board is None:
        print("Error: no K4H818 found -- neither /dev/ttyAMA0 nor /dev/ttyUSB* is present.\n")
        sys.exit(1)

    print("Found K4H818 on " + port + " (" + ("KHARI PiHat" if board == 'pihat' else "KHARI PiXX") + ")")

    restore_reset = None
    if board == 'pihat':
        restore_reset = reset_pihat()

    print("Flashing " + firmware_path + "...")
    result = subprocess.call([
        'avrdude', '-c', 'arduino', '-p', 'm328p',
        '-P', port, '-b', '57600',
        '-U', 'flash:w:' + firmware_path,
    ])

    if restore_reset is not None:
        restore_reset()

    if result == 0:
        print("\nFirmware update successful.\n")
        sys.exit(0)
    else:
        print("\navrdude reported an error -- firmware update failed. See output above.\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
