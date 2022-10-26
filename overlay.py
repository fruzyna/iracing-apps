import tkinter
from tkinter import ttk

import irsdk
from irsdk import Flags

from threading import Thread
from time import sleep
from sys import exit
from datetime import datetime as dt

# window measurements
width       = 375
height      = 285
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
    global root, canvas, flag, meatball, c1, c2, c3, c4, lap, speed, rpm, gear, position, incidents, alive, shiftCanvas, shiftInd, pedalCanvas, clutch, brake, throttle, wheel, fuel, laps, bestLap, lastLap, frontTire, tireWear, rearTire, lapLabel, time, fps, delta, pct

    # fuel mileage tracking data
    thisLap = []
    maxUse = 0
    lastUse = 0
    lastTime = 0
    lapValid = False
    contLaps = 0
    lastLapNum = -1
    tireWears = {
        'LF': -1,
        'RF': -1,
        'LR': -1,
        'RR': -1
    }
    sinceTireChange = {
        'LF': -1,
        'RF': -1,
        'LR': -1,
        'RR': -1
    }

    # connect to ir service
    ir = irsdk.IRSDK()
    ir.startup()

    while alive:
        try:
            # inner loop reads ir at 100 hz
            if ir['IsOnTrack']:
                # format gear
                g = ir['Gear']
                if (g < 0):
                    g = 'R'
                elif g == 0:
                    g = 'N'
                gear.config(text=g)

                # various numeric values
                now = dt.now()
                revs = ir['RPM']
                last = ir['LapLastLapTime']
                my_inc = ir['PlayerCarMyIncidentCount']
                team_inc = ir['PlayerCarTeamIncidentCount']
                rem_rps = ir['FastRepairAvailable']
                tot_rps = ir['FastRepairUsed'] + rem_rps
                if team_inc > my_inc:
                    my_inc = f'{my_inc} ({team_inc})'
                d = ir['LapDeltaToBestLap']
                idx = ir['DriverInfo']['DriverCarIdx']
                
                if lastLapNum < 0:
                    lastLapNum = ir['Lap']
                if last > 0 and lastTime != last:
                    lastTime = last

                lastRemLaps = '-'
                minRemLaps = '-'
                last_fpl = lastUse * lastTime / 3600
                max_fpl = maxUse * lastTime / 3600
                if last_fpl > 0:
                    lastRemLaps = round(ir['FuelLevel'] / last_fpl, 1)
                if max_fpl > 0:
                    minRemLaps = round(ir['FuelLevel'] / max_fpl, 1)
                # TODO: estimate fuel needed to finish
                # TODO: estimate laps remaining in timed races

                # fill basic fields
                speed.config(text=round(ir['Speed'] * 2.23694, 1))
                rpm.config(text=int(revs))
                incidents.config(text=my_inc)
                totalEntries = len(set([d['CarIdx'] for d in ir['DriverInfo']['Drivers'] if d['CarIsPaceCar'] == 0 and d['IsSpectator'] == 0]))
                position.config(text=f"{ir['PlayerCarClassPosition']}/{totalEntries}")
                bestLap.config(text=formatSeconds(ir['LapBestLapTime'], 3))
                lastLap.config(text=formatSeconds(last, 3))
                time.config(text=now.strftime('%H:%M'))
                fps.config(text=int(ir['FrameRate']))
                pct.config(text=f"{int(ir['LapDistPct'] * 100)}%")
                fuel.config(text=f"{minRemLaps} {lastRemLaps}")
                laps.config(text=contLaps)

                # lap time delta
                if d == 0:
                    delta.config(text='')
                elif d < 0:
                    delta.config(text=f'{d:.3f}', foreground='green')
                else:
                    delta.config(text=f'{d:.3f}', foreground='red')

                # display fast repairs if race has them
                #if tot_rps > 0:
                #    repairs.config(text=f"{rem_rps}/{tot_rps}")
                #else:
                #    repairs.config(text='')

                # laps are displayed as time if more than 10k
                if ir['SessionLapsTotal'] < 10000:
                    lap.config(text=f"{ir['Lap']}/{ir['SessionLapsTotal']}")
                    if ir['SessionTimeRemain'] < 100000:
                        lapLabel.config(text=formatSeconds(ir['SessionTimeRemain']))
                    else:
                        lapLabel.config(text='Lap')
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

                # determine if this lap should still be counted
                if (flagColor != 'green' and flagColor != 'white') or ir['OnPitRoad']:
                    lapValid = False

                if ir['OnPitRoad']:
                    for tire in tireWears:
                        if ir[f'{tire}wearM'] != tireWears[tire]:
                            sinceTireChange[tire] = 0
                            tireWears[tire] = ir[f'{tire}wearM']

                    frontTire.config(text=f"{round(100*tireWears['LF'], 1)} {round(100*tireWears['RF'], 1)}")
                    tireWear.config(text=f"Tire Wear (last %)")
                    rearTire.config(text=f"{round(100*tireWears['LR'], 1)} {round(100*tireWears['RR'], 1)}")
                else:
                    frontTire.config(text=f"{sinceTireChange['LF']} {sinceTireChange['RF']}")
                    tireWear.config(text=f"Tire Wear (laps)")
                    rearTire.config(text=f"{sinceTireChange['LR']} {sinceTireChange['RR']}")

                if ir['Lap'] > lastLapNum:
                    if lapValid:
                        contLaps += 1
                        for tire in tireWears:
                            sinceTireChange[tire] += 1

                        if len(thisLap) > 0:
                            lastUse = sum(thisLap) / len(thisLap)
                            if lastUse > maxUse:
                                maxUse = lastUse
                    else:
                        contLaps = 0

                    thisLap = []
                    lapValid = True
                    lastLapNum = ir['Lap']

                # log fuel level
                thisLap.append(ir['FuelUsePerHour'])

                root.deiconify()
                root.update()
                sleep(0.01)
            else:
                lapValid = False
                root.withdraw()
                sleep(3)
                
        except AttributeError:
            root.withdraw()
            sleep(3)

            ir = irsdk.IRSDK()
            ir.startup()

        except KeyboardInterrupt:
            alive = False
            sleep(3)
            root.destroy()
            exit(0)

