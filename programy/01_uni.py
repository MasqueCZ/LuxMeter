from machine import Pin, I2C
from BH1750 import BH1750
from ssd1306 import SSD1306_I2C
from neopixel import Neopixel
import DS1307, utime, _thread

version = "1.23 uni"
"""
LUX CORRIDOR meter

The relay waits until it gets stable reading of OFF luminaire. And then start the cycle of measurement and datawrite.

UNIVERZÁLNÍ měření - nevyhodnotí nakonec OK nebo NOK stav !!

!! ZKONTROLOVAT - freeze u třetí části

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

#enable oscillator
#ds.halt(FALSE)

# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
# now = (2022, 5, 30, 1, 8, 57, 30, 0)
# ds.datetime(now)

def get_time():
    time_list = ds.datetime()
    print(f"Time is {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")


get_time()


def get_seconds():
    allseconds = (counter_s + (counter_m * 60) + (counter_h * 60 * 60))
    return allseconds


button_pressed = False
# button_up_pressed = False
# button_down_pressed = False

def button_reader_thread():
    global button_pressed
#     global button_up_pressed
#     global button_down_pressed
    while True:
        if button.value() == 1:
            button_pressed = True
#         elif button_up.value() == 1:
#             button_up_pressed = True
#         elif button_down.value() == 1:
#             button_down_pressed = True
        time.sleep(0.05)

_thread.start_new_thread(button_reader_thread, ())

# set variables for measurement and comparison
"""
Variables for final written data
Val0 - Val4 = lux
Tim0 - Tim6 = sec
Per1 and Per2 = %
Fad0, Fad1 and Fad3 = sec
Hol1, Hol2, and Hol3 = sec
"""
Val0 = "x"
Val1 = "x"
Val2 = "x"
Val3 = "x"
Val4 = "x"
Tim0 = "x"
Tim1 = "x"
Tim2 = "x"
Tim3 = "x"
Tim4 = "x"
Tim5 = "x"
Tim6 = "x"
# calculated from the values Val and Tim
Per1 = "x"
Per2 = "x"
Fad1 = "x"
Fad2 = "x"
Fad3 = "x"
Hol1 = "x"
Hol2 = "x"
Hol3 = "x"

phase = "warm up"
phase2 = ""

# for last 5 values to compare if stabilised
lux_list = [0, 0, 0, 0, 0]
lux_value = [False, False, False, False, False]

stable_boolean = False

# for short txt file
# final_measurement_short = []

# waiting phase
while button_pressed == False:
    LED.toggle()
    oled.fill(0)
    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = str(round(lux, 0))
    oled.text(lux + " lx", 0, 12)
    oled.text("PRESS START", 15, 36)
    oled.show()
    utime.sleep(0.25)

# sets MOOD LED to MEASUREMENT STARTS
pixels.fill((0, 0, 25))
pixels.show()

utime.sleep(1)

# button reset
button_pressed = False

# measurement phase
time_list = ds.datetime()
test_file_name = (
    f"/mereni/{time_list[0]}-{time_list[1]}-{time_list[2]}_{time_list[4]}-{time_list[5]}-{time_list[6]}.txt")
file = open(test_file_name, "w")
file.write(
    f"Program started {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]} v{version}" + "\n")
file.flush()

# counter time
# display update and read data time 0.1 works well for now
update_time = 0.25

time_start = [time_list[4], time_list[5], time_list[6]]
time_actual = [time_list[4], time_list[5], time_list[6]]

sec_to_measure = time_actual[2]

# time counters
counter_s = 0
counter_m = 0
counter_h = 0

# data LOGGING counter
counter_log = 1

while button_pressed == False:

    time_list = ds.datetime()
    time_actual = [time_list[4], time_list[5], time_list[6]]

    if time_actual[2] > sec_to_measure or time_actual[2] < sec_to_measure:
        sec_to_measure = time_actual[2]
        counter_log = 1
        counter_s += 1

    if counter_s >= 60:
        counter_s = 0
        counter_m += 1

    if counter_m >= 60:
        counter_m = 0
        counter_h += 1

    #     print(f"{time_actual[0]} h {time_actual[1]} m {time_actual[2]} s")
    #     print(f"{counter_h} {counter_m} {counter_s}")

    LED.value(1)

    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = round(lux, 0)
    lux = str(round(lux, 1))  # round to whole numbers
    oled.fill(0)

    if counter_h > 0:
        oled.text("time " + str(counter_h) + "h " + str(counter_m) + "m " + str(counter_s) + "s", 0, 0)
    elif counter_m == 0:
        oled.text("time " + str(counter_s) + "s", 0, 0)
    else:
        oled.text("time " + str(counter_m) + "m " + str(counter_s) + "s", 0, 0)

    oled.text(lux + " lx", 0, 12)
    oled.text("Phase: ", 0, 24)
    oled.text(phase, 0, 36)
    oled.text(phase2, 0, 48)
    oled.show()

    # datalogger
    if counter_log == 1:

        #         file.write(str(counter_h) + ":" + str(counter_m) + ":" + str(counter_s) + "-" + lux + "\n")
        #         file.flush()

        #         file.write(str(value) + "" + "\n")
        #         file.flush()

        counter_log = 0
        lux_list.insert(0, lux)
        if len(lux_list) > 5:
            lux_list.pop()

        lx_valmin = (float(lux_list[1])) * 0.98
        lx_valmax = (float(lux_list[1])) * 1.02

        if float(lux) >= lx_valmin and float(
                lux) <= lx_valmax:  # and float(lux) >= lx_val095 or float(lux) <= lx_val105
            lux_value.insert(0, True)
            stable_boolean = True
        else:
            lux_value.insert(0, False)
            stable_boolean = False

    if len(lux_value) > 5:
        lux_value.pop()
    #     print(lux_list)
    #     print(lux_value)
    stable = all(i for i in lux_value)

    if Val0 == "x" and stable == True:
        Val0 = lux
        Tim0 = get_seconds() - 5  # play with this number in real situations
        relay.value(0)
        utime.sleep(0)
        stable = False  # this is condition enough to catch the OFF ON transition, so it does not evaluate STABLE = TRUE immediately

    if Val1 == "x" and stable == True:
        Val1 = lux
        Tim1 = get_seconds() - 5
        #                 lux_value.insert(0, False)
        #                 lux_value.pop()
        phase = "Operative:"
        phase2 = "Tim 1 - HOLD"

    if Tim1 != "x" and Tim2 == "x" and stable_boolean == False:
        Tim2 = get_seconds()
        #             Tim2 -= Tim1
        phase = "StandBy 1:"
        phase2 = "Tim 2 - FADE"
        Hol1 = Tim2 - Tim1
        Fad0 = Tim1 - Tim0
        file.write("Stable at: " + str(Val0) + "lx\n")
        file.write("Fade time 1: " + str(Fad0) + "s\n")
        file.write("Hold time 1: " + str(Hol1) + "s at value: " + str(Val1) + "lx\n")
        file.flush()

    if Tim1 != "x" and Tim2 != "x" and Tim3 == "x" and stable == True:
        Val2 = lux
        Tim3 = get_seconds()
        Tim3 -= 5
        phase2 = "Tim 3 - HOLD"
        Fad2 = Tim3 - Tim2
        file.write("Fade time 2: " + str(Fad2) + "s\n")
        file.flush()

    if Tim3 != "x" and Tim4 == "x" and stable_boolean == False:
        Tim4 = get_seconds()
        phase = "StandBy 2:"
        phase2 = "Tim 4 - FADE"
        Hol2 = Tim4 - Tim3
        if Val1 != "x" and Val2 != "x" and Per1 == "x":
            Per1 = round((float(Val2) / float(Val1)) * 100, 1)
        file.write("Hold time 2: " + str(Hol2) + "s at value: " + str(Val2) + "lx " + "at " + str(Per1) + "%" + "\n")
        file.flush()

    if Tim4 != "x" and Tim5 == "x" and stable == True:
        Val3 = lux
        Tim5 = get_seconds()
        Tim5 -= 5
        phase2 = "Tim 5 - HOLD"
        Fad3 = Tim5 - Tim4
        file.write("Fade time 3: " + str(Fad3) + "s\n")
        file.flush()

    if Tim6 == "x" and Tim5 != "x" and stable_boolean == False:
        Tim6 = get_seconds()
        Val4 = lux
        phase2 = "Tim 6 - END"
        Hol3 = Tim6 - Tim5
        if Val1 != "x" and Val3 != "x" and Per2 == "x":
            Per2 = round(float(Val3) / float(Val1) * 100, 1)
        file.write("Hold time 3: " + str(Hol3) + "s at value: " + str(Val3) + "lx " + "at " + str(Per2) + "%" + "\n")
        file.flush()

    #     print(f"{Val1} lux operative phase - Val1")
    #     print(f"{Tim1} s - operative phase HOLD 1 - Tim1")
    #     print(f"{Tim2} s - standby phase1 - fade2 start - Tim2")
    #     print(f"{Tim3} s - standby phase1 - fade2 end - Tim3")
    #     print(f"{Val2} lux ({Per1}%) standby phase1 - Val2")
    #     print(f"{Tim4} s - standby phase2 - fade3 start - Tim4")
    #     print(f"{Tim5} s - standby phase2 - fade3 end - Tim5")
    #     print(f"{Val3} lux ({Per2}%) standby phase2 - Val3")
    #     print(f"{Tim6} s - standby phase2 - END - Tim6")
    #     print(f"{Val4} lux standby phase2 - END Val4")
    #         print(f"{percent_one}% of fade")

    utime.sleep(update_time)


relay.value(1)
LED.value(0)

"""OK or NOK - to be finished"""
# sets MOOD LED to NOK or OK
pixels.fill((80, 0, 0))
pixels.show()
utime.sleep(2)
pixels.fill((0, 80, 0))
pixels.show()
utime.sleep(2)

file.close()

# re-sets MOOD LED to END
# pixels.fill((0, 0, 0))
# pixels.show()

# change first file name to test_data.txt
# file = open(test_file_name, "w")
# file.write(final_measurement_short)

# for final and short data after the measurement is done or STOPPED
# file = open("actual_date.txt", "w")


"""END screen ANIMATION"""
# final_round = 0
# text_PRESS = "---PRESS---"
# text_RESET = "---RESET---"
# 
# while True:
#     if final_round == 0:
#         text_PRESS = "---PRESS---"
#         text_RESET = "---RESET---"
#         final_round += 1
#     elif final_round == 1:
#         text_PRESS = ">--PRESS--<"
#         text_RESET = "---RESET---"
#         final_round += 1
#     elif final_round == 2:
#         text_PRESS = "->-PRESS-<-"
#         text_RESET = ">--RESET--<"
#         final_round += 1
#     elif final_round == 3:
#         text_PRESS = "-->PRESS<--"
#         text_RESET = "->-RESET-<-"
#         final_round += 1
#     elif final_round == 4:
#         text_PRESS = "---PRESS---"
#         text_RESET = "-->RESET<--"
#         final_round = 0
#     oled.fill(0)
#     #     oled.text("We are done!", 0, 0)
#     oled.text(text_PRESS, 20, 18)
#     oled.text(text_RESET, 20, 32)
#     #     oled.text("to start again", 0,48)
#     oled.show()
#     utime.sleep(0.25)
