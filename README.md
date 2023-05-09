# LuxMeter
microPython - RPiPico LuxMeter with RTC and SSR relay

My first project, be gentle with comments, but I am open to improvements.


Main part of the project was to measure lumen data over time, save them and then use excel to analyze the result.
But as clever workers are expensive, I was forced to make different programs, which are tailor made just for one type of 
luminaire and at the end of the measurement, you have result in GREEN or RED light and small text file with important 
milestones of corridor function. (for more detailed info about corridor function see blueprints/scheme.jpg)

But as universal measurement was the main pillar of the project, it is updated the most. And it is now in the list of 
programs under name 00_uni_uni.py.

# uni_uni
You can select sampling time from values (1, 5, 10, 30, 60, 600, 3600) seconds and the measurement can end at selected 
time of (0, 1, 2, 4, 8, 12, 24, 168) hours. It measures indefinitely if 0 is selected.

There is data saver feature which stops saving data after 2 same measurements the 3rd is just "stable" and it continues 
to measure but does not take up another space unless the value changes.

There is also a SSR relay that turns on the power at the start of the measurement, second relay can be turned temporarily
by pushing buttons UP and DOWN at the same time. It can be used to re-start the corridor function cycle or jumpstart
emergency mode.

-work in process-

I work on 2 level stable checker, one without a tolerance, one with tolerance but I have to polish it since it can 
slowly slide out of tolerance, without the program realising, since it is so slow changes, that they would be then 
seen as STABLE.

I want to add data write, even if stable and within the tolerance to save data at least once a minute or once a hour 
or a day, if the sampling is lower.