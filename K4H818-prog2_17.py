#!/usr/bin/python3
# K4H818 programmer by N8AR 2026/07/03.
# Based on SA818-prog from Kits 4 Hams
#Current version = 1.70  so change line 29

#Change Log

import time
import serial
import sys
import signal
import os
import shutil
import subprocess


### VARIABLE DECLARATIONS ###

tx_ctcss = ''
rx_ctcss = ''
tx_dcs = ''
rx_dcs = ''
txaudtone = ''
rxaudtone = ''
txaudText = ''
rxaudText = ''
ctcssSTEtone = "5500"  # This is 55 Hz
cdcssSTEtone = "13440"  # This is 134.4 Hz
tx_CDCSS_polarity_text = ''
rx_CDCSS_polarity_text = ''
prog_ver = '2.17'
verboseMode = '-v' in sys.argv  # -v: print every command sent during programming
                                 # (instead of a '+' progress tick), plus full
                                 # connection diagnostics (reset timing, raw
                                 # bytes received, etc)
expertMode = '-e' in sys.argv  # -e: ask for RX analog gain (volume1) and RX DSP gain (volume2) directly, instead of a single 0-39 RX Volume index
CRLF='\r\n'

# ANSI terminal colors, used for caution/warning messages
CAUTION = '\033[1;33m'  # bold yellow
COLOR_RESET = '\033[0m'

#CTCSS tone to code dictionary
codelookup = {
  "0": "0000", 
  "67.0": "0001",
  "71.9": "0002",
  "74.4": "0003",
  "77.0": "0004",
  "79.7": "0005",
  "82.5": "0006",
  "85.4": "0007",
  "88.5": "0008",
  "91.5": "0009",
  "94.8": "0010",
  "97.4": "0011",
  "100.0": "0012",
  "103.5": "0013",
  "107.2": "0014",
  "110.9": "0015",
  "114.8": "0016",
  "118.8": "0017",
  "123.0": "0018",
  "127.3": "0019",
  "131.8": "0020",
  "136.5": "0021",
  "141.3": "0022",
  "146.2": "0023",
  "151.4": "0024",
  "156.7": "0025",
  "162.2": "0026",
  "167.9": "0027",
  "173.8": "0028",
  "179.9": "0029",
  "186.2": "0030",
  "192.8": "0031",
  "203.5": "0032",
  "210.7": "0033",
  "218.1": "0034",
  "225.7": "0035",
  "233.6": "0036",
  "241.8": "0037",
  "250.3": "0038"
}
# 83 DCS codes from TIA-603-E specification (https://fasma.org/wp-content/uploads/TIA-603-E-1.pdf)
dcs_codes = ["023", "025", "026", "031", "032", "043", "047", "051", "054", "065",
    "071", "072", "073", "074", "114", "115", "116", "125", "131", "132",
    "134", "143", "152", "155", "156", "162", "165", "172", "174", "205",
    "223", "226", "243", "244", "245", "251", "261", "263", "265", "271", 
  "306", "311", "315", "331", "343", "346", "351", "364", "365", "371",
    "411", "412", "413", "423", "431", "432", "445", "464", "465", "466",
    "503", "506", "516", "532", "546", "565", "606", "612", "624", "627",
    "631", "632", "654", "662", "664", "703", "712", "723", "731", "732",
    "734", "743", "754"]
    

# Bit patterns in hex for normal and inverted DCS codes
dcs_normal = [0x640E37, 0x540F6B, 0x340DD3, 0x4C0FC5, 0x2C0D7D, 0x620B6D, 0x720DF8,
    0x4A0A9F, 0x1A097B, 0x560C5D, 0x4E0CF3, 0x2E0E4B, 0x6E0B3A, 0x1E0F17,
    0x190BD6, 0x590EA7, 0x390C1F, 0x550EF0, 0x4D0E5E, 0x2D0CE6, 0x1D0DBA,
    0x630AF6, 0x2B09BC, 0x5B0D91, 0x3B0F29, 0x2709EB, 0x570DC6, 0x2F0FD0,
    0x1F0E8C, 0x508CBB, 0x648B8B, 0x34886F, 0x628ED1, 0x128AFC, 0x528F8D,
    0x4A8F23, 0x468F74, 0x6688BD, 0x5689E1, 0x4E894F, 0x318F98, 0x498D8E,
    0x598B1B, 0x4D8BE2, 0x638F4A, 0x338CAE, 0x4B8EB8, 0x178D0B, 0x57887A,
    0x4F88D4, 0x484B77, 0x2849CF, 0x684CBE, 0x644CE9, 0x4C4D1B, 0x2C4FA3,
    0x5248EF, 0x164BF2, 0x564E83, 0x364C3B, 0x614B1E, 0x3148FA, 0x394EC1,
    0x2D4E38, 0x334BCC, 0x574F18, 0x30CCDD, 0x28CC73, 0x14CD78, 0x74CFC0,
    0x4CC8A7, 0x2CCA1F, 0x1ACE19, 0x26CF12, 0x16CE4E, 0x61CEA2, 0x29CDE8,
    0x65C8CE, 0x4DC93C, 0x2DCB84, 0x1DCAD8, 0x63CD94, 0x1BCF82]

dcs_inverted = [0x1BF1C8, 0x2BF094, 0x4BF22C, 0x33F03A, 0x53F282, 0x1DF492, 0x0DF207, 0x35F560,
    0x65F684, 0x29F3A2, 0x31F30C, 0x51F1B4, 0x11F4C5, 0x61F0E8, 0x66F429, 0x26F158,
    0x46F3E0, 0x2AF10F, 0x32F1A1, 0x52F319, 0x62F245, 0x1CF509, 0x54F643, 0x24F26E,
    0x44F0D6, 0x58F614, 0x28F239, 0x50F02F, 0x60F173, 0x2F7344, 0x1B7474, 0x4B7790,
    0x1D712E, 0x6D7503, 0x2D7072, 0x3570DC, 0x39708B, 0x197742, 0x29761E, 0x3176B0,
    0x4E7067, 0x367271, 0x2674E4, 0x32741D, 0x1C70B5, 0x4C7351, 0x347147, 0x6872F4,
    0x287785, 0x30772B, 0x37B488, 0x57B630, 0x17B341, 0x1BB316, 0x33B2E4, 0x53B05C,
    0x2DB710, 0x69B40D, 0x29B17C, 0x49B3C4, 0x1EB4E1, 0x4EB705, 0x46B13E, 0x52B1C7,
    0x4CB433, 0x28B0E7, 0x4F3322, 0x57338C, 0x6B3287, 0x0B303F, 0x333758, 0x5335E0,
    0x6531E6, 0x5930ED, 0x6931B1, 0x1E315D, 0x563217, 0x1A3731, 0x3236C3, 0x52347B,
    0x623527, 0x1C326B, 0x64307D]

subaud_tone_type = ["No Sub-audible tone", "CTCSS", "CDCSS", "CTCSS with squelch tail elimination", 
"CDCSS with squelch tail elimination"]

volume1 = [3,5,5,6,5,6,6,8,6,5,7,10,8,10,8,9,8,9,11,10,11,10,11, 9,11, 9,12, 9,12,15,12,15,12,15,12,15,13,15,15,15]
volume2 = [8,4,5,4,6,5,6,4,7,9,7, 5,7, 6,8,8,9,9, 8, 9, 9,10,10,12,11,13,11,14,12, 9,13,10,14,11,15,12,15,13,14,15]

### FUNCTION DEFINITIONS ###

#Function to verify serial communication with the K4H818
K4H818_RESET_GPIO = 19  # BCM numbering - K4H818 reset line on the KHARI PiHat
GPIOCHIP_NAME = 'gpiochip0'  # 'gpiochip4' on Pi 5 -- see note in resetK4H818()
CONNECT_LISTEN_TIMEOUT = 3.0  # seconds to wait for "K4H818READY" after reset

def resetK4H818(ser):
    # PiHat's UART shows up as /dev/ttyAMA0 on some systems, /dev/ttyS0 on
    # others -- depends on whether the Pi's more capable PL011 UART or its
    # "mini UART" ends up assigned to the GPIO header vs Bluetooth. Either
    # name means the same physical connection and needs the same GPIO
    # reset handling, not the PiXX/DTR path.
    if 'ttyAMA' in ser.port or 'ttyS0' in ser.port:
        # KHARI PiHat: K4H818 is wired directly to the Pi's UART, so there's
        # no USB-serial chip and no DTR line. Reset is instead wired to
        # GPIO19 through a 0.1uF coupling cap. This exact sequence (HIGH,
        # settle, LOW, back HIGH) matches k4h818_ama0_fwu.sh, which is
        # proven working with avrdude on this hardware - the falling edge
        # is what creates the reset pulse; the 0.5s pause lets the cap
        # fully charge/settle first.
        #
        # Two different GPIO tools are used depending on what's actually
        # available, detected directly rather than guessed by OS/distro:
        #   - 'gpio' (WiringPi): still shipped and confirmed working on
        #     HamVOIP, so it's preferred whenever it's present.
        #   - libgpiod (Python 'gpiod' module): used as a fallback on
        #     systems where WiringPi has been dropped (e.g. ASL3). Its
        #     Python API changed completely between v1 and v2, and which
        #     one is installed varies by system, so that's also detected
        #     rather than assumed.
        if shutil.which('gpio'):
            r1 = subprocess.call(['gpio', '-g', 'mode', str(K4H818_RESET_GPIO), 'out'])
            r2 = subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '1'])
            time.sleep(0.5)  # let the 0.1uF capacitor settle
            r3 = subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '0'])
            time.sleep(0.1)  # hold LOW long enough to register as a real pulse
            r4 = subprocess.call(['gpio', '-g', 'write', str(K4H818_RESET_GPIO), '1'])
            if r1 != 0 or r2 != 0 or r3 != 0 or r4 != 0:
                print("WARNING: 'gpio' command reported an error -- the K4H818 may not")
                print("have actually been reset. This often means a permissions issue")
                print("(GPIO access usually needs root or 'gpio' group membership) --")
                print("try running with sudo.\n")
        else:
            import gpiod
            # '/dev/gpiochip0' is correct on the Pi 3/4/5 (Pi 5's RP1
            # southbridge still exposes it as a BCM-numbering compatibility
            # layer) -- if this fails to find GPIO19, run 'gpiodetect' to
            # find the right chip name for this board and update
            # GPIOCHIP_NAME below.
            try:
                if hasattr(gpiod, 'LINE_REQ_DIR_OUT'):
                    # v1 API
                    chip = gpiod.Chip('/dev/' + GPIOCHIP_NAME)
                    reset_line = chip.get_line(K4H818_RESET_GPIO)
                    reset_line.request(consumer="K4H818-prog", type=gpiod.LINE_REQ_DIR_OUT)
                    reset_line.set_value(1)
                    time.sleep(0.5)  # let the 0.1uF capacitor settle
                    reset_line.set_value(0)
                    time.sleep(0.1)  # hold LOW long enough to register as a real pulse
                    reset_line.set_value(1)
                    reset_line.release()
                    chip.close()
                else:
                    # v2 API
                    from gpiod.line import Direction, Value
                    with gpiod.request_lines(
                        '/dev/' + GPIOCHIP_NAME,
                        consumer="K4H818-prog",
                        config={
                            K4H818_RESET_GPIO: gpiod.LineSettings(
                                direction=Direction.OUTPUT, output_value=Value.ACTIVE
                            )
                        },
                    ) as request:
                        time.sleep(0.5)  # let the 0.1uF capacitor settle
                        request.set_value(K4H818_RESET_GPIO, Value.INACTIVE)
                        time.sleep(0.1)  # hold LOW long enough to register as a real pulse
                        request.set_value(K4H818_RESET_GPIO, Value.ACTIVE)
            except Exception as e:
                print("WARNING: GPIO reset failed (" + str(e) + ") -- the K4H818 may")
                print("not have actually been reset. This often means a permissions")
                print("issue (GPIO access usually needs root or 'gpio' group")
                print("membership) -- try running with sudo.\n")
    else:
        # KHARI PiXX: K4H818 reached via a USB-serial chip on ttyUSB0 -
        # reset via DTR. Matches the same settle-time principle as the
        # GPIO path above -- if this adapter's DTR-to-reset circuit is
        # also capacitor-coupled (a common design), toggling with zero
        # dwell time between transitions may not reliably generate a
        # clean reset pulse every time.
        ser.setDTR(True)
        time.sleep(0.5)
        ser.setDTR(False)
        time.sleep(0.1)
        ser.setDTR(True)


def connectAndListen(ser, ackCommand, listenTimeout=CONNECT_LISTEN_TIMEOUT):
    # Resets the K4H818 and passively listens for its one-time
    # "K4H818READY" ready ping, then sends ackCommand and confirms
    # COMMOK. No active polling/retrying -- the firmware only ever
    # announces readiness once, right after Serial.begin(), before
    # doing any slow chip initialization, and only waits 500ms for a
    # response before moving on to normal operation. Repeatedly
    # resending a command (the old approach) risked exactly the
    # connection failure this redesign fixes: multiple queued replies
    # arriving as one unparseable blob.
    #
    # listenTimeout allows for the reset pulse/settle time, AVR boot
    # time, and the firmware's own 500ms decision window -- generous on
    # purpose since missing the one-shot ready ping means waiting for
    # an entirely new reset cycle.
    is_dtr_path = not ('ttyAMA' in ser.port or 'ttyS0' in ser.port)

    if is_dtr_path:
        # PiXX/DTR: opening a serial port implicitly toggles DTR --
        # well-documented pyserial/OS behavior, confirmed even with
        # dsrdtr=False explicitly set (a known, still-unresolved
        # pyserial limitation). That means the device's ORIGINAL
        # port-open (earlier in the script, well before this function
        # is ever called) already triggered a real reset -- but at an
        # uncontrolled moment, with unpredictable delay before we
        # actually start listening here. Confirmed on real hardware:
        # by the time this function's own listen loop started, that
        # earlier reset's "K4H818READY" had already been sent and its
        # 500ms window had already closed, with nobody listening yet.
        #
        # Fix: close and re-open the port right here, immediately
        # before listening -- this triggers a FRESH implicit reset at
        # a precisely controlled moment, with no gap before we start
        # watching for its result. No explicit resetK4H818() call is
        # needed (or wanted) on this path -- calling it in addition to
        # this would just reintroduce the original double-reset
        # collision this whole fix was for.
        ser.close()
        ser.open()
        if verboseMode:
            print("DIAG: closed and re-opened port to trigger a freshly-timed implicit reset (PiXX/DTR)")
    else:
        # PiHat/GPIO: unrelated to DTR, resets normally.
        resetK4H818(ser)

    ser.reset_input_buffer()
    connect_t0 = time.time()

    raw_bytes = bytearray()
    start_time = time.time()
    while time.time() - start_time < listenTimeout:
        n = ser.in_waiting
        if n > 0:
            chunk = ser.read(n)
            if verboseMode:
                t = time.time() - connect_t0
                print("DIAG: t=" + "{:.3f}".format(t) + "s received " + str(len(chunk)) +
                      " bytes: " + repr(chunk))
            # Strip stray null bytes before line-parsing -- observed on a
            # real Pi (first run after a reboot): a null byte arrived
            # embedded mid-line (e.g. b'K\x004H818READY\r\n'), which
            # survives decode()/strip() invisibly in a terminal, so the
            # printed RECEIVED line looked correct while the actual
            # string never matched. The raw chunk above still shows
            # exactly what arrived, unfiltered, for diagnosis.
            raw_bytes.extend(chunk.replace(b'\x00', b''))
            while b'\n' in raw_bytes:
                idx = raw_bytes.index(b'\n')
                line_bytes = bytes(raw_bytes[:idx+1])
                del raw_bytes[:idx+1]
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if verboseMode:
                    print("RECEIVED: '" + line + "'")
                if line == "K4H818READY":
                    ser.write((ackCommand + '\n').encode('utf-8'))
                    ser.flush()
                    ack_start = time.time()
                    while time.time() - ack_start < 1.0:
                        if ser.in_waiting > 0:
                            ack_response = ser.readline().decode('utf-8', errors='ignore').strip()
                            if verboseMode:
                                print("ACK RESPONSE: '" + ack_response + "'")
                            if ack_response == "COMMOK":
                                return True
                            break
                    print("No COMMOK response from the K4H818 after sending " + ackCommand)
                    return False

    if verboseMode:
        print("DIAG: leftover unterminated bytes at timeout: " + repr(raw_bytes))
    print("No K4H818READY response from the K4H818 within " + str(listenTimeout) + " seconds.")
    return False

