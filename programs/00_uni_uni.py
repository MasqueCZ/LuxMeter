from machine import Pin, I2C
from BH1750 import BH1750
from SH1106 import SH1106_I2C
from neopixel import Neopixel
import DS1307
import utime

v = "1.02 uni"
"""
LUX meter

UNIVERSAL measurement - writes data every X sec!! (1, 5, 10, 30, 60, 600, 3600)
You can set timed OFF of measurement after "never", 1, 2, 4, 8, 12, 24 or 168 hours. 

There is a graph of last 30 values on the display

RELAY - Turns on at the start of the measurement
RELAY02 - push UP+DOWN to turn on momentarily
LED blinks while reading value - green while value changes, blue if it is considered the light source a stable one
Display(i2c) 128x64
RTC module
3x buttons START/STOP, UP, DOWN
1x reset
+ GRAPH of 30 last values

Přidat verzi: program name: uni-cycle? Pun intended. Or add it at choosing the times of OFF timer.
Nastavit délku doby měření (ON-stykače) v hodinách, když 0, tak bez limitu a ostatní nastavování přeskočit.
Nastavit délku doby měření v (OFF-stykače) v hodinách, měření stále bude zapisovat
Nastavit počet cyklů. 

Add version with timer that counts up the time and gives data-over time and shows TIME UP after end of testing
EMERGENCY - how long battery lasts. Possibly when the lumen drop below 5% of what it was?

rework the time tokens, to consider RTC unit and compare real-time to frequency, not as a tokens.
rework time with W module - so it can grab actual time of internet

GRAPH turn on and turn off? Variable?
"""

DATA_SAVE = True
stable_checker = 3 #values
TIMED_END = True
stable_tolerance = 25
#turns L3 5 times ON and OFF in 2.5 seconds
reset_corridor = False

i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)

# display
width = 128
height = 64
oled = SH1106_I2C(width=width, height=height, i2c=i2c, rotate=180)
oled.fill(0)

# light meter module
light = BH1750(i2c)

# RealTimeClock module
ds = DS1307.DS1307(i2c)

# relays
relay = Pin(21, Pin.OUT)
relay02 = Pin(22, Pin.OUT)
relay.value(1)
relay02.value(1)

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

# enable CLOCK oscillator (for starting a new machine)
# ds.halt(FALSE)

# for setting the TIME and EDITS
# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
# print(ds.datetime())
# now = (2023, 1, 26, 4, 7, 50, 0, 0)
# ds.datetime(now)


def get_time():
    time_list = ds.datetime()
    print(f"Time is {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")

get_time()

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

#selection of SAMPLING frequency
while True:
    if button_ok.value() == 1:
        break
    if button_up.value() == 1:
        if selection >= 6: #zkopirovat tohle do MAIN.py menu
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
    oled.text(f"...", 0, 12)
    oled.text(str(lm) + " lx", 0, 24)
    oled.text("PRESS START", 15, 36)
    oled.show()
    utime.sleep(0.14)

utime.sleep(1)


timeOFF_list = (0, 1, 2, 4, 8, 12, 24, 168)
timeOFF = timeOFF_list[0]
selectionOFF = 0

# selection of OFF TIME
while True:
    if button_ok.value() == 1:
        break
    if button_up.value() == 1:
        if selectionOFF >= len(timeOFF_list)-1:
            continue
        else:
            selectionOFF += 1
            timeOFF = timeOFF_list[selectionOFF]
    if button_down.value() == 1:
        if selectionOFF <= 0:
            continue
        else:
            selectionOFF -= 1
            timeOFF = timeOFF_list[selectionOFF]

    LED.toggle()
    oled.fill(0)
    lm = lux()

    oled.text(f"sampling {frequency}s", 0, 0)
    if timeOFF == 0:
        oled.text(f"Nevypne..", 0,12)
    else:
        oled.text(f"Vypne po:{timeOFF}h", 0, 12)
    oled.text(str(lm) + " lx", 0, 24)
    oled.text("PRESS START", 15, 36)
    oled.show()
    utime.sleep(0.14)

