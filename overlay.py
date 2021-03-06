import tkinter
from tkinter import ttk

import irsdk
from irsdk import Flags

from threading import Thread
from time import sleep
from sys import exit

# window measurements
width       = 375
height      = 250
shiftHeight = 15
inputWidth  = 10
inputHeight = 75
flagWidth   = 100
flagHeight  = 75

# fonts
fontXLarge = ('Arial', 50)
fontLarge  = ('Arial', 25)
fontMedium = ('Arial', 20)
fontSmall  = ('Arial', 15)
fontXSmall = ('Arial', 12)

# format seconds into MM:SS with optional milliseconds
def formatSeconds(secs, roundTo=0):
    if secs <= 0:
        return "0:00"
    mins = int(secs // 60)
    secs = secs % 60
    if roundTo == 0:
        secs = int(secs)
    else:
        secs = round(secs, roundTo)
    if secs < 10:
        secs = f"0{secs}"
    if mins >= 60:
        hrs = int(mins // 60)
        mins = int(mins % 60)
        if mins < 10:
            mins = f"0{mins}"
        time = f"{hrs}:{mins}:{secs}"
    else:
        time = f"{mins}:{secs}"
    return time

# iracing thread that reads ir and adjusts the window
def irThread():
    global root, canvas, flag, meatball, c1, c2, c3, c4, lap, speed, rpm, gear, position, incidents, alive, shiftCanvas, shiftInd, pedalCanvas, clutch, brake, throttle, wheel, fuel, bestLap, lastLap, frontTire, rearTire, lapLabel

    # fuel mileage tracking data
    thisLap = []
    pastLap = []
    currLap = -1
    lastTime = -1
    lapValid = True

    # outer loop catches crashes from iracing not running
    while alive:
        try:
            ir = irsdk.IRSDK()
            ir.startup()
            
            # inner loop reads ir at 100 hz
            while alive:
                # format gear
                g = ir['Gear']
                if (g < 0):
                    g = 'R'
                elif g == 0:
                    g = 'N'
                gear.config(text=g)

                # various numeric values
                revs = ir['RPM']
                last = ir['LapLastLapTime']
                speed.config(text=round(ir['Speed'] * 2.23694, 1))
                rpm.config(text=int(revs))
                incidents.config(text=ir['PlayerCarTeamIncidentCount'])
                totalEntries = len(set([d['CarIdx'] for d in ir['DriverInfo']['Drivers'] if d['CarIsPaceCar'] == 0 and d['IsSpectator'] == 0]))
                position.config(text=f"{ir['PlayerCarClassPosition']}/{totalEntries}")
                bestLap.config(text=formatSeconds(ir['LapBestLapTime'], 3))
                lastLap.config(text=formatSeconds(last, 3))
                frontTire.config(text=f"{round(100*ir['LFwearM'], 1)}% {round(100*ir['RFwearM'], 1)}%")
                rearTire.config(text=f"{round(100*ir['LRwearM'], 1)}% {round(100*ir['RRwearM'], 1)}%")

                # laps are displayed as time if more than 10k
                if ir['SessionLapsTotal'] < 10000:
                    lap.config(text=f"{ir['Lap']}/{ir['SessionLapsTotal']}")
                    if ir['SessionTimeRemain'] < 100000:
                        lapLabel.config(text=formatSeconds(ir['SessionTimeRemain']))
                    else:
                        lapLabel.config(text='Laps')
                elif ir['SessionTimeRemain'] < 100000:
                    lap.config(text=formatSeconds(ir['SessionTimeRemain']))
                    lapLabel.config(text=f"Lap {ir['Lap']}")
                else:
                    lap.config(text=ir['Lap'])
                    lapLabel.config(text='Laps')

                # determine flag color
                val = ir['SessionFlags']
                flagColor = 'green'
                if val & Flags.checkered:
                    flagColor = 'checkered'
                    canvas.itemconfig(c1, state='normal')
                    canvas.itemconfig(c2, state='normal')
                    canvas.itemconfig(c3, state='normal')
                    canvas.itemconfig(c4, state='normal')
                else:
                    if val & Flags.blue:
                        flagColor = 'blue'
                    elif val & Flags.black:
                        flagColor = 'black'
                    elif val & Flags.furled:
                        flagColor = 'gray'
                    elif val & Flags.red:
                        flagColor = 'red'
                    elif val & Flags.white:
                        flagColor = 'white'
                    elif val & Flags.yellow or val & Flags.yellow_waving or val & Flags.caution or val & Flags.caution_waving or val & Flags.debris:
                        flagColor = 'yellow'
                    elif val & Flags.green or val & Flags.green_held:
                        flagColor = 'green'
                    else:
                        flagColor = 'green'
                    canvas.itemconfig(flag, fill=flagColor)
                    canvas.itemconfig(c1, state='hidden')
                    canvas.itemconfig(c2, state='hidden')
                    canvas.itemconfig(c3, state='hidden')
                    canvas.itemconfig(c4, state='hidden')
                if val & Flags.repair:
                    canvas.itemconfig(meatball, state='normal')
                else:
                    canvas.itemconfig(meatball, state='hidden')

                # determine shift indicator color
                color = 'purple'
                if revs >= ir['DriverInfo']['DriverCarRedLine']:
                    color = 'blue'
                elif revs >= ir['DriverInfo']['DriverCarSLBlinkRPM']:
                    color = 'red'
                elif revs >= ir['DriverInfo']['DriverCarSLLastRPM']:
                    color = 'orange'
                elif revs >= ir['DriverInfo']['DriverCarSLShiftRPM']:
                    color = 'yellow'
                elif revs >= ir['DriverInfo']['DriverCarSLFirstRPM']:
                    color = 'green'
                if color == 'orange':
                    root.configure(background='red')
                else:
                    root.configure(background='purple')
                ind = ir['ShiftIndicatorPct']
                shiftCanvas.itemconfig(shiftInd, fill=color)
                shiftCanvas.coords(shiftInd, 0, 0, width * ind, shiftHeight)

                # draw input bars
                pedalCanvas.itemconfig(clutch, fill='blue')
                pedalCanvas.coords(clutch,   0,              0, inputWidth,     inputHeight * (1 - ir['Clutch']))
                pedalCanvas.itemconfig(brake, fill='red')
                pedalCanvas.coords(brake,    inputWidth,     0, inputWidth * 2, inputHeight * ir['Brake'])
                pedalCanvas.itemconfig(throttle, fill='green')
                pedalCanvas.coords(throttle, inputWidth * 2, 0, inputWidth * 3, inputHeight * ir['Throttle'])
                pedalCanvas.itemconfig(steer, fill='orange')
                pedalCanvas.coords(steer,    inputWidth * 3, 0, inputWidth * 4, (inputHeight * ir['SteeringWheelAngle'] / ir['SteeringWheelAngleMax'] + inputHeight) / 2)

                # at end of lap calculate fuel
                if currLap != ir['Lap']:
                    currLap = ir['Lap']
                    pastLap = thisLap
                    thisLap = []

                if lastTime != last:
                    lastTime = last
                    avg = sum(pastLap) / len(pastLap)
                    fps = avg / 3600
                    fpl = fps * last
                    remLaps = ir['FuelLevel'] * 0.75 / fpl
                    if remLaps > 0:
                        fuel.config(text=round(remLaps, 1))
                    lapValid = True

                # log fuel level
                thisLap.append(ir['FuelUsePerHour'])

                # determine if this lap should still be counted
                if (flagColor != 'green' and flagColor != 'white') or not ir['IsOnTrack'] or ir['OnPitRoad']:
                    lapValid = False

                # would be used for hiding overlay
                if not ir['IsOnTrack']:
                    continue

                root.update()
                sleep(0.01)
        except KeyboardInterrupt:
            alive = False
            sleep(3)
            root.destroy()
            exit(0)
        except:
            sleep(3)

# builds the overlay tkinter window on start
def build_window():
    global root, canvas, flag, meatball, c1, c2, c3, c4, lap, speed, rpm, gear, position, incidents, alive, shiftCanvas, shiftInd, pedalCanvas, clutch, brake, throttle, steer, fuel, bestLap, lastLap, frontTire, rearTire, lapLabel

    # transparent borderless window at bottom left of middle display
    root = tkinter.Tk()
    root.attributes('-transparentcolor', 'purple')
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.geometry(f"{width}x{height}+200+800")
    root.configure(background='purple')
    root.tk_setPalette(background='purple', foreground='white')

    # shift indicator
    shiftCanvas = tkinter.Canvas(root, width=width, height=shiftHeight)
    shiftCanvas.pack(side=tkinter.TOP)
    shiftInd = shiftCanvas.create_rectangle(0, 0, width, shiftHeight)

    # numbers grid frame
    frame = tkinter.Frame(root)
    frame.pack(side=tkinter.BOTTOM)

    # flag box
    canvas = tkinter.Canvas(frame, width=flagWidth, height=flagHeight)
    canvas.grid(column=0, row=0)
    flag = canvas.create_rectangle(0, 0, flagWidth, flagHeight, fill='green')
    c1 = canvas.create_rectangle(0, 0, flagWidth / 2, flagHeight / 2, fill='black')
    c2 = canvas.create_rectangle(0, flagHeight / 2, flagWidth / 2, flagHeight, fill='white')
    c3 = canvas.create_rectangle(flagWidth / 2, 0, flagWidth, flagHeight / 2, fill='white')
    c4 = canvas.create_rectangle(flagWidth / 2, flagHeight / 2, flagWidth, flagHeight, fill='black')
    meatball = canvas.create_oval(flagWidth / 2 - flagHeight / 3, flagHeight / 6, flagWidth / 2 + flagHeight / 3, 5 / 6 * flagHeight, fill='orange')

    # laps / time remaining
    lapFrame = tkinter.Frame(frame)
    lapFrame.grid(column=0, row=1)
    lap = ttk.Label(lapFrame, text="XX/YY", font=fontLarge, foreground='orange', background='purple')
    lap.pack(side=tkinter.TOP)
    lapLabel = ttk.Label(lapFrame, text="Lap", foreground='orange', background='purple')
    lapLabel.pack(side=tkinter.BOTTOM)

    # fuel estimation
    fuelFrame = tkinter.Frame(frame)
    fuelFrame.grid(column=0, row=2)
    fuel = ttk.Label(fuelFrame, text="XX", font=fontLarge, foreground='orange', background='purple')
    fuel.pack(side=tkinter.TOP)
    ttk.Label(fuelFrame, text="Laps Remaining", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # speed in MPH
    speedFrame = tkinter.Frame(frame)
    speedFrame.grid(column=1, row=0)
    speed = ttk.Label(speedFrame, text="XXX", font=fontMedium, foreground='orange', background='purple')
    speed.pack(side=tkinter.TOP)
    ttk.Label(speedFrame, text="MPH", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # engine RPM
    rpmFrame = tkinter.Frame(frame)
    rpmFrame.grid(column=1, row=1)
    rpm = ttk.Label(rpmFrame, text="XXXX", font=fontMedium, foreground='orange', background='purple')
    rpm.pack(side=tkinter.TOP)
    ttk.Label(rpmFrame, text="RPM", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # best and last lap times
    timeFrame = tkinter.Frame(frame)
    timeFrame.grid(column=1, row=2)
    bestLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
    bestLap.pack(side=tkinter.TOP)
    ttk.Label(timeFrame, text="Lap Times", foreground='orange', background='purple').pack(side=tkinter.TOP)
    lastLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
    lastLap.pack(side=tkinter.BOTTOM)

    # current gear
    gear = ttk.Label(frame, text="X", font=fontXLarge, foreground='orange', background='purple')
    gear.grid(column=2, row=0)

    # pedal and wheel input bars
    pedalCanvas = tkinter.Canvas(frame, width=inputWidth * 4, height=inputHeight)
    pedalCanvas.grid(column=2, row=1)
    clutch   = pedalCanvas.create_rectangle(0,              0, inputWidth,     inputHeight)
    brake    = pedalCanvas.create_rectangle(inputWidth,     0, inputWidth * 2, inputHeight)
    throttle = pedalCanvas.create_rectangle(inputWidth * 2, 0, inputWidth * 3, inputHeight)
    steer    = pedalCanvas.create_rectangle(inputWidth * 3, 0, inputWidth * 4, inputHeight)

    # current position
    posFrame = tkinter.Frame(frame)
    posFrame.grid(column=3, row=0)
    position = ttk.Label(posFrame, text="XX/YY", font=fontMedium, foreground='orange', background='purple')
    position.pack(side=tkinter.TOP)
    ttk.Label(posFrame, text="Place", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # incidents count
    xFrame = tkinter.Frame(frame)
    xFrame.grid(column=3, row=1)
    incidents = ttk.Label(xFrame, text="X", font=fontLarge, foreground='orange', background='purple')
    incidents.pack(side=tkinter.TOP)
    ttk.Label(xFrame, text="Incidents", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # tire wears (middle)
    tireFrame = tkinter.Frame(frame)
    tireFrame.grid(column=3, row=2)
    frontTire = ttk.Label(tireFrame, text="XX% YY%", font=fontXSmall, foreground='orange', background='purple')
    frontTire.pack(side=tkinter.TOP)
    ttk.Label(tireFrame, text="Tire Wear", foreground='orange', background='purple').pack(side=tkinter.TOP)
    rearTire = ttk.Label(tireFrame, text="XX% YY%", font=fontXSmall, foreground='orange', background='purple')
    rearTire.pack(side=tkinter.BOTTOM)

    alive = True
    thread = Thread(target=irThread).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        alive = False
        sleep(3)
        root.destroy()
        exit(0)

if __name__ == '__main__':
    build_window()