#Install a signal handler so that the user can cancel by pressing Ctl+C
def sigterm_handler(_signo, _stack_frame):
  # AT+97 (Ctrl-C abort) no longer exists -- exiting a config session,
  # cleanly or otherwise, is always a real hardware reset now. Whatever
  # was already written to EEPROM before this point stays written,
  # same as before -- only the restart mechanism changed.
  resetK4H818(ser)
  print ('\n')
  print ('------------------------------------------------------')
  print("You terminated the program. Exiting now.")
  print ('------------------------------------------------------')
  print ('')
  exit()

signal.signal(signal.SIGINT, sigterm_handler)

# Ignore Ctrl-Z (SIGTSTP) entirely -- suspending mid-wizard would leave
# the serial connection open but unresponsive. Ctrl-C remains the only
# way to exit. hasattr guard since SIGTSTP doesn't exist on all platforms.
if hasattr(signal, 'SIGTSTP'):
  signal.signal(signal.SIGTSTP, signal.SIG_IGN)

#Function to help convert back and forth from bitstrings
def writeSerial(ser, string):
  ser.write((string + CRLF).encode())
  time.sleep(.05)
  raw_serial = ser.readline()
  cleaned = raw_serial.rstrip(b'\r\n').decode(errors='ignore')
  return cleaned

#Like writeSerial(), but also reads the follow-up OK/FAIL line the firmware
#sends specifically for AT+01 and AT+94, since a TX frequency can be
#rejected if it's out of band for this unit's installed LPF. Returns
#(echoed_command, ack) where ack is "OK" or "FAIL".
def writeSerialFreq(ser, string):
  ser.write((string + CRLF).encode())
  time.sleep(.05)
  raw_serial = ser.readline()
  cleaned = raw_serial.rstrip(b'\r\n').decode(errors='ignore')
  time.sleep(.05)
  ack_raw = ser.readline()
  ack = ack_raw.rstrip(b'\r\n').decode(errors='ignore')
  return cleaned, ack

#Send a command during the programming phase. By default (no -v flag) this
#prints a '+' progress tick instead of the full command/response text --
#pass -v on the command line to see every command sent, as before.
# No separate band question -- frequency is validated directly against
# whichever of the three ham bands it falls in.
HAM_BANDS = [(144, 148), (222, 225), (420, 450)]

def in_valid_ham_band(freq_mhz):
  return any(lo <= freq_mhz <= hi for lo, hi in HAM_BANDS)

def ham_band_range_text():
  return ', '.join('{0:.3f}-{1:.3f}'.format(lo, hi) for lo, hi in HAM_BANDS)

def sendCmd(ser, command):
  response = writeSerial(ser, command)
  if verboseMode:
    print(" Command Sent:")
    print("    " + command + "\n")
  else:
    print('+', end='', flush=True)
  return response

#Same as sendCmd, but for the two commands (AT+01, AT+94) that get a
#follow-up OK/FAIL ack line.
def sendCmdFreq(ser, command):
  response, ack = writeSerialFreq(ser, command)
  if verboseMode:
    print(" Command Sent:")
    print("    " + command + "\n")
  else:
    print('+', end='', flush=True)
  return response, ack

#Python 3 only
def my_input(prompt):
  return input(prompt).strip()

# Function to prompt for y/n answer, showing the real current state.
# Enter keeps whatever is currently set -- it does NOT default to 'y'.
def yesNoPrompt(prop, current_enabled):
  current_str = 'y' if current_enabled else 'n'
  while True:
    val=my_input('Enable ' + prop + ' (current: ' + current_str + ') [y/n, Enter to keep]: ').lower()
    if val == '':
      val = current_str
    if val == 'y':
      print('\t' + prop + ' is enabled\n')
      break
    if val == 'n':
      print('\t' + prop + ' is not enabled\n')
      break
    else:
      print("Must enter Y or N")
  return val

#Reverse lookup: raw stored volume1/volume2 register values back to the
#friendly 0-39 RX Volume number the wizard actually asks for. Every
#(volume1[i], volume2[i]) pair across all 40 indices is unique, confirmed
#by direct check, so this is a reliable exact match, not a guess.
def volumeIndexFromRegisters(v1, v2):
  for i in range(40):
    if volume1[i] == v1 and volume2[i] == v2:
      return i
  return None

#Reverse lookup: raw CDCSS hex code (as stored by the firmware) back to the
#friendly 3-digit code shown in dcs_codes. The wizard always sends
#dcs_normal[i] regardless of polarity -- polarity is tracked separately
#(TXnormalCDCSS/RXnormalCDCSS) -- so only dcs_normal needs searching here.
def dcsCodeToString(raw_code):
  for i in range(83):
    if dcs_normal[i] == raw_code:
      return dcs_codes[i]
  return '???'

#Read the firmware version (AT+98). Same two-line pattern as readConfig:
#the shared echo comes first, then the actual version string.
def readFwVersion(ser):
  echoed = writeSerial(ser, "AT+98,")
  time.sleep(.05)
  raw_serial = ser.readline()
  return raw_serial.rstrip(b'\r\n').decode(errors='ignore')

#Read the K4H818's entire live configuration in one AT+93 round trip.
#Field order matches CommandProcessor.cpp's AT+93 handler exactly.
def readConfig(ser):
  echoed = writeSerial(ser, "AT+93,")  # reads/discards the shared echo line
  time.sleep(.05)
  raw_serial = ser.readline()          # the actual comma-separated data line
  response = raw_serial.rstrip(b'\r\n').decode(errors='ignore')
  fields = response.split(',')
  if len(fields) < 21:
    print("Error: AT+93 response from the K4H818 was incomplete or empty.")
    print("Expected 21 comma-separated fields, got: '" + response + "'")
    print("This usually means a serial timing issue -- try again.\n")
    resetK4H818(ser)
    exit()
  cfg = {}
  cfg['txFreq']         = int(fields[0])
  cfg['rxFreq']         = int(fields[1])
  cfg['txCTCSS']        = int(fields[2])
  cfg['rxCTCSS']        = int(fields[3])
  cfg['rfPower']        = int(fields[4])
  cfg['volume1']        = int(fields[5])
  cfg['volume2']        = int(fields[6])
  cfg['squelch']        = int(fields[7])
  cfg['txcssType']      = int(fields[8])
  cfg['rxcssType']      = int(fields[9])
  cfg['bypassRSSIlpf']  = int(fields[10])
  cfg['txCDCSScode']    = int(fields[11])
  cfg['rxCDCSScode']    = int(fields[12])
  cfg['TXnormalCDCSS']  = int(fields[13])
  cfg['RXnormalCDCSS']  = int(fields[14])
  cfg['bypassPreDe']    = int(fields[15])
  cfg['bypassVoiceHPF'] = int(fields[16])
  cfg['bypassVoiceLPF'] = int(fields[17])
  cfg['bypassCtcssLPF'] = int(fields[18])
  cfg['bypassCtcssHPF'] = int(fields[19])
  cfg['txGainNibble']   = int(fields[20])
  return cfg

