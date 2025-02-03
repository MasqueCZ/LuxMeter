box_version = "01"
'''
box version
00 - TU
01 - Mont / set display rot 0
02 - Inno / set display rot 180
'''
display_rotation = 0

if box_version == 01:
    display_rotation = 0
elif box_version == 02:
    display_rotation = 180

v = "3.0"

#PREPARATION
#dictionary
program29 = \
    {'version' :  "- FIN:0.7s, RON:60s/100%, FOUT:2s, ABL:10%, SOFF:1800s",
    'FADE1' : 0.7,
    'HOLD1' : 60,
    'LEVEL1' : 100,
    'FADE2' : 2,
    'HOLD2' : 600,
    'LEVEL2' : 10,
    'FADE3' : 0,
    'HOLD3' : 0,
    'LEVEL3' : 0,
    'INFINITE' : True
    }