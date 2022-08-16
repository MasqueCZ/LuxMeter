from machine import Pin, I2C
from BH1750 import BH1750
from ssd1306 import SSD1306_I2C
from neopixel import Neopixel
import DS1307, utime

version = "1.00 uni uni"
"""
LUX meter

UNIVERZÁLNÍ měření - zapisuje každých X sec!!

RELAY
kontrolní LED - bliká při čtení aktuální hodnoty
3x tlačítka START/STOP, UP, DOWN
1x reset
"""
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)

# display
oled = SSD1306_I2C(128, 64, i2c)
oled.fill(0)

# light meter module
light = BH1750(i2c)

# RealTimeClock module
ds = DS1307.DS1307(i2c)

# relay
relay = Pin(21, Pin.OUT)
relay.value(1)

# strip of 1 chips, state machine 0, GPIO 28(pin34), RGB mode
n_leds = 1
pixels = Neopixel(n_leds, 0, 28, "GRB")

# sets MOOD LED to READY
pixels.fill((25, 10, 0))
pixels.show()

# buttons
button = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_up = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(18, Pin.IN, Pin.PULL_DOWN)

# control LED
LED = Pin(25, Pin.OUT)
LED.value(0)

# enable oscillator
# ds.halt(FALSE)

# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
# now = (2022, 5, 30, 1, 8, 57, 30, 0)
# ds.datetime(now)

def get_time():
    time_list = ds.datetime()
    print(f"Time is {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")

frequency = 5

while True:
    if button.value() == 1:
        break
    if button_up.value() == 1:
        frequency += 1
        print(button_up.value())
    if button_down.value() == 1:
        frequency -= 1
        if frequency <= 1:
            frequency = 1
        print(button_down.value())

    LED.toggle()
    oled.fill(0)
    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = str(round(lux, 0))
    oled.text(f"sampling {frequency}s", 0, 0)
    oled.text(lux + " lx", 0, 12)
    oled.text("PRESS START", 15, 36)
    oled.show()
    utime.sleep(0.2)

# sets MOOD LED to MEASUREMENT STARTS
pixels.fill((0, 0, 10))
pixels.show()
utime.sleep(1)

# measurement phase
time_list = ds.datetime()
test_file_name = (f"/mereni/uniuni{time_list[0]}-{time_list[1]}-{time_list[2]}_{time_list[4]}-{time_list[5]}-{time_list[6]}.txt")
file = open(test_file_name, "w")
file.write(f"Program started {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]} v{version}" + "\n")
file.flush()

# display update and read data time 0.1 works well for now
update_time = 0.1

time_start = [time_list[4], time_list[5], time_list[6]]
time_actual = [time_list[4], time_list[5], time_list[6]]

sec_to_measure = time_actual[2]

# time counters
counter_s = 0
counter_m = 0
counter_h = 0

# data LOGGING counter
counter_log = frequency - 1

while True:
    relay.value(0)
    LED.toggle()
    pixels.fill((10, 0, 0))
    pixels.show()

    if button.value() == 1:
        break

    time_list = ds.datetime()
    time_actual = [time_list[4], time_list[5], time_list[6]]

    if time_actual[2] > sec_to_measure or time_actual[2] < sec_to_measure:
        sec_to_measure = time_actual[2]
        counter_log += 1
        counter_s += 1

    if counter_s >= 60:
        counter_s = 0
        counter_m += 1

    if counter_m >= 60:
        counter_m = 0
        counter_h += 1

    #     print(f"{time_actual[0]} h {time_actual[1]} m {time_actual[2]} s")
    #     print(f"{counter_h} {counter_m} {counter_s}")

    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = round(lux, 0)
    lux = str(round(lux, 1))  # round to whole numbers
    oled.fill(0)

    oled.text(str(counter_h) + ":" + str(counter_m) + ":" + str(counter_s), 0, 0)
    oled.text(lux + " lx", 0, 12)
    oled.text(f"smpl_frq {frequency}s", 0, 24)
    oled.text("..Measuring..", 12, 36)
    oled.text("..forever..", 18, 48)
    oled.show()

    # datalogger
    if counter_log == frequency or counter_log >= frequency:
        file.write(str(counter_h) + ":" + str(counter_m) + ":" + str(counter_s) + "-" + lux + "\n")
        file.flush()
        counter_log = 0
        pixels.fill((0, 25, 0))
        pixels.show()
        utime.sleep(0.05)

    utime.sleep(update_time)

relay.value(1)
LED.value(0)
oled.fill(0)
oled.show()
file.close()
utime.sleep(2)

"""no END screen ANIMATION"""
