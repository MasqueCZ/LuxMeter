from machine import Pin, I2C
from os import listdir
from SH1106 import SH1106_I2C
from utime import sleep
from BH1750 import BH1750
from neopixel import Neopixel
import DS1307, _thread, micropython

v = "2.6-14"
version = f"{v} - 14 FIN:0.7s, RON:60s/100%, FOUT:30s, ABL:30%, SOFF:/"

"""
LUX CORRIDOR meter

The relay waits until it gets stable reading of OFF luminaire. And then start the cycle of measurement and data-write phase.
"""
DEBUG = False #If TRUE, program shows extra data in shell

FADE1 = 0.7
HOLD1 = 60
LEVEL1 = 100
FADE2 = 30
HOLD2 = 600 #even when the CORRIDOR won't stop it needs time to know how long to measure
LEVEL2 = 30
FADE3 = 0
HOLD3 = 0
LEVEL3 = 0
INFINITE = True # if TRUE > HOLD2 INDEFINITELY or HOLD3 INDEFINITELY | FALSE if exact by the times stated above

TOLERANCE = 0.10 #tolerance porovnani dat 10%
TOL_LUX = 0.02 #tolerance zmeny hodnoty v namerenych lumenech 2%
cas_bezi = 0

# display update and read data time 0.1 works well for now
update_time = 0.42
pix_val = 0.5 # variable for PIXELS value

#program_end = False
program_result = "nevyhodnocen/program ukončen předčasně"
OK = True   # PROGRAM final verdict | False = NOK


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

# strip of 1 chips, state machine 0, GPIO 28(pin34), RGB mode
n_leds = 1
pixels = Neopixel(n_leds, 0, 28, "GRB")

# buttons
button_ok = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_up = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(18, Pin.IN, Pin.PULL_DOWN)

# control LED
LED = Pin(25, Pin.OUT)
LED.value(0)

# sets MOOD LED to READY
pixels.fill((25*pix_val, 10*pix_val, 0)) # ORANGE
pixels.show()

#enable oscillator
#ds.halt(FALSE)

# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
# now = (2022, 5, 30, 1, 8, 57, 30, 0)
# ds.datetime(now)

if INFINITE == True:
    trvani_s_rezervou = (5 + FADE1 + HOLD1 + FADE2 + HOLD2 + FADE3 + HOLD3) * 1.15
else:
    trvani_s_rezervou = (5 + FADE1 + HOLD1 + FADE2 + HOLD2 + FADE3 + HOLD3) * 1.08

if DEBUG == True:
    print(f"{trvani_s_rezervou} trvani_s_rezervou")

