"""Pro aktualizaci času, protože hodinový modul malinko utíká od reality"""
from machine import Pin, I2C
import DS1307

def get_time():
    time_list = ds.datetime()
    print(f"Čas je {time_list[4]}:{time_list[5]}:{time_list[6]} {time_list[0]}-{time_list[1]}-{time_list[2]}")

i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)

#RealTimeClock module
ds = DS1307.DS1307(i2c)

print("Čas před změnou:")
get_time()
print(ds.datetime())
# sets actual time year/month/day/DOW(starts with sunday=0)/hour/minute/second/subseconds
"""
data popořadě:
(ROK, měsíc, den, DEN v týdnu (neděle = 0, pondělí = 1,..), hodina, minuta, sekunda, milisekunda)

False: pokud se nemá měnit čas a chceme jen vyčíst pro kontrolu
True + aktuální data pokud chceme aktualizovat čas
"""
AKTUALIZOVAT = False
if AKTUALIZOVAT == True:
    now = (2022, 6, 21, 2, 12, 56, 0, 0)
    ds.datetime(now)
    print("\n")
    print("Aktualizovaný čas:")
    get_time()
    AKTUALIZOVAT = False
else:
    print("\n")
    print("Aktualizovaný čas: NE")