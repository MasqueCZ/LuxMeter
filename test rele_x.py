from machine import Pin, I2C
from os import listdir
from ssd1306 import SSD1306_I2C
from utime import sleep
from BH1750 import BH1750
from neopixel import Neopixel
import DS1307, _thread

# relay
relay = Pin(21, Pin.OUT)
relay.value(1)

for i in range(100):
    relay.toggle()
    sleep(1)