def format_seconds_to_hhmmss(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

celkovy_cas_rezerva = format_seconds_to_hhmmss(trvani_s_rezervou)

def get_time():
    time_list = ds.datetime()
    print(f"Time is {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")

if DEBUG == True:
    get_time()

def get_seconds():
    allseconds = (counter_s + (counter_m * 60) + (counter_h * 60 * 60))
    return allseconds

# set variables for measurement and comparison
"""
Variables for final written data
Val0 - Val4 = lux
Tim0 - Tim6 = sec
Per1 and Per2 = %
Fad1, Fad2 and Fad3 = sec
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

# time counters
counter_s = 0
counter_m = 0
counter_h = 0

# data LOGGING counter
counter_log = 1

# for last 5 values to compare if stabilised
lux_list = [0, 0, 0, 0, 0]
lux_value = [False, False, False, False, False]

stable_boolean = False

# waiting phase
while True:
    if button_ok.value() == 1:
        break
    LED.toggle()
    oled.fill(0)
    lux = light.luminance(BH1750.CONT_HIRES_1)
    lux = str(round(lux, 0))
    oled.text(lux + " lx", 0, 0)
    oled.text("PRESS START", 15, 18)
    oled.text("Delka testu:", 0, 36)
    oled.text(celkovy_cas_rezerva, 0, 48)
    oled.show()
    sleep(0.18)

# sets MOOD LED to MEASUREMENT STARTS
pixels.fill((0, 0, 15*pix_val)) # BLUE
pixels.show()

sleep(1)

# measurement phase
time_list = ds.datetime()

# corrects file name time and date to format 2022-07-05 from 2022-7-5 etc
for i in range (0,6):
    time_list = list(time_list)

    if time_list[i] <= 9:
        time_list[i] = (f"0{time_list[i]}")
    time_list = tuple(time_list)

test_file_name = (f"/mereni/{time_list[0]}-{time_list[1]}-{time_list[2]}_{time_list[4]}-{time_list[5]}-{time_list[6]}-{v}.txt")
file = open(test_file_name, "w")
file.write(f"Program started {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}" + "\n" + f"version: v{v}-{version}" + "\n")
file.write("\n" + f"Parameters:" + "\n" + f"Fade {FADE1}s, Hold {HOLD1}s at {LEVEL1}%" + "\n")
file.write(f"fade {FADE2}s, hold {HOLD2}s at {LEVEL2}%" + "\n")
file.write(f"fade {FADE3}s, hold {HOLD3}s at {LEVEL3}%" + "\n")

if INFINITE == True:
    file.write(f"Driver nikdy nevypíná úplně do 0% ale měří jen: {celkovy_cas_rezerva}" + "\n")
elif INFINITE == False:
    file.write(f"Driver vypíná do 0% a měří: {celkovy_cas_rezerva}" + "\n")
file.write("\n")
file.flush()


time_start = [time_list[4], time_list[5], time_list[6]]
time_actual = [time_list[4], time_list[5], time_list[6]]

sec_to_measure = time_actual[2]



while True:
    if button_ok.value() == 1:
        file.write("Shut down by BUTTON press" + "\n")
        break

    # LEDs to see whether it FROZE or NOT
    LED.toggle()
    pixels.fill((3*pix_val, 3*pix_val, 3*pix_val)) # WHITE
    pixels.show()

    # updates time list
    time_list = ds.datetime()
    time_actual = [time_list[4], time_list[5], time_list[6]]

    # TIME counters - updates 1 second counter which dictates if it is ready to read and write data
    if time_actual[2] > sec_to_measure or time_actual[2] < sec_to_measure:
        sec_to_measure = time_actual[2] # updates
        counter_log = 1 # calls datalogging
        counter_s += 1

    if counter_s >= 60:
        counter_s = 0
        counter_m += 1

    if counter_m >= 60:
        counter_m = 0
        counter_h += 1


    # READS lumen value
    lux = light.luminance(BH1750.CONT_HIRES_1)
    if DEBUG == True:
        print(f"{lux} lux type {type(lux)}")
    lux = str(round(lux, 1))  # round to whole numbers
    oled.fill(0)

    # DISPLAY update
    oled.text(str(counter_h) + ":" + str(counter_m) + ":" + str(counter_s) + f"/{celkovy_cas_rezerva}", 0, 0)
    oled.text(lux + " lx", 0, 12)
    oled.text("Phase: ", 0, 24)
    oled.text(phase, 0, 36)
    oled.text(phase2, 0, 48)
    oled.show()

    # DATA LOGGER
    # checks whether it is needed to write and compare LUX data
    if counter_log == 1:

        counter_log = 0
        lux_list.insert(0, lux)
        if len(lux_list) > 5:
            lux_list.pop()

        lx_valmin = (float(lux_list[1])) * (1 - TOL_LUX)
        lx_valmax = (float(lux_list[1])) * (1 + TOL_LUX)

        if float(lux) >= lx_valmin and float(lux) <= lx_valmax:  # and float(lux) >= lx_val095 or float(lux) <= lx_val105
            lux_value.insert(0, True)
            stable_boolean = True
        else:
            lux_value.insert(0, False)
            stable_boolean = False

    if len(lux_value) > 5:
        lux_value.pop()
        if DEBUG == True:
            print(f"{lux_list} lux_list")
            print(f"{lux_value} lux_value")
    stable = all(i for i in lux_value)

# OPERATIVE phase

    if Val0 == "x" and stable == True:
        Val0 = lux
        Tim0 = get_seconds() - 0  # play with this number in real situations | 0 sec for this is where all other starts
        relay.value(0)
        relay02.value(0)
        #sleep(0) # lets try 0 here, whether it works or dont
        stable = False  # this condition and the line above IS enough to catch the OFF ON transition, so it does not evaluate STABLE = TRUE immediately
        file.write("Measurement:" + "\n")
        file.write("Stable at: " + str(Val0) + "lx\n")
        sleep(1)
        relay02.value(1)

    if Val1 == "x" and stable == True:
        Val1 = lux
        Tim1 = get_seconds() - 5
        if float(Val1) < 1.0:
            #button_pressed = True
            program_result = "Val1 nemuze byt nula"
            file.write("Val1 nemuze byt nula" + "\n")
            break

        phase = "Operative:"
        phase2 = "Tim 1 - HOLD"

# Standby 1
    if Tim1 != "x" and Tim2 == "x" and stable_boolean == False:
        Tim2 = get_seconds()
        phase = "StandBy 1:"
        phase2 = "Tim 2 - FADE"
        Hol1 = Tim2 - Tim1
        Fad1 = Tim1 - Tim0

        if Fad1 <= 1 and FADE1 <= 1:
            file.write("OK")
        elif Fad1 <= (10 * FADE1):
            file.write(f"OK-ish")
        else:
            if float(FADE1) <= Fad1 + (Fad1 * TOLERANCE) and float(FADE1) >= Fad1 - (Fad1 * TOLERANCE):
                file.write("OK")
            else:
                file.write("NOK")
                OK = False

        file.write(" - Fade time 1: " + str(Fad1) + "s\n")

        if float(HOLD1) <= Hol1 + (Hol1 * TOLERANCE) and float(HOLD1) >= Hol1 - (Hol1 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False

        file.write(" - Hold time 1: " + str(Hol1) + "s at value: " + str(Val1) + "lx (100%)\n")
        file.flush()

    if Tim1 != "x" and Tim2 != "x" and Tim3 == "x" and stable == True:
        Val2 = lux
        Tim3 = get_seconds()
        Tim3 -= 5
        phase2 = "Tim 3 - HOLD"
        Fad2 = Tim3 - Tim2
        Per1 = round((float(Val2) / float(Val1)) * 100, 1)

        if float(Val2) == 0.0:
            #button_pressed = True #ENDS CYCLE
            program_result = "END at Tim3, Val2 = 0"
            if LEVEL2 == 0.0:
#                OK = True
                file.write(f"OK - Val2: {str(Val2)} equals {str(LEVEL2)}\n")
            break
        elif float(FADE2) <= Fad2 + (Fad2 * TOLERANCE) and float(FADE2) >= Fad2 - (Fad2 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False
            break

        file.write(" - Fade time 2: " + str(Fad2) + "s\n")

        if float(LEVEL2) <= Per1 + (Per1 * TOLERANCE) and float(LEVEL2) >= Per1 - (Per1 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False

        file.write(" - level 2: " + str(Per1) + "%" + "\n")
        file.flush()

# Standby 2
    if Tim3 != "x" and Tim4 == "x" and stable_boolean == False:
        Tim4 = get_seconds()
        phase = "StandBy 2:"
        phase2 = "Tim 4 - FADE"
        Hol2 = Tim4 - Tim3

        if float(HOLD2) <= Hol2 + (Hol2 * TOLERANCE) and float(HOLD2) >= Hol2 - (Hol2 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False

        file.write(" - hold time 2: " + str(Hol2) + "s at value: " + str(Val2) + "lx " + "at " + str(Per1) + "%" + "\n")
        file.flush()

    if Tim4 != "x" and Tim5 == "x" and stable == True:
        Val3 = lux
        Tim5 = get_seconds()
        Tim5 -= 5
        Per2 = round(float(Val3) / float(Val1) * 100, 1)
        phase2 = "Tim 5 - HOLD"
        Fad3 = Tim5 - Tim4

        if float(FADE3) <= Fad3 + (Fad3 * TOLERANCE) and float(FADE3) >= Fad3 - (Fad3 * TOLERANCE):
            file.write("OK")
        elif Fad3 <= (10 * FADE3):
            file.write("OK-ish")
        else:
            file.write("NOK")
            OK = False

        file.write("- fade time 3: " + str(Fad3) + "s\n")

        if float(LEVEL3) <= Per2 + (Per2 * TOLERANCE) and float(LEVEL3) >= Per2 - (Per2 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False

        file.write(f"- to level 3: {Per2}%\n")
        file.flush()

    if Tim6 == "x" and Tim5 != "x" and stable_boolean == False:
        Tim6 = get_seconds()
        Val4 = lux
        phase2 = "Tim 6 - END"
        Hol3 = Tim6 - Tim5

        if float(HOLD3) <= Hol3 + (Hol3 * TOLERANCE) and float(HOLD3) >= Hol3 - (Hol3 * TOLERANCE):
            file.write("OK")
        else:
            file.write("NOK")
            OK = False

        file.write("- hold time 3: " + str(Hol3) + "s at value: " + str(Val3) + "lx " + "\n")
        file.write("Final lx value: " + str(Val4) + "\n")
        file.flush()
        #button_pressed = True
        break

    #AUTOMATIC END if measuring too long TIME+10%
    cas_bezi = float(get_seconds())
    cas_celeho_testu = float(trvani_s_rezervou) * 1.0

    if DEBUG == True:
        print(f"{cas_bezi}/{cas_celeho_testu}")

    if cas_bezi >= cas_celeho_testu:
        print("piskej KONEC KURVA!")

        if DEBUG == True:
            print(f"Per1 {Per1}")
            print(f"Per2 {Per2}")

        if INFINITE == True:
            if Per2 == "x" or Per2 > 1:
                Per2X = True
            if float(Per1) > 1 and Per2X == True:
                file.write(f"OK - Světlo svítilo dál, ukončeno automaticky po definovaném čase\n")
                #OK = False
            else:
                file.write(f"NOK - Světlo zhaslo, ukončeno zhasnutím\n")
                OK = False
        break


    if DEBUG == True:
        micropython.mem_info()

    pixels.fill((0, 0, 15*pix_val))  # BLUE
    pixels.show()
    sleep(update_time)

"""Result comparison"""
if Val0 == "x" or Val1 == "x" or Val2 == "x":
    OK = False

oled.fill(0)
if OK == True:
    oled.text("OK", 0, 24)
    program_result = "Měření OK"
    pixels.fill((0, 80 * pix_val, 0))
    pixels.show()
else:
    oled.text("NOK", 0, 24)
    program_result = "Měření NOK"
    pixels.fill((80 * pix_val, 0, 0))
    pixels.show()
oled.show()

file.write("\n" + "Result:" + program_result + "\n")

relay.value(1) #shuts off luminaire
relay02.value(1) #shuts off phase from Relay02
LED.value(0) #shuts off control LED on RPiPico
file.close()

# WAIT phase for button click before jumping back to the menu
while True:
    if button_ok.value() == 1:
        break

# re-sets MOOD LED to END
pixels.fill((0, 0, 0))
pixels.show()
sleep(0.75)