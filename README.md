# iracing-apps

This repository contains a collection of iRacing integrations I have created using the [Python iRacing SDK](https://github.com/kutu/pyirsdk). The integrations in this repository were designed to be run along side pyirsdk's `irsdk.py` and `setup.py` scripts.

## Overlay

Currently my overlay is a grid of boxes showing several metrics, with a bar on top indicating the shift indicator percentage. Below are definitions of the cboxes' content from left to right, top to bottom.

### Shift Indicator
Draws a bar from the far left edge to far right edge where the length indicates the shift indicator percentage (0-1) and the color the intensity.

#### Colors
- Green: First indicator, > 0
- Yellow: Shift indicator
- Orange: Last indicator
- Red: Blink
- Blue: Red line

### Flag
Fills a grid cell with a color indicating the current flag state. These states need to be expanded but are currently as follows. (TODO add all states)

#### Colors
The colors are listed most important to least in cases where multiple are displayed.
- Orange: Repair (meatball) flag
- Black: Black flag
- Gray: Furled black flag
- Red: Red flag
- Yellow: Yellow or yellow waving flag
- White: White flag
- Gray: Checkered flag
- Green: Green, green held, or no previous flag

### MPH
The current speed converted to miles per hour.

### Gear
The current gear, R for reverse and N for neutral.

### Position
The player's car's current running order position in their class followed by the number of registered drivers in the race. (TODO better handle multi-class racing)

### Laps / Time Remaining
If the race has under 10,000 laps the number of laps started followed by length of the session in laps is displayed. If the session is under 10,000 hours, the time remaining in the race is displayed as MM:SS (TODO add hours). If both are over 10,000 the number of started laps is displayed.

### RPM
The engine's rate in rotations per minute.

### Input Bars
The clutch, brake, and throttle pedals and steering wheel's input levels are plotted as bars from top to bottom (0-1).

### Incidents
The number of incidents for the player's team in the current session.

### Fuel Estimation
A rough estimation of laps remaining of fuel at the line using the average consumption rate for the last lap and last lap time.

### Lap Times
The driver's best lap time and last lap time in the session displayed as MM:SS.sss. Best on top.

### Tire Wears
The last checked tire wear at the middle of each of the 4 tires as a percent.