#Print a human-readable summary of a config dict returned by readConfig().
def printConfigSummary(cfg, fwVersion, title='Current configuration read from the K4H818:'):
  print('------------------------------------------------------')
  print(title)
  print('')
  print('             Firmware Version: ' + fwVersion)
  print('                 Tx Frequency: ' + '{0:.3f}'.format(cfg['txFreq']/1000) + ' MHz')
  print('                 Rx Frequency: ' + '{0:.3f}'.format(cfg['rxFreq']/1000) + ' MHz')
  print('          Tx Sub-audible Type: ' + subaud_tone_type[cfg['txcssType']])
  if cfg['txcssType'] in (1, 3):
    print('           Tx CTCSS Frequency: ' + '{0:.1f}'.format(cfg['txCTCSS']/100) + ' Hz')
  if cfg['txcssType'] in (2, 4):
    print('                  Tx DCS Code: ' + dcsCodeToString(cfg['txCDCSScode']) + (' Inverted' if cfg['TXnormalCDCSS'] else ' Normal'))
  print('          Rx Sub-audible Type: ' + subaud_tone_type[cfg['rxcssType']])
  if cfg['rxcssType'] in (1, 3):
    print('           Rx CTCSS Frequency: ' + '{0:.1f}'.format(cfg['rxCTCSS']/100) + ' Hz')
  if cfg['rxcssType'] in (2, 4):
    print('                  Rx DCS Code: ' + dcsCodeToString(cfg['rxCDCSScode']) + (' Inverted' if cfg['RXnormalCDCSS'] else ' Normal'))
  print('                Squelch Value: ' + str(cfg['squelch']))
  if expertMode:
    print('       RX Volume (raw values): ' + str(cfg['volume1']) + ', ' + str(cfg['volume2']))
  else:
    volIdx = volumeIndexFromRegisters(cfg['volume1'], cfg['volume2'])
    if volIdx is not None:
      print('                    RX Volume: ' + str(volIdx))
    else:
      # Shouldn't happen -- every valid volume1/volume2 pair from the 0-39
      # table is accounted for. Fall back to raw values so nothing's hidden.
      print('       RX Volume (raw values): ' + str(cfg['volume1']) + ', ' + str(cfg['volume2']))
  if expertMode:
    print('                     TX Gain: ' + str(cfg['txGainNibble']))
  print('      Pre/De-Emphasis Enabled: ' + ('n' if cfg['bypassPreDe'] else 'y'))
  print('      Voice High Pass Enabled: ' + ('n' if cfg['bypassVoiceHPF'] else 'y'))
  print('       Voice Low Pass Enabled: ' + ('n' if cfg['bypassVoiceLPF'] else 'y'))
  print('CTCSS/CDCSS High Pass Enabled: ' + ('n' if cfg['bypassCtcssHPF'] else 'y'))
  print(' CTCSS/CDCSS Low Pass Enabled: ' + ('n' if cfg['bypassCtcssLPF'] else 'y'))
  print(' RSSI Low Pass Filter Enabled: ' + ('n' if cfg['bypassRSSIlpf'] else 'y'))
  print('------------------------------------------------------')
  print('')

