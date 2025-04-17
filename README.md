# Timer

It's a not just a simple timer, albeit it can be used as one if needed. It was made for my personal use, such that as long as the timer is active I am supposed to work/study. By default it has 60 min as work time and 15 min as break time. It runs in a loop such that a work time is followed by a break time and then another work time and break time and so on. The values can be changed if needed. 


Another functionality is notifications. It is often that while being engrossed in study or work, I forget to do smaller things like texting someone back or drinking water, etc. You can enter a percentage number and say you entered 60 min as your work time, and your notification time as 50%, so after 30 mins it will pop up with a notification message that you entered. 


# How to convert to .exe

You have 2 source code files, one for windows(timer-win.py) and one for Linux(timer.py). Choose the according to your need. 

Install pyinstaller via

```
pip install pyinstaller
```

Now run 
```
pyinstaller --onefile --windowed --icon=timer_icon.ico timer-win.py
```