if timeOFF == 0:
    TIMED_END = False

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
    f"Program started {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]} v{v}_freq_{frequency}s with time OFF set to {timeOFF}h and {stable_tolerance} lm tolerance" + "\n")
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
save_data_ph1 = stable_checker - 1
save_data_ph2 = stable_checker - 1
stable_phase1 = False
stable_phase2 = False
lx_ph1_compare = "x"
pix_green = (0, 25, 0)
pix_blue = (0, 0, 25)
pix_red = (10, 0, 0)

#JUST TO RESET CORRIDOR
while reset_corridor == True:
    relay.value(0)
    utime.sleep(2)
    for i in range(10):
        relay02.toggle()
        utime.sleep(0.25)
    break

#MEASUREMENT PHASE
while True:

    if button_up.value() == 1 and button_down.value() == 1:
        relay02.value(0)
    else:
        relay02.value(1)

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
    oled.rect(0, 20, 128, 43, 1)

    # datalogger
    if counter_log == frequency or counter_log >= frequency:

        if relay02.value() == 0:
            file.write(f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-temp. L3 - ON \n")

        data_saver.append(lm)
        if len(data_saver) > stable_checker:
            data_saver.pop(0)

            #Phase one STABLE checker - is it exactly the same?
            for i in range(0, stable_checker - 1):
                if int(data_saver[i]) == lm:
                    save_data_ph1 += 1
                else:
                    save_data_ph1 = 0
                    stable_phase1 = False

                """"
                Dat tuhle phase2 za uroven phase1 a pokud se nespusti tak phase2 ani nekontrolovat
                a kdyz vypadne z limitu vstupni hodnoty, tak to vyhodit mimo stable phase1/2
                
                pouzit lx_ph1_compare = lm ??
                 """

            #Phase two STABLE checker - is it within limit?
            for i in range(0, stable_checker - 1):
                if int(data_saver[i]) >= (lm - stable_tolerance) and int(data_saver[i]) <= (lm + stable_tolerance):
                    save_data_ph2 += 1
                else:
                    save_data_ph2 = 0
                    stable_phase2 = False



        if save_data_ph1 >= stable_checker and save_data_ph2 >= stable_checker:
            if stable_phase1 == True:
                pixels.fill(pix_blue)
                oled.text(str(lm) + " lx - STABLE", 0, 12)
                #add data write if there was MINUTE up or HOUR up - depending on time, even though it is STABLE
            else:
                stable_phase1 = True
                # save exact data for PHASE1 to compare
                lx_ph1_compare = lm
                pixels.fill(pix_blue)
                file.write(f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-{str(lm)}\n")
                oled.text(str(lm) + " lx - STABLE", 0, 12)

        elif save_data_ph2 >= stable_checker:
            if stable_phase2 == True:
                pixels.fill(pix_blue)
                oled.text(str(lm) + " lx - stable", 0, 12)
                # add data write if there was MINUTE up or HOUR up - depending on time, even though it is STABLE
            else:
                stable_phase2 = True
                pixels.fill(pix_blue)
                file.write(f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-{str(lm)}\n")
                oled.text(str(lm) + " lx - stable", 0, 12)
        else:
            file.write(f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-{str(lm)}\n")
            pixels.fill(pix_green)

        file.flush()
        counter_log = 0

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

    pixels.show()
    oled.show()

    #fckadoodledoo MAGIC turn off
    if TIMED_END==True and counter_h >= timeOFF:
        file.write((f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-{str(lm)}\n"))
        file.write(f"Ukončeno automaticky po čase: {timeOFF} h \n")
        break

    utime.sleep(update_time)

file.write(f"{str(counter_h)}:{str(counter_m)}:{str(counter_s)}-{str(lm)}\nTHE END\n")
relay.value(1)
LED.value(0)
oled.fill(0)
oled.show()
file.close()
utime.sleep(1)

"""no END screen ANIMATION"""