# Sends the complete AT+ programming sequence for a full configuration,
# ending in a real hardware reset. Takes a dict shaped exactly like readConfig()'s
# output (same field names, same types) -- so re-sending the device's
# own current config is just programRadio(ser, liveConfig).
#
# Returns True on success. On failure, prints an explanation and
# returns False -- callers decide whether to exit or try something else.
def _programRadioInner(ser, cfg):
  print("Programming the K4H818 ", end='', flush=True)

  command = "AT+01," + str(cfg['txFreq'])
  response, ack = sendCmdFreq(ser, command)
  if response != command:
    print()
    print("    Transmit frequency (" + response + ")...")
    return False
  if ack != "OK":
    print()
    print("    " + '{0:.3f}'.format(cfg['txFreq']/1000) + " MHz was rejected by the K4H818 -- it's not in a valid ham band")
    print("    for this unit's installed low-pass filter. Check the frequency and try again.\n")
    return False

  command = "AT+05," + str(cfg['rxFreq'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Receive frequency (" + response + ")...")
    return False

  if cfg['txcssType'] in (1, 3):
    command = "AT+09," + str(cfg['txCTCSS'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("    " + command + "\n")
      return False

  if cfg['rxcssType'] in (1, 3):
    command = "AT+11," + str(cfg['rxCTCSS'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("    " + command + "\n")
      return False

  command = "AT+14," + str(cfg['volume1'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Volume1 setting (" + response + ")...")
    return False

  command = "AT+15," + str(cfg['volume2'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Volume2 setting (" + response + ")...")
    return False

  command = "AT+45," + str(cfg['txGainNibble'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    TX gain setting (" + response + ")...")
    return False

  command = "AT+16," + str(cfg['squelch'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Squelch setting (" + response + ")...")
    return False

  command = "AT+20," + str(cfg['txcssType'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Transmit sub-audible tone (" + response + ")...")
    return False

  command = "AT+21," + str(cfg['rxcssType'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Receive sub-audible tone (" + response + ")...")
    return False

  command = "AT+22," + str(cfg['bypassRSSIlpf'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    RSSI low pass filter setting (" + response + ")...")
    return False

  if cfg['txcssType'] in (2, 4):
    command = "AT+24," + str(cfg['txCDCSScode'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("Error: Response did not match command!\n    Expected:" + command + "\n    Received:" + response)
      return False

  if cfg['rxcssType'] in (2, 4):
    command = "AT+28," + str(cfg['rxCDCSScode'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("Error: Response did not match command!\n    Expected:" + command + "\n    Received:" + response)
      return False

  if cfg['txcssType'] in (2, 4):
    command = "AT+32," + str(cfg['TXnormalCDCSS'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("    Transmit DCS code polarity (" + response + ")...")
      return False

  if cfg['rxcssType'] in (2, 4):
    command = "AT+33," + str(cfg['RXnormalCDCSS'])
    response = sendCmd(ser, command)
    if response != command:
      print()
      print("    Receive DCS code polarity (" + response + ")...")
      return False

  command = "AT+40," + str(cfg['bypassPreDe'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Pre/De-emphasis setting (" + response + ")...")
    return False

  command = "AT+41," + str(cfg['bypassVoiceHPF'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Voice High pass filter setting (" + response + ")...")
    return False

  command = "AT+42," + str(cfg['bypassVoiceLPF'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    Voice Low pass filter setting (" + response + ")...")
    return False

  command = "AT+43," + str(cfg['bypassCtcssLPF'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    CTCSS/CDCSS low pass filter setting (" + response + ")...")
    return False

  command = "AT+44," + str(cfg['bypassCtcssHPF'])
  response = sendCmd(ser, command)
  if response != command:
    print()
    print("    CTCSS/CDCSS high pass filter setting (" + response + ")...")
    return False

  print()
  print("Programming Successful\n")
  printConfigSummary(cfg, fwVersion, title='Applied configuration:')
  return True


def programRadio(ser, cfg):
    # Thin wrapper guaranteeing a reset on every exit path from
    # _programRadioInner -- success, or any of its many individual
    # command-send failure returns. Without this, a config session
    # left mid-write (e.g. one AT+ command not acknowledged) would
    # leave the K4H818 stuck in commandSessionForever() indefinitely,
    # since nothing else will ever reset it under the new protocol.
    try:
        return _programRadioInner(ser, cfg)
    finally:
        resetK4H818(ser)


### MAIN PROGRAM STATEMENTS ###

# Reads and validates K4H818.ini, returning a cfg dict shaped exactly
# like readConfig()'s output (ready for programRadio()). Returns None
# and prints an explanation if the file is missing or any field fails
# validation -- same rules the interactive wizard uses for each field.
def readIniConfig(path):
  if not os.path.isfile(path):
    print("\nCould not find " + path)
    print("Create a K4H818.ini in the same folder as this program -- see")
    print("the example K4H818.ini for the required format.\n")
    return None

  raw = {}
  with open(path, 'r') as f:
    for line in f:
      line = line.strip()
      if line == '' or line.startswith(';'):
        continue
      if '=' not in line:
        continue
      key, _, value = line.partition('=')
      raw[key.strip()] = value.strip()

  required = ['txFreq', 'rxFreq', 'txcssType', 'rxcssType', 'squelch',
              'rxVolume', 'bypassPreDe', 'bypassVoiceHPF', 'bypassVoiceLPF',
              'bypassCtcssHPF', 'bypassCtcssLPF', 'bypassRSSIlpf']
  missing = [k for k in required if k not in raw]
  if missing:
    print("\n" + path + " is missing required field(s): " + ', '.join(missing) + "\n")
    return None

  cfg = {}

  try:
    txFreqMhz = float(raw['txFreq'])
    rxFreqMhz = float(raw['rxFreq'])
    if not in_valid_ham_band(txFreqMhz):
      print("\ntxFreq in " + path + " (" + raw['txFreq'] + " MHz) is not within one of: " + ham_band_range_text() + " MHz\n")
      return None
    if not in_valid_ham_band(rxFreqMhz):
      print("\nrxFreq in " + path + " (" + raw['rxFreq'] + " MHz) is not within one of: " + ham_band_range_text() + " MHz\n")
      return None
    cfg['txFreq'] = int(round(txFreqMhz * 1000))
    cfg['rxFreq'] = int(round(rxFreqMhz * 1000))
  except ValueError:
    print("\ntxFreq/rxFreq in " + path + " must be numbers in MHz (xxx.xxx)\n")
    return None

  try:
    txcssType = int(raw['txcssType'])
    rxcssType = int(raw['rxcssType'])
    if txcssType not in (0, 1, 2, 3, 4) or rxcssType not in (0, 1, 2, 3, 4):
      raise ValueError()
    cfg['txcssType'] = txcssType
    cfg['rxcssType'] = rxcssType
  except ValueError:
    print("\ntxcssType/rxcssType in " + path + " must be an integer 0-4\n")
    return None

  cfg['txCTCSS'] = 0
  cfg['rxCTCSS'] = 0
  cfg['txCDCSScode'] = 0
  cfg['rxCDCSScode'] = 0
  cfg['TXnormalCDCSS'] = 0
  cfg['RXnormalCDCSS'] = 0

  if cfg['txcssType'] in (1, 3):
    if 'txCTCSS' not in raw:
      print("\ntxcssType in " + path + " requires a txCTCSS field\n")
      return None
    try:
      cfg['txCTCSS'] = int(round(float(raw['txCTCSS']) * 100))
    except ValueError:
      print("\ntxCTCSS in " + path + " must be a number in Hz\n")
      return None

  if cfg['rxcssType'] in (1, 3):
    if 'rxCTCSS' not in raw:
      print("\nrxcssType in " + path + " requires an rxCTCSS field\n")
      return None
    try:
      cfg['rxCTCSS'] = int(round(float(raw['rxCTCSS']) * 100))
    except ValueError:
      print("\nrxCTCSS in " + path + " must be a number in Hz\n")
      return None

  if cfg['txcssType'] in (2, 4):
    if 'txCDCSScode' not in raw or raw['txCDCSScode'] not in dcs_codes:
      print("\ntxCDCSScode in " + path + " must be a valid 3-digit DCS code\n")
      return None
    cfg['txCDCSScode'] = dcs_normal[dcs_codes.index(raw['txCDCSScode'])]
    if 'txCDCSSpolarity' not in raw or raw['txCDCSSpolarity'].upper() not in ('N', 'I'):
      print("\ntxCDCSSpolarity in " + path + " must be N or I\n")
      return None
    cfg['TXnormalCDCSS'] = 1 if raw['txCDCSSpolarity'].upper() == 'I' else 0

  if cfg['rxcssType'] in (2, 4):
    if 'rxCDCSScode' not in raw or raw['rxCDCSScode'] not in dcs_codes:
      print("\nrxCDCSScode in " + path + " must be a valid 3-digit DCS code\n")
      return None
    cfg['rxCDCSScode'] = dcs_normal[dcs_codes.index(raw['rxCDCSScode'])]
    if 'rxCDCSSpolarity' not in raw or raw['rxCDCSSpolarity'].upper() not in ('N', 'I'):
      print("\nrxCDCSSpolarity in " + path + " must be N or I\n")
      return None
    cfg['RXnormalCDCSS'] = 1 if raw['rxCDCSSpolarity'].upper() == 'I' else 0

  try:
    sq = int(raw['squelch'])
    if sq < 0 or sq > 15:
      raise ValueError()
    cfg['squelch'] = sq
  except ValueError:
    print("\nsquelch in " + path + " must be an integer 0-15\n")
    return None

  try:
    vol = int(raw['rxVolume'])
    if vol < 0 or vol > 39:
      raise ValueError()
    cfg['volume1'] = volume1[vol]
    cfg['volume2'] = volume2[vol]
  except ValueError:
    print("\nrxVolume in " + path + " must be an integer 0-39\n")
    return None

  # Optional, expert-level setting -- defaults to the validated value if
  # not present, so existing .ini files without this field still work.
  if 'txGainNibble' in raw:
    try:
      txg = int(raw['txGainNibble'])
      if txg < 0 or txg > 15:
        raise ValueError()
      cfg['txGainNibble'] = txg
    except ValueError:
      print("\ntxGainNibble in " + path + " must be an integer 0-15\n")
      return None
  else:
    cfg['txGainNibble'] = 0x0B

  for field in ['bypassPreDe', 'bypassVoiceHPF', 'bypassVoiceLPF',
                'bypassCtcssHPF', 'bypassCtcssLPF', 'bypassRSSIlpf']:
    if raw[field].upper() not in ('Y', 'N'):
      print("\n" + field + " in " + path + " must be Y or N\n")
      return None
    cfg[field] = 1 if raw[field].upper() == 'Y' else 0

  return cfg

# configure the serial connections (the parameters differs on the device 
# you are connecting to).  ttyUSB0 is used for SHARI PiXX and K4H818
# ttyAMA0 is used for SHARI PiHat.  Selection is automatic.
device_list = ['/dev/ttyUSB0', '/dev/ttyAMA0', '/dev/ttyS0']
for device in device_list:
  try:
    ser = serial.Serial(
      port=device,
      baudrate=9600,
      parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_ONE,
      bytesize=serial.EIGHTBITS,
      timeout=1
    )
    time.sleep(2)   
  except Exception as e:
    if device == device_list[-1]:
      print ('Could not open any of these serial devices:\n' + '\t\n'.join(device_list) )
      print(e)
      exit()
  else:
    #We found a device that works, just break the loop
    break

# Splash screen
print ('------------------------------------------------------')
print ('')
print ('K4H818-prog, Version ' + prog_ver)
print ('Programing SHARI PiXX / SHARI PiHat / K4H818(U/V) Module')
print ('Programming Device name:')
print ('      ' + ser.portstr)       # show which port was really used
print ('')
print ('------------------------------------------------------')
print ('')

# -r must be checked before the main config-session connect below --
# it needs its own connectAndListen() call with a different ack string
# ("AT+K4H818RSSI" instead of "AT+K4H818CONNECT"), since the firmware
# decides which mode to enter based on which string it receives in
# response to its one-shot ready ping, and each ready ping only ever
# gets sent once per reset.
if '-r' in sys.argv:
  success = connectAndListen(ser, "AT+K4H818RSSI")
  if not success:
    exit()
  print("Monitoring Radio Signal Strength (press Ctl+c to exit)")
  # Passive stream -- the firmware now reports RSSI once a second on
  # its own; nothing is sent to request it.
  while True:
    if ser.in_waiting > 0:
      line = ser.readline().decode('utf-8', errors='ignore').strip()
      if line:
        print(line)

# Check for serial communications with the K4H818

# Reset and passively listen for the ready ping, then request a config session
success = connectAndListen(ser, "AT+K4H818CONNECT")

# You can now branch based on success
if success:
    print("Serial communications with the K4H818 are OK\n")
    liveConfig = readConfig(ser)
    fwVersion = readFwVersion(ser)
    printConfigSummary(liveConfig, fwVersion)
else:
    print("Exiting program due to communication failure")
    exit()

# Reset K4H818 to default values. Invoke this by using K4H818-prog -d to start program
if '-d' in sys.argv:
  print("")
  print("Choose a default configuration to apply:")
  print("  1) Reset EEPROM only -- the K4H818's own built-in defaults")
  print("     will be applied immediately")
  print("  2) 2 meters   (146.540 MHz, CTCSS 100.0 Hz)")
  print("  3) 1.25 meters (223.400 MHz, CTCSS 100.0 Hz)")
  print("  4) 70 cm      (446.100 MHz, CTCSS 100.0 Hz)")
  print("  5) Use K4H818.ini (in the same folder as this program)")
  print("")
  while True:
    dChoice = my_input("Enter choice (1-5): ")
    if dChoice in ('1', '2', '3', '4', '5'):
      break
    print(" Sorry, you must enter a number from 1 to 5\n")

  if dChoice == '1':
    writeSerial(ser, "AT+96,")
    resetK4H818(ser)
    print("\nEEPROM invalidated. The K4H818's own built-in defaults have")
    print("been applied.\n")
    exit()

  # Choices 2-5 all build a complete cfg dict and hand it to the same
  # programRadio() function the interactive wizard uses -- no need to
  # invalidate EEPROM first, since every field gets sent regardless.
  bandProfiles = {
    '2': {'name': '2 meters',    'freqKhz': 146540},
    '3': {'name': '1.25 meters', 'freqKhz': 223400},
    '4': {'name': '70 cm',       'freqKhz': 446100},
  }

  if dChoice in ('2', '3', '4'):
    profile = bandProfiles[dChoice]
    print("\nUsing the " + profile['name'] + " default configuration.\n")
    newCfg = {}
    newCfg['txFreq'] = profile['freqKhz']
    newCfg['rxFreq'] = profile['freqKhz']
    newCfg['txcssType'] = 1
    newCfg['rxcssType'] = 1
    newCfg['txCTCSS'] = 10000
    newCfg['rxCTCSS'] = 10000
    newCfg['txCDCSScode'] = 0
    newCfg['rxCDCSScode'] = 0
    newCfg['TXnormalCDCSS'] = 0
    newCfg['RXnormalCDCSS'] = 0
    newCfg['volume1'] = volume1[30]
    newCfg['volume2'] = volume2[30]
    newCfg['txGainNibble'] = 0x0B
    newCfg['squelch'] = 5
    newCfg['bypassRSSIlpf'] = 0
    newCfg['bypassPreDe'] = 0
    newCfg['bypassVoiceHPF'] = 0
    newCfg['bypassVoiceLPF'] = 0
    newCfg['bypassCtcssLPF'] = 0
    newCfg['bypassCtcssHPF'] = 0
    if not programRadio(ser, newCfg):
      exit()
    exit()

  if dChoice == '5':
    iniPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'K4H818.ini')
    newCfg = readIniConfig(iniPath)
    if newCfg is None:
      resetK4H818(ser)
      exit()
    if not programRadio(ser, newCfg):
      exit()
    exit()

print(CAUTION + "IMPORTANT: the frequency you enter must match this node's" + COLOR_RESET)
print(CAUTION + "installed hardware low-pass filter. Selecting the wrong band" + COLOR_RESET)
print(CAUTION + "can result in no output power or out-of-spec harmonic" + COLOR_RESET)
print(CAUTION + "emissions." + COLOR_RESET + "\n")


# Ask for transmit frequency.  Make sure it is in 2m, 1.25m or 70cm ham band. Correct input format errors
while True:
  raw = my_input('Enter transmit frequency in MHz (xxx.xxx) [current: ' + '{0:.3f}'.format(liveConfig['txFreq']/1000) + ', Enter to keep]: ')
  if raw == '':
    freq = liveConfig['txFreq'] / 1000.0
    if not in_valid_ham_band(freq):
      print(CAUTION + " The current frequency (" + '{0:.3f}'.format(freq) + " MHz) is not in a valid ham band." + COLOR_RESET)
      print(" You must enter a new Tx frequency within one of: " + ham_band_range_text() + " MHz.\n")
      continue
    FreqTxKhz = str(liveConfig['txFreq'])
    FreqTx = '{0:.3f}'.format(freq)
    print(' Keeping the current transmit frequency: ' + FreqTx + ' MHz\n')
    break
  try:
    freq=float(raw)
    if not in_valid_ham_band(freq):
      raise ValueError()
  except ValueError:
      print("The Tx frequency must be entered as (xxx.xxx) and must be within one of: " + ham_band_range_text() + " MHz.\n")
  else:
    #Convert frequency in MHz to frequency in kHz then convert to string
    FreqTxKhz = str(int(freq * 1000))
    # Save string with 3 decimal places
    FreqTx = '{0:.3f}'.format(freq)
    print(' The transmit frequency is ' + FreqTx + ' MHz\n')
    break


# Ask for receive frequency.  Make sure it is in 2m, 1.25m or 70cm ham band. Correct input format errors
while True:
  raw = my_input('Enter receive frequency in MHz (xxx.xxx) [current: ' + '{0:.3f}'.format(liveConfig['rxFreq']/1000) + ', Enter to keep]: ')
  if raw == '':
    freq = liveConfig['rxFreq'] / 1000.0
    if not in_valid_ham_band(freq):
      print(CAUTION + " The current frequency (" + '{0:.3f}'.format(freq) + " MHz) is not in a valid ham band." + COLOR_RESET)
      print(" You must enter a new Rx frequency within one of: " + ham_band_range_text() + " MHz.\n")
      continue
    FreqRxKhz = str(liveConfig['rxFreq'])
    FreqRx = '{0:.3f}'.format(freq)
    print(' Keeping the current receive frequency: ' + FreqRx + ' MHz\n')
    break
  try:
    freq=float(raw)
    if not in_valid_ham_band(freq):
      raise ValueError()
  except ValueError:
      print("The Rx frequency must be entered as (xxx.xxx) and must be within one of: " + ham_band_range_text() + " MHz.\n")
  else:
    #Convert frequency in MHz to frequency in kHz then convert to string
    FreqRxKhz = str(int(freq * 1000))
    # Save string with 3 decimal places
    FreqRx = '{0:.3f}'.format(freq)
    print(' The receive frequency is ' + FreqRx + ' MHz\n')
    break


#Ask if using transmit subaudible tone
while True:
  print('Do you want to use a transmit sub-audible tone?\n')
  print('0 = No Sub-audible tone')
  print('1 = CTCSS')
  print('2 = CDCSS')
  print('3 = CTCSS with squelch tail elimination')
  print('4 = CDCSS with squelch tail elimination\n')
  #print('5 = CTCSS with 120 degrees reverse burst')
  #print('6 = CTCSS with 180 degrees reverse burst')
  #print('7 = CTCSS with 240 degrees reverse burst\n')
  txaudtone = my_input('Enter a number between 0 and 4 [current: ' + str(liveConfig['txcssType']) + ' (' + subaud_tone_type[liveConfig['txcssType']] + '), Enter to keep]: ')
  if txaudtone == '':
    txaudtone = str(liveConfig['txcssType'])
    print(" Keeping current: " + subaud_tone_type[liveConfig['txcssType']] + "\n")
    break
  if txaudtone == '0':
    print(" You chose no transmit sub-audible tone\n")
    break 
  elif txaudtone == '1':
    print(" You chose CTCSS\n")
    break 
  elif txaudtone == '2':
    print(" You chose CDCSS\n")
    break 
  elif txaudtone == '3':
    print(" CTCSS with squelch tail elimination\n")
    break 
  elif txaudtone == '4':
    print(" CDCSS with squelch tail elimination\n")
    break 
  #elif txaudtone == '5':
  # print(" CTCSS with 120 degrees reverse burst\n")
  # break 
  #elif txaudtone == '6':
  # print(" CTCSS with 180 degrees reverse burst\n")
  # break
  #elif txaudtone == '7':
  # print(" CTCSS with 240 degrees reverse burst\n")
  # break
  else:
    print(" Sorry, you must enter either 0, 1, 2, 3 or 4\n")

#Ask if using receive subaudible tone
while True:
  print('Do you want to use a receive sub-audible tone?\n')
  print('0 = No Sub-audible tone')
  print('1 = CTCSS')
  print('2 = CDCSS')
  print('3 = CTCSS with squelch tail elimination')
  print('4 = CDCSS with squelch tail elimination\n')
    #print('5 = CTCSS with 120 degrees reverse burst')
  #print('6 = CTCSS with 180 degrees reverse burst')
  #print('7= CTCSS with 240 degrees reverse burst')
  rxaudtone = my_input('Enter a number between 0 and 4 [current: ' + str(liveConfig['rxcssType']) + ' (' + subaud_tone_type[liveConfig['rxcssType']] + '), Enter to keep]: ')
  if rxaudtone == '':
    rxaudtone = str(liveConfig['rxcssType'])
    print(" Keeping current: " + subaud_tone_type[liveConfig['rxcssType']] + "\n")
    break
  if rxaudtone == '0':
    print(" You chose no receive sub-audible tone\n")
    break 
  elif rxaudtone == '1':
    print(" You chose CTCSS\n")
    break 
  elif rxaudtone == '2':
    print(" You chose CDCSS\n")
    break 
  elif rxaudtone == '3':
    print(" CTCSS with squelch tail elimination\n")
    break 
  elif rxaudtone == '4':
    print(" CDCSS with squelch tail elimination\n")
    break 
  #elif rxaudtone == '4':
  #  print(" CTCSS with 120 degrees reverse burst\n")
  #  break 
  #elif rxaudtone == '5':
  #  print(" CTCSS with 180 degrees reverse burst\n")
  #  break
  #elif rxaudtone == '6':
  #  print(" CTCSS with 240 degrees reverse burst\n")
  #  break
  else:
    print(" Sorry, you must enter either 0, 1, 2, 3 or 4\n")

#CTCSS options
if txaudtone in ('1', '3'):
  while True:
    raw = my_input('Enter Tx CTCSS Frequency in Hz(xxx.x) [current: ' + '{0:.1f}'.format(liveConfig['txCTCSS']/100) + ', Enter to keep]: ')
    if raw == '':
      txctcss = '{0:.1f}'.format(liveConfig['txCTCSS']/100)
      tx_ctcss = codelookup.get(txctcss, '????')
      txctcssX100 = str(liveConfig['txCTCSS'])
      print(' Keeping current Tx CTCSS: ' + txctcss + ' Hz\n')
      break
    txctcss = raw
    if txctcss in codelookup:
      print(' You entered ' + txctcss + ' Hz') 
      tx_ctcss = codelookup[txctcss]
      print(' The Tx CTCSS code is ' + tx_ctcss + '\n')
      #Convert TX CTCSS frequency in Hz to frequency times 100, then convert to string
      txctcssX100 = (txctcss.replace(".","") + '0')
      break
    else:
      print(" Tx CTCSS frequency is incorrect, please re-enter\n")

if rxaudtone in ('1', '3'):  
  while True:
    raw = my_input('Enter Rx CTCSS Frequency in Hz(xxx.x) [current: ' + '{0:.1f}'.format(liveConfig['rxCTCSS']/100) + ', Enter to keep]: ')
    if raw == '':
      rxctcss = '{0:.1f}'.format(liveConfig['rxCTCSS']/100)
      rx_ctcss = codelookup.get(rxctcss, '????')
      rxctcssX100 = str(liveConfig['rxCTCSS'])
      print(' Keeping current Rx CTCSS: ' + rxctcss + ' Hz\n')
      break
    rxctcss = raw
    if rxctcss in codelookup:
      print(' You entered ' + rxctcss + ' Hz') 
      rx_ctcss = codelookup[rxctcss]
      print(' The Rx CTCSS code is ' + rx_ctcss + '\n')
      #Convert RX CTCSS frequency in Hz to frequency times 100, then convert to string
      rxctcssX100 = (rxctcss.replace(".","") + '0')
      break
    else:
      print(" Rx CTCSS frequency is incorrect, please re-enter\n")

#DCS options
if txaudtone in ('2', '4') or rxaudtone in ('2', '4'):
  while True:
    ans = my_input('Would you like a list of valid DCS codes? (y/[n]): ').lower() or 'n'
    if ans == "y":
      print('\nA valid DCS code is three digits as shown in the following table:\n')
      line = ""
      for i, code in enumerate(dcs_codes):
        line += "{:>3} ".format(code)  # Add each code to the line
        if i % 8 == 7:  # Break line after every 8 codes
          print(line)  # Print the current line
          line = ""    # Reset the line
      if line:  # Print any remaining codes
        print(line)
      print("")  # Final newline for neatness
      break
    elif ans == "n":
      break
    else:
      print("Please enter 'y' for yes or 'n' for no.")

if txaudtone in ('2', '4'):
    while True:
        raw = my_input('\n\nEnter Transmit DCS Code (xxx) [current: ' + dcsCodeToString(liveConfig['txCDCSScode']) + ', Enter to keep]: ').upper()
        if raw == '':
            tx_dcs = dcsCodeToString(liveConfig['txCDCSScode'])
            print('    Keeping current: ' + tx_dcs + '\n')
            break
        tx_dcs = raw
        if len(tx_dcs) == 3 and tx_dcs in dcs_codes:
            print('    You entered ' + tx_dcs + '\n')
            break
        else:
            print('    Code is incorrect')
            print('    Please re-enter as three digits')
      
if txaudtone in ('2', '4'): 
  while True:
    raw = my_input('Enter polarity of the transmit DCS code (Normal = N, Inverted = I) [current: ' + ('I (Inverted)' if liveConfig['TXnormalCDCSS'] else 'N (Normal)') + ', Enter to keep]: ').upper()
    if raw == '':
      tx_dcs_polarity = str(liveConfig['TXnormalCDCSS'])
      print(' Keeping current: ' + ('Inverted' if liveConfig['TXnormalCDCSS'] else 'Normal') + '\n')
      tx_CDCSS_polarity_text = (' Inverted' if liveConfig['TXnormalCDCSS'] else ' Normal')
      break
    if raw == 'N':
      print(" You chose Normal")
      print('')
      tx_dcs_polarity = '0'
      tx_CDCSS_polarity_text = (' Normal')
      break 
    elif raw == 'I':
      print(" You chose Inverted")
      print('')
      tx_dcs_polarity = '1'
      tx_CDCSS_polarity_text = (' Inverted')
      break 
    else:
      print(" Sorry, you must enter either N or I\n")

if rxaudtone in ('2', '4'):
  while True: 
    raw = my_input('Enter Receive DCS Code (xxx) [current: ' + dcsCodeToString(liveConfig['rxCDCSScode']) + ', Enter to keep]: ').upper()
    if raw == '':
      rx_dcs = dcsCodeToString(liveConfig['rxCDCSScode'])
      print(' Keeping current: ' + rx_dcs + '\n')
      break
    rx_dcs = raw
    if len(rx_dcs) == 3 and rx_dcs in dcs_codes:
      print(' You entered ' + rx_dcs + '\n')
      break
    else:
      print(' Code is incorrect')
      print(' Please re-enter as three digits ')

if rxaudtone in ('2', '4'): 
  while True:
    raw = my_input('Enter polarity of the receive DCS code (Normal = N, Inverted = I) [current: ' + ('I (Inverted)' if liveConfig['RXnormalCDCSS'] else 'N (Normal)') + ', Enter to keep]: ').upper()
    if raw == '':
      rx_dcs_polarity = str(liveConfig['RXnormalCDCSS'])
      print(' Keeping current: ' + ('Inverted' if liveConfig['RXnormalCDCSS'] else 'Normal') + '\n')
      rx_CDCSS_polarity_text = (' Inverted' if liveConfig['RXnormalCDCSS'] else ' Normal')
      break
    if raw == 'N':
      print(" You chose Normal")
      print('')
      rx_dcs_polarity = '0'
      rx_CDCSS_polarity_text = (' Normal')
      break 
    elif raw == 'I':
      print(" You chose Inverted")
      print('')
      rx_dcs_polarity = '1'
      rx_CDCSS_polarity_text = (' Inverted')
      break 
    else:
      print(" Sorry, you must enter either N or I\n")

# Enter squelch value (0-15)
while True:
  raw = my_input('Enter Squelch Value (0-15) [current: ' + str(liveConfig['squelch']) + ', Enter to keep]: ')
  if raw == '':
    squelch = str(liveConfig['squelch'])
    print(" Keeping current squelch: " + squelch + "\n")
    break
  try:
    sq=int(raw)
    if sq < 0 or sq > 15:    
      raise ValueError()
  except ValueError:
    print(" Squelch must be an integer between 0 and 15\n")
  else:
    squelch = str(sq)
    print(" Squelch is set to " + squelch + "\n")
    break

# Enter RX volume value -- either as a single friendly 0-39 index (normal
# mode) or as raw volume1 (RX analog gain, AT+14) / volume2 (RX DSP gain,
# AT+15) directly, each 0-15 (expert mode, -e).
if expertMode:
  while True:
    raw = my_input('Enter RX analog gain, Volume1 (0-15) [current: ' + str(liveConfig['volume1']) + ', Enter to keep]: ')
    if raw == '':
      vol1 = liveConfig['volume1']
      print(" Keeping current RX analog gain: " + str(vol1) + "\n")
      break
    try:
      vol1 = int(raw)
      if vol1 < 0 or vol1 > 15:
        raise ValueError()
    except ValueError:
      print(" Volume1 must be an integer between 0 and 15\n")
    else:
      print(" RX analog gain (Volume1) is set to " + str(vol1) + "\n")
      break
  while True:
    raw = my_input('Enter RX DSP gain, Volume2 (0-15) [current: ' + str(liveConfig['volume2']) + ', Enter to keep]: ')
    if raw == '':
      vol2 = liveConfig['volume2']
      print(" Keeping current RX DSP gain: " + str(vol2) + "\n")
      break
    try:
      vol2 = int(raw)
      if vol2 < 0 or vol2 > 15:
        raise ValueError()
    except ValueError:
      print(" Volume2 must be an integer between 0 and 15\n")
    else:
      print(" RX DSP gain (Volume2) is set to " + str(vol2) + "\n")
      break
  while True:
    raw = my_input('Enter TX gain, register 44H[11:8] (0-15) [current: ' + str(liveConfig['txGainNibble']) + ', Enter to keep]: ')
    if raw == '':
      txGain = liveConfig['txGainNibble']
      print(" Keeping current TX gain: " + str(txGain) + "\n")
      break
    try:
      txGain = int(raw)
      if txGain < 0 or txGain > 15:
        raise ValueError()
    except ValueError:
      print(" TX gain must be an integer between 0 and 15\n")
    else:
      print(" TX gain is set to " + str(txGain) + "\n")
      break
  vol_44vol1 = str(vol1)
  vol_44vol2 = str(vol2)
  rxVolume = str(vol1) + ", " + str(vol2) + " (raw Volume1, Volume2)"
else:
  currentVolIdx = volumeIndexFromRegisters(liveConfig['volume1'], liveConfig['volume2'])
  while True:
    raw = my_input('Enter RX Volume (0-39) [current: ' + (str(currentVolIdx) if currentVolIdx is not None else 'unknown') + ', Enter to keep]: ')
    if raw == '' and currentVolIdx is not None:
      vol = currentVolIdx
      rxVolume = str(vol)
      print(" Keeping current RX Volume: " + rxVolume + "\n")
      vol_44vol1 = str(volume1[vol])
      vol_44vol2 = str(volume2[vol])
      break
    try:
      vol=int(raw)
      if vol < 0 or vol > 39:
        raise ValueError()
    except ValueError:
      print(" Volume must be an integer between 0 and 39\n")
    else:
      rxVolume = str(vol)
      print(" RX Volume is set to " + rxVolume )
      print('')
      # Assign string variables
      vol_44vol1 = str(volume1[vol])
      vol_44vol2 = str(volume2[vol])
      break
  txGain = liveConfig['txGainNibble']  # expert-mode-only setting -- not asked here, just preserved

# Ask about pre-emphasis
PreEmphasis = yesNoPrompt("Pre/De-Emphasis", liveConfig['bypassPreDe'] == 0)

# Ask about voice high pass filter
VoiceHighPass = yesNoPrompt("Voice High Pass Filter", liveConfig['bypassVoiceHPF'] == 0)

# Ask about voice low pass filter
VoiceLowPass = yesNoPrompt("Voice Low Pass Filter", liveConfig['bypassVoiceLPF'] == 0)

# Ask about CTCSS/CDCSS high pass filter
CSSHighPass = yesNoPrompt("CTCSS/CDCSS High Pass Filter", liveConfig['bypassCtcssHPF'] == 0)

# Ask about CTCSS/CDCSS low pass filter
CSSLowPass = yesNoPrompt("CTCSS/CDCSS Low Pass Filter", liveConfig['bypassCtcssLPF'] == 0)

# Ask about RSSI low pass filter
rssiLPF = yesNoPrompt("RSSI Low Pass Filter", liveConfig['bypassRSSIlpf'] == 0)

# Format the outputs

if txaudtone == '0':
  txaudText = '   No transmit sub-audible tone\n'
if rxaudtone == '0':
  rxaudText = '    No receive sub-audible tone\n'

if txaudtone in ('1', '3'):
  txaudText = ('          Transmit CTCSS code: ' + tx_ctcss + ' Frequency: ' + txctcss + ' Hz\n')
if rxaudtone in ('1', '3'):
  rxaudText = ('           Receive CTCSS code: ' + rx_ctcss + ' Frequency: ' + rxctcss + ' Hz\n')
  
if txaudtone in ('2', '4'):
  txaudText = ('          Transmit CDCSS code: ' + tx_dcs + tx_CDCSS_polarity_text + '\n')
if rxaudtone in ('2', '4'):
  rxaudText = ('           Receive CDCSS code: ' + rx_dcs + rx_CDCSS_polarity_text + '\n')


prettyText = ('------------------------------------------------------\n'
'                 Tx Frequency: ' + FreqTx + '\n'
'                 Rx Frequency: ' + FreqRx + '\n'
'          Tx Sub-audible Type: ' + subaud_tone_type[int(txaudtone)] + '\n'
+ txaudText +
'          Rx Sub-audible Type: ' + subaud_tone_type[int(rxaudtone)] + '\n'
+ rxaudText +
'                Squelch Value: ' + squelch + '\n'
'                    RX Volume: ' + rxVolume + '\n'
'      Pre/De-Emphasis Enabled: ' + PreEmphasis + '\n'
'      Voice High Pass Enabled: ' + VoiceHighPass + '\n'
'       Voice Low Pass Enabled: ' + VoiceLowPass + '\n'
'CTCSS/CDCSS High Pass Enabled: ' + CSSHighPass + '\n'
' CTCSS/CDCSS Low Pass Enabled: ' + CSSLowPass + '\n'
' RSSI Low Pass Filter Enabled: ' + rssiLPF + '\n'
'------------------------------------------------------\n')

# Ask if the values are correct and whether to program the unit
print ('\nVerify:')
print (prettyText)
Answer=my_input('Is this correct ([y]/n) ?').lower() or 'y'

if Answer == 'y':
  print

if Answer == 'n':
  resetK4H818(ser)
  print
  print('Press the <UP-ARROW> and <enter> on your keyboard to re-run the program')
  print
  exit()

# Build a cfg dict, shaped exactly like readConfig()'s output, from
# everything the wizard collected above, then hand it to the one
# shared function that actually does the programming.
newCfg = {}
newCfg['txFreq'] = int(FreqTxKhz)
newCfg['rxFreq'] = int(FreqRxKhz)
newCfg['txcssType'] = int(txaudtone)
newCfg['rxcssType'] = int(rxaudtone)
newCfg['txCTCSS'] = int(txctcssX100) if txaudtone in ('1', '3') else 0
newCfg['rxCTCSS'] = int(rxctcssX100) if rxaudtone in ('1', '3') else 0
if txaudtone in ('2', '4'):
  for i in range(83):
    if dcs_codes[i] == tx_dcs:
      break
  newCfg['txCDCSScode'] = dcs_normal[i]
else:
  newCfg['txCDCSScode'] = 0
if rxaudtone in ('2', '4'):
  for i in range(83):
    if dcs_codes[i] == rx_dcs:
      break
  newCfg['rxCDCSScode'] = dcs_normal[i]
else:
  newCfg['rxCDCSScode'] = 0
newCfg['TXnormalCDCSS'] = int(tx_dcs_polarity) if txaudtone in ('2', '4') else 0
newCfg['RXnormalCDCSS'] = int(rx_dcs_polarity) if rxaudtone in ('2', '4') else 0
newCfg['volume1'] = int(vol_44vol1)
newCfg['volume2'] = int(vol_44vol2)
newCfg['txGainNibble'] = txGain
newCfg['squelch'] = int(squelch)
newCfg['bypassRSSIlpf'] = 0 if rssiLPF == 'y' else 1
newCfg['bypassPreDe'] = 0 if PreEmphasis == 'y' else 1
newCfg['bypassVoiceHPF'] = 0 if VoiceHighPass == 'y' else 1
newCfg['bypassVoiceLPF'] = 0 if VoiceLowPass == 'y' else 1
newCfg['bypassCtcssLPF'] = 0 if CSSLowPass == 'y' else 1
newCfg['bypassCtcssHPF'] = 0 if CSSHighPass == 'y' else 1

if not programRadio(ser, newCfg):
  exit()

