import time

import board
import busio
import neopixel
import adafruit_ssd1306
import rtc
import touchio
from digitalio import DigitalInOut

TOUCH_THRESHOLD     = 3800
RTC_FILE            = "now.dat"
REMINDERS_FILE      = "reminders.dat"
REMINDER_COLOR      = 0xEA6292
REMINDER_TIME       = 3
DISP_DAYS           = 5


i2c = busio.I2C(board.SCL, board.SDA)

pixels = neopixel.NeoPixel(board.D5, 5, pixel_order=neopixel.RGB)

disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3d, reset=DigitalInOut(board.A5))

clock = rtc.RTC()

touch_pads = ( touchio.TouchIn(board.A4),
               touchio.TouchIn(board.A3),
               touchio.TouchIn(board.A2),
               touchio.TouchIn(board.A1),
               touchio.TouchIn(board.A0)  )
 

for p in touch_pads:
    p.threshold = TOUCH_THRESHOLD

def touched_pad():
    for i, pad in enumerate(touch_pads):
        if pad.value:
            return i
    return None

def set_rtc():
    """Set the RTC if the file is present."""
    print("Checking for date file...", end="")
    try:
        with open(RTC_FILE, "r") as fp:
            d, t = fp.readline().split("T", 1)
        tm_year, tm_mon, tm_mday = (int(x) for x in d.split("-"))
        tm_hour, tm_min, tm_sec = (int(x) for x in t.split(":"))
        clock.datetime = time.struct_time((tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec) + (0,)*3)
        print("found. RTC set to {:4}-{:02}-{:02} {:02}:{:02}:{:02}.".format(tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec))
    except OSError:
        now = time.datetime
        print("not found. RTC current time is {:4}-{:02}-{:02} {:02}:{:02}:{:02}.".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec))

def load_reminders():
    """Read the reminders file and load any reminders within the current time window."""
    print("Reading reminders file...", end="")
    now_secs = time.mktime(clock.datetime)
    reminders = [None]*DISP_DAYS   
    try:
        with open(REMINDERS_FILE,"r") as fp:
            raw_info = fp.read()
        for entry in raw_info.split("\n"):
            d, msg = entry.split(":", 1)
            tm_year, tm_mon, tm_mday = (int(x) for x in d.split("-"))
            reminder_secs = time.mktime((tm_year, tm_mon, tm_mday, 24, 59, 59) + (0,)*3)
            if reminder_secs >= now_secs: 
                delta = (reminder_secs - now_secs) // 86400
                if (delta < DISP_DAYS):
                    reminders[delta] = msg
        print("done.")
        return reminders
    except OSError:
        print("not found. I'm just going to sit here.")
        while True:
            pass

def update_pixels(reminders):
    pixels.fill(0)
    for p, r in enumerate(reminders):
        if r is not None:
            pixels[p] = REMINDER_COLOR
    if not pixels.auto_write:
        pixels.show()

pixels.fill(0)
set_rtc()
reminders = load_reminders()
update_pixels(reminders)

last_display = time.monotonic()
display_needs_clearing = False

while True:
    touched = touched_pad()
    if touched is not None:
        if reminders[touched] is not None:            
            print(reminders[touched])
            disp.fill(0)
            disp.text(reminders[touched], 0 ,0)
            disp.show()
            last_display = time.monotonic()
            display_needs_clearing = True
            time.sleep(0.25)
    if display_needs_clearing:
        if time.monotonic() - last_display > REMINDER_TIME:
            disp.fill(0)
            disp.show()
            display_needs_clearing = False