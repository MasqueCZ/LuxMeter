from machine import Pin, I2C
from BH1750 import BH1750
from ssd1306 import SSD1306_I2C
from neopixel import Neopixel
import DS1307
import utime

v = "1.00 uni"
"""
LUX meter

UNIVERZÁLNÍ měření - zapisuje každých X sec!! (1, 5, 10, 30, 60, 600, 3600)

RELAY - zapne po zapnutí měření
kontrolní LED - bliká při čtení aktuální hodnoty
3x tlačítka START/STOP, UP, DOWN
1x reset
+ GRAPH

ADD check, if last 5 values are exactly the same for example ZERO, write down time at which paused writing to file. 
AND wait for change. Then start LOGGING again.

WAIT PHASE HAS BUG, it STOPS signaling that it measures, seems like it froze

GRAPH turn on and turn off? Variable?
"""
DATA_SAVE = True

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

# control LED
LED = Pin(25, Pin.OUT)
LED.value(0)

# strip of 1 chips, state machine 0, GPIO 28(pin34), RGB mode
n_leds = 1
pixels = Neopixel(n_leds, 0, 28, "GRB")
# sets MOOD LED to READY
pixels.fill((25, 10, 0))
pixels.show()

# buttons
button_ok = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_up = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(18, Pin.IN, Pin.PULL_DOWN)

# enable oscillator (for starting a new machine)
# ds.halt(FALSE)

# for setting the TIME and EDITS
# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
# now = (2022, 5, 30, 1, 8, 57, 30, 0)
# ds.datetime(now)


def get_time():
    time_list = ds.datetime()
    print(f"Time is {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")


def lux():
    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = int(round(lux, 0))
    lm = lux
    if lm <= 1:
        lm = 1
    return lm


freq_list = (1, 5, 10, 30, 60, 600, 3600)
frequency = freq_list[0]
selection = 0

while True:
    if button_ok.value() == 1:
        break
    if button_up.value() == 1:
        if selection >= 6:
            continue
        else:
            selection += 1
            frequency = freq_list[selection]
    if button_down.value() == 1:
        if selection <= 0:
            continue
        else:
            selection -= 1
            frequency = freq_list[selection]

    LED.toggle()
    oled.fill(0)
    lm = lux()

    oled.text(f"sampling {frequency}s", 0, 0)
    oled.text(str(lm) + " lx", 0, 12)
    oled.text("PRESS START", 15, 36)
    oled.show()
    utime.sleep(0.2)

# sets MOOD LED to MEASUREMENT STARTS
pixels.fill((0, 0, 10))
pixels.show()
utime.sleep(1)

# measurement phase
time_list = ds.datetime()

# corrects file name time and date to format 2022-07-05 from 2022-7-5 etc
for i in range(0, 6):
    time_list = list(time_list)

    if time_list[i] <= 9:
        time_list[i] = f"0{time_list[i]}"
    time_list = tuple(time_list)

test_file_name = (
    f"/mereni/{time_list[0]}-{time_list[1]}-{time_list[2]}_{time_list[4]}-{time_list[5]}-{time_list[6]}-{v}-freq{frequency}s.txt")
file = open(test_file_name, "w")
file.write(
    f"Program started {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]} v{v}_freq_{frequency}s" + "\n")
file.flush()

# display update and read data time 0.1 works well for now
update_time = 0.02

time_start = [time_list[4], time_list[5], time_list[6]]
time_actual = [time_list[4], time_list[5], time_list[6]]

sec_to_measure = time_actual[2]

# time counters
counter_s = 0
counter_m = 0
counter_h = 0

# data LOGGING counter
counter_log = frequency - 1

graph_list = []
graph_max = 2
oled.fill(0)

data_saver = []
save_data = 4
waiting = False
pix_green = (0, 25, 0)
pix_blue = (0, 0, 25)
pix_red = (10, 0, 0)

while True:
    relay.value(0)
    LED.toggle()
    pixels.fill(pix_red)
    pixels.show()

    if button_ok.value() == 1:
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

    lm = lux()

    oled.fill(0)

    oled.text(f"{counter_h}:{counter_m}:{counter_s} - {frequency}s", 0, 0)
    oled.text(str(lm) + " lx", 0, 12)
    oled.rect(0, 20, 128, 44, 1)

    # datalogger
    if counter_log == frequency or counter_log >= frequency:

        data_saver.append(lm)
        print(lm)
        if len(data_saver) > 5:
            data_saver.pop(0)
            print(data_saver)
            for i in range(0, 4):
                if int(data_saver[i]) == lm:
                    save_data += 1
                    print(data_saver[i])
                    print(save_data)
                else:
                    save_data = 0
                    waiting = False
                    print(lm)
                    print(save_data)

        if save_data >= 5:
            if waiting == True:
                pixels.fill(pix_blue)
                pixels.show()
                continue
            else:
                waiting = True
                pixels.fill(pix_blue)
                file.write(f"stable\n")
                pixels.show()
        else:
            file.write(str(counter_h) + ":" + str(counter_m) + ":" + str(counter_s) + "-" + str(lm) + "\n")
            pixels.fill(pix_green)
            pixels.show()
        file.flush()
        counter_log = 0

        #pixels.show()

        graph_list.append(lm)

        # graph max length
        if len(graph_list) > 30:
            graph_list.pop(0)

    if True:
        # second list with values compared to max value and within 1,33 to 126,62 / for better visibility 2,34 125,61
        # 2 x 62 = nula pro GRAPH, max -27 tj vysledek 34
        if len(graph_list) >= 1:
            graph_max = max(graph_list)
        if graph_max <= 1:
            graph_max = 1
        for i in range(0, len(graph_list)):
            graph_val = round((graph_list[i] / graph_max) * 36)
            round(graph_val, 0)
            oled.rect((2+(4*i)), 60 - (int(graph_val)), 3, 2, 1)

    oled.show()

    utime.sleep(update_time)

relay.value(1)
LED.value(0)
oled.fill(0)
oled.show()
file.close()
utime.sleep(2)

"""no END screen ANIMATION"""