# builds the overlay tkinter window on start
def build_window():
    global root, canvas, flag, meatball, c1, c2, c3, c4, lap, speed, rpm, gear, position, incidents, alive, shiftCanvas, shiftInd, pedalCanvas, clutch, brake, throttle, steer, fuel, laps, bestLap, lastLap, frontTire, tireWear, rearTire, lapLabel, time, fps, delta, pct

    # transparent borderless window at bottom left of middle display
    root = tkinter.Tk()
    root.attributes('-transparentcolor', 'purple')
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.geometry(f"{width}x{height}+200+775")
    root.configure(background='purple')
    root.tk_setPalette(background='purple', foreground='white')

    # shift indicator
    shiftCanvas = tkinter.Canvas(root, width=width, height=shiftHeight)
    shiftCanvas.pack(side=tkinter.TOP)
    shiftInd = shiftCanvas.create_rectangle(0, 0, width, shiftHeight)

    # numbers grid frame
    frame = tkinter.Frame(root)
    frame.pack(side=tkinter.BOTTOM)

    # time
    timeFrame = tkinter.Frame(frame)
    timeFrame.grid(column=0, row=0)
    time = ttk.Label(timeFrame, text="XX:YY", font=fontMedium, foreground='orange', background='purple')
    time.pack(side=tkinter.TOP)

    # flag box
    canvas = tkinter.Canvas(frame, width=flagWidth, height=flagHeight)
    canvas.grid(column=0, row=1)
    flag = canvas.create_rectangle(0, 0, flagWidth, flagHeight, fill='green')
    c1 = canvas.create_rectangle(0, 0, flagWidth / 2, flagHeight / 2, fill='black')
    c2 = canvas.create_rectangle(0, flagHeight / 2, flagWidth / 2, flagHeight, fill='white')
    c3 = canvas.create_rectangle(flagWidth / 2, 0, flagWidth, flagHeight / 2, fill='white')
    c4 = canvas.create_rectangle(flagWidth / 2, flagHeight / 2, flagWidth, flagHeight, fill='black')
    meatball = canvas.create_oval(flagWidth / 2 - flagHeight / 3, flagHeight / 6, flagWidth / 2 + flagHeight / 3, 5 / 6 * flagHeight, fill='orange')

    # laps / time remaining
    lapFrame = tkinter.Frame(frame)
    lapFrame.grid(column=0, row=2)
    lap = ttk.Label(lapFrame, text="XX/YY", font=fontLarge, foreground='orange', background='purple')
    lap.pack(side=tkinter.TOP)
    lapLabel = ttk.Label(lapFrame, text="Lap", foreground='orange', background='purple')
    lapLabel.pack(side=tkinter.BOTTOM)

    # fuel estimation
    fuelFrame = tkinter.Frame(frame)
    fuelFrame.grid(column=0, row=3)
    fuel = ttk.Label(fuelFrame, text="XX YY", font=fontSmall, foreground='orange', background='purple')
    fuel.pack(side=tkinter.TOP)
    ttk.Label(fuelFrame, text="Laps Rem / Grn", foreground='orange', background='purple').pack(side=tkinter.TOP)
    laps = ttk.Label(fuelFrame, text="XX YY", font=fontSmall, foreground='orange', background='purple')
    laps.pack(side=tkinter.BOTTOM)

    # framerate
    fpsFrame = tkinter.Frame(frame)
    fpsFrame.grid(column=1, row=0)
    fps = ttk.Label(fpsFrame, text="XX", font=fontSmall, foreground='orange', background='purple')
    fps.pack(side=tkinter.LEFT)
    ttk.Label(fpsFrame, text="fps", foreground='orange', background='purple').pack(side=tkinter.RIGHT)

    # speed in MPH
    speedFrame = tkinter.Frame(frame)
    speedFrame.grid(column=1, row=1)
    speed = ttk.Label(speedFrame, text="XXX", font=fontMedium, foreground='orange', background='purple')
    speed.pack(side=tkinter.TOP)
    ttk.Label(speedFrame, text="MPH", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # engine RPM
    rpmFrame = tkinter.Frame(frame)
    rpmFrame.grid(column=1, row=2)
    rpm = ttk.Label(rpmFrame, text="XXXX", font=fontMedium, foreground='orange', background='purple')
    rpm.pack(side=tkinter.TOP)
    ttk.Label(rpmFrame, text="RPM", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # tire wears (middle)
    tireFrame = tkinter.Frame(frame)
    tireFrame.grid(column=1, row=3)
    frontTire = ttk.Label(tireFrame, text="XX% YY%", font=fontSmall, foreground='orange', background='purple')
    frontTire.pack(side=tkinter.TOP)
    tireWear = ttk.Label(tireFrame, text="Tire Wear", foreground='orange', background='purple')
    tireWear.pack(side=tkinter.TOP)
    rearTire = ttk.Label(tireFrame, text="XX% YY%", font=fontSmall, foreground='orange', background='purple')
    rearTire.pack(side=tkinter.BOTTOM)

    # lap percent
    pctFrame = tkinter.Frame(frame)
    pctFrame.grid(column=2, row=0)
    pct = ttk.Label(pctFrame, text="XX%", font=fontSmall, foreground='orange', background='purple')
    pct.pack(side=tkinter.TOP)

    # current gear
    gear = ttk.Label(frame, text="X", font=fontXLarge, foreground='orange', background='purple')
    gear.grid(column=2, row=1)

    # pedal and wheel input bars
    pedalCanvas = tkinter.Canvas(frame, width=inputWidth * 4, height=inputHeight)
    pedalCanvas.grid(column=2, row=2)
    clutch   = pedalCanvas.create_rectangle(0,              0, inputWidth,     inputHeight)
    brake    = pedalCanvas.create_rectangle(inputWidth,     0, inputWidth * 2, inputHeight)
    throttle = pedalCanvas.create_rectangle(inputWidth * 2, 0, inputWidth * 3, inputHeight)
    steer    = pedalCanvas.create_rectangle(inputWidth * 3, 0, inputWidth * 4, inputHeight)

    # delta
    deltaFrame = tkinter.Frame(frame)
    deltaFrame.grid(column=3, row=0)
    delta = ttk.Label(deltaFrame, text="X.YYY", font=fontMedium, foreground='orange', background='purple')
    delta.pack(side=tkinter.TOP)

    # current position
    posFrame = tkinter.Frame(frame)
    posFrame.grid(column=3, row=1)
    position = ttk.Label(posFrame, text="XX/YY", font=fontMedium, foreground='orange', background='purple')
    position.pack(side=tkinter.TOP)
    ttk.Label(posFrame, text="Place", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # incidents count
    xFrame = tkinter.Frame(frame)
    xFrame.grid(column=3, row=2)
    incidents = ttk.Label(xFrame, text="X", font=fontLarge, foreground='orange', background='purple')
    incidents.pack(side=tkinter.TOP)
    ttk.Label(xFrame, text="Incidents", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

    # best and last lap times
    timeFrame = tkinter.Frame(frame)
    timeFrame.grid(column=3, row=3)
    bestLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
    bestLap.pack(side=tkinter.TOP)
    ttk.Label(timeFrame, text="Lap Times", foreground='orange', background='purple').pack(side=tkinter.TOP)
    lastLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
    lastLap.pack(side=tkinter.BOTTOM)

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
