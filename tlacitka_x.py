
# relay
relay = Pin(21, Pin.OUT)
relay.value(1)

# buttons
button = Pin(20, Pin.IN, Pin.PULL_DOWN)
button_up = Pin(19, Pin.IN, Pin.PULL_DOWN)
button_down = Pin(18, Pin.IN, Pin.PULL_DOWN)

# relay.value(0)
RUN = True
button_val = 0
button_up_val = 0
button_do_val = 0
sleep_time = 1
refresh = 0.1

while RUN:

    if button.value() == 1:
        print("START.stisk")
        button_val = 1

    if button_up.value() == 1:
        print("UP.stisk")
        button_up_val = 1

    if button_down.value() == 1:
        print("DOWN.stisk")
        button_do_val = 1

    if button_up.value() and button_down.value() == 1:
        RUN = False


    if button_val == 1:
        print("START")
        relay.toggle()
        sleep(sleep_time)
        button_val = 0

    if button_up_val == 1:
        print("UP")
        sleep(sleep_time)
        button_up_val = 0

    if button_do_val == 1:
        print("DOWN")
        sleep(sleep_time)
        button_do_val = 0

    sleep(refresh)