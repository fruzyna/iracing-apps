import tkinter
from tkinter import ttk

import irsdk
from irsdk import Flags, PaceMode

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


class overlay(object):

    def init(self):
        self.shiftCanvas = None
        self.shiftInd = None

        self.time = None

        self.canvas = None
        self.flag = None
        self.c1 = None
        self.c2 = None
        self.c3 = None
        self.c4 = None
        self.meatball = None

        self.lap = None
        self.lapLabel = None

        self.fuel = None
        self.laps = None

        self.fps = None
        self.speed = None
        self.rpm = None

        self.frontTire = None
        self.tireWear = None
        self.rearTire = None

        self.pct = None
        self.gear = None

        self.pedalCanvas = None
        self.clutch = None
        self.brake = None
        self.throttle = None
        self.steer = None

        self.delta = None
        self.position = None
        self.incidents = None
        self.bestLap = None
        self.lastLap = None
        
        self.alive = False
        
        self.lapValid = False
        

    def setup_window(self):
        # transparent borderless window at bottom left of middle display
        self.root = tkinter.Tk()
        self.root.attributes('-transparentcolor', 'purple')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.geometry(f"{width}x{height}+200+775")
        self.root.configure(background='purple')
        self.root.tk_setPalette(background='purple', foreground='white')

        # shift indicator
        self.shiftCanvas = tkinter.Canvas(self.root, width=width, height=shiftHeight)
        self.shiftCanvas.pack(side=tkinter.TOP)
        self.shiftInd = self.shiftCanvas.create_rectangle(0, 0, width, shiftHeight)

        # numbers grid frame
        frame = tkinter.Frame(self.root)
        frame.pack(side=tkinter.BOTTOM)

        # time
        timeFrame = tkinter.Frame(frame)
        timeFrame.grid(column=0, row=0)
        self.time = ttk.Label(timeFrame, text="XX:YY", font=fontMedium, foreground='orange', background='purple')
        self.time.pack(side=tkinter.TOP)

        # flag box
        self.canvas = tkinter.Canvas(frame, width=flagWidth, height=flagHeight)
        self.canvas.grid(column=0, row=1)
        self.flag = self.canvas.create_rectangle(0, 0, flagWidth, flagHeight, fill='green')
        self.c1 = self.canvas.create_rectangle(0, 0, flagWidth / 2, flagHeight / 2, fill='black')
        self.c2 = self.canvas.create_rectangle(0, flagHeight / 2, flagWidth / 2, flagHeight, fill='white')
        self.c3 = self.canvas.create_rectangle(flagWidth / 2, 0, flagWidth, flagHeight / 2, fill='white')
        self.c4 = self.canvas.create_rectangle(flagWidth / 2, flagHeight / 2, flagWidth, flagHeight, fill='black')
        self.meatball = self.canvas.create_oval(flagWidth / 2 - flagHeight / 3, flagHeight / 6, flagWidth / 2 + flagHeight / 3, 5 / 6 * flagHeight, fill='orange')

        # laps / time remaining
        lapFrame = tkinter.Frame(frame)
        lapFrame.grid(column=0, row=2)
        self.lap = ttk.Label(lapFrame, text="XX/YY", font=fontLarge, foreground='orange', background='purple')
        self.lap.pack(side=tkinter.TOP)
        self.lapLabel = ttk.Label(lapFrame, text="Lap", foreground='orange', background='purple')
        self.lapLabel.pack(side=tkinter.BOTTOM)

        # fuel estimation
        fuelFrame = tkinter.Frame(frame)
        fuelFrame.grid(column=0, row=3)
        self.fuel = ttk.Label(fuelFrame, text="XX YY", font=fontSmall, foreground='orange', background='purple')
        self.fuel.pack(side=tkinter.TOP)
        ttk.Label(fuelFrame, text="Laps Rem / Grn", foreground='orange', background='purple').pack(side=tkinter.TOP)
        self.laps = ttk.Label(fuelFrame, text="XX YY", font=fontSmall, foreground='orange', background='purple')
        self.laps.pack(side=tkinter.BOTTOM)

        # framerate
        fpsFrame = tkinter.Frame(frame)
        fpsFrame.grid(column=1, row=0)
        self.fps = ttk.Label(fpsFrame, text="XX", font=fontSmall, foreground='orange', background='purple')
        self.fps.pack(side=tkinter.LEFT)
        ttk.Label(fpsFrame, text="fps", foreground='orange', background='purple').pack(side=tkinter.RIGHT)

        # speed in MPH
        speedFrame = tkinter.Frame(frame)
        speedFrame.grid(column=1, row=1)
        self.speed = ttk.Label(speedFrame, text="XXX", font=fontMedium, foreground='orange', background='purple')
        self.speed.pack(side=tkinter.TOP)
        ttk.Label(speedFrame, text="MPH", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

        # engine RPM
        rpmFrame = tkinter.Frame(frame)
        rpmFrame.grid(column=1, row=2)
        self.rpm = ttk.Label(rpmFrame, text="XXXX", font=fontMedium, foreground='orange', background='purple')
        self.rpm.pack(side=tkinter.TOP)
        ttk.Label(rpmFrame, text="RPM", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

        # tire wears (middle)
        tireFrame = tkinter.Frame(frame)
        tireFrame.grid(column=1, row=3)
        self.frontTire = ttk.Label(tireFrame, text="XX% YY%", font=fontSmall, foreground='orange', background='purple')
        self.frontTire.pack(side=tkinter.TOP)
        self.tireWear = ttk.Label(tireFrame, text="Tire Wear", foreground='orange', background='purple')
        self.tireWear.pack(side=tkinter.TOP)
        self.rearTire = ttk.Label(tireFrame, text="XX% YY%", font=fontSmall, foreground='orange', background='purple')
        self.rearTire.pack(side=tkinter.BOTTOM)

        # lap percent
        pctFrame = tkinter.Frame(frame)
        pctFrame.grid(column=2, row=0)
        self.pct = ttk.Label(pctFrame, text="XX%", font=fontSmall, foreground='orange', background='purple')
        self.pct.pack(side=tkinter.TOP)

        # current gear
        self.gear = ttk.Label(frame, text="X", font=fontXLarge, foreground='orange', background='purple')
        self.gear.grid(column=2, row=1)

        # pedal and wheel input bars
        self.pedalCanvas = tkinter.Canvas(frame, width=inputWidth * 4, height=inputHeight)
        self.pedalCanvas.grid(column=2, row=2)
        self.clutch   = self.pedalCanvas.create_rectangle(0,              0, inputWidth,     inputHeight)
        self.brake    = self.pedalCanvas.create_rectangle(inputWidth,     0, inputWidth * 2, inputHeight)
        self.throttle = self.pedalCanvas.create_rectangle(inputWidth * 2, 0, inputWidth * 3, inputHeight)
        self.steer    = self.pedalCanvas.create_rectangle(inputWidth * 3, 0, inputWidth * 4, inputHeight)

        # delta
        deltaFrame = tkinter.Frame(frame)
        deltaFrame.grid(column=3, row=0)
        self.delta = ttk.Label(deltaFrame, text="X.YYY", font=fontMedium, foreground='orange', background='purple')
        self.delta.pack(side=tkinter.TOP)

        # current position
        posFrame = tkinter.Frame(frame)
        posFrame.grid(column=3, row=1)
        self.position = ttk.Label(posFrame, text="XX/YY", font=fontMedium, foreground='orange', background='purple')
        self.position.pack(side=tkinter.TOP)
        ttk.Label(posFrame, text="Place", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

        # incidents count
        xFrame = tkinter.Frame(frame)
        xFrame.grid(column=3, row=2)
        self.incidents = ttk.Label(xFrame, text="X", font=fontLarge, foreground='orange', background='purple')
        self.incidents.pack(side=tkinter.TOP)
        ttk.Label(xFrame, text="Incidents", foreground='orange', background='purple').pack(side=tkinter.BOTTOM)

        # best and last lap times
        timeFrame = tkinter.Frame(frame)
        timeFrame.grid(column=3, row=3)
        self.bestLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
        self.bestLap.pack(side=tkinter.TOP)
        ttk.Label(timeFrame, text="Lap Times", foreground='orange', background='purple').pack(side=tkinter.TOP)
        self.lastLap = ttk.Label(timeFrame, text="X:XX", font=fontSmall, foreground='orange', background='purple')
        self.lastLap.pack(side=tkinter.BOTTOM)

        self.alive = True

    def hard_reset(self):
        self.soft_reset()
        self.maxUse = 0
        self.lastUse = 0
        self.lastTime = 0

    def soft_reset(self):
        self.thisLap = []
        self.lapValid = False
        self.lapGreen = False
        self.contLaps = 0
        self.tireWears = {
            'LF': -1,
            'RF': -1,
            'LR': -1,
            'RR': -1
        }
        self.sinceTireChange = {
            'LF': 0,
            'RF': 0,
            'LR': 0,
            'RR': 0
        }
        self.lastLapNum = -1
        self.lastNotGreen = 0

    def update(self, ir):
        # inner loop reads ir at 100 hz
        if ir['IsOnTrack']:
            self.onTrack(ir)

            # show and draw window every 10 ms
            self.root.deiconify()
            self.root.update()
            sleep(0.01)
        else:
            self.soft_reset()

            # hide window and wait 3 s
            self.root.withdraw()
            sleep(3)

    def onTrack(self, ir):
        # format gear
        g = ir['Gear']
        if (g < 0):
            g = 'R'
        elif g == 0:
            g = 'N'
        self.gear.config(text=g)

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
        
        if self.lastLapNum < 0:
            self.lastLapNum = ir['Lap']
        if last > 0 and self.lastTime != last:
            self.lastTime = last

        lastRemLaps = self.estimateRemainingLaps(ir['FuelLevel'], self.lastUse)
        minRemLaps = self.estimateRemainingLaps(ir['FuelLevel'], self.maxUse)
        # TODO: estimate fuel needed to finish
        # TODO: estimate laps remaining in timed races

        # fill basic fields
        self.speed.config(text=round(ir['Speed'] * 2.23694, 1))
        self.rpm.config(text=int(revs))
        self.incidents.config(text=my_inc)
        totalEntries = len(set([d['CarIdx'] for d in ir['DriverInfo']['Drivers'] if d['CarIsPaceCar'] == 0 and d['IsSpectator'] == 0]))
        self.position.config(text=f"{ir['PlayerCarClassPosition']}/{totalEntries}")
        self.bestLap.config(text=formatSeconds(ir['LapBestLapTime'], 3))
        self.lastLap.config(text=formatSeconds(last, 3))
        self.time.config(text=now.strftime('%H:%M'))
        self.fps.config(text=int(ir['FrameRate']))
        self.pct.config(text=f"{int(ir['LapDistPct'] * 100)}%")
        self.fuel.config(text=f"{minRemLaps} {lastRemLaps}")
        self.laps.config(text=self.contLaps)

        # lap time delta
        if d == 0:
            self.delta.config(text='')
        elif d < 0:
            self.delta.config(text=f'{d:.3f}', foreground='green')
        else:
            self.delta.config(text=f'{d:.3f}', foreground='red')

        # display fast repairs if race has them
        #if tot_rps > 0:
        #    self.repairs.config(text=f"{rem_rps}/{tot_rps}")
        #else:
        #    self.repairs.config(text='')

        # laps are displayed as time if more than 10k
        if ir['SessionLapsTotal'] < 10000:
            self.lap.config(text=f"{ir['Lap']}/{ir['SessionLapsTotal']}")
            if ir['SessionTimeRemain'] < 100000:
                self.lapLabel.config(text=formatSeconds(ir['SessionTimeRemain']))
            else:
                self.lapLabel.config(text='Lap')
        elif ir['SessionTimeRemain'] < 100000:
            self.lap.config(text=formatSeconds(ir['SessionTimeRemain']))
            self.lapLabel.config(text=f"Lap {ir['Lap']}")
        else:
            self.lap.config(text=ir['Lap'])
            self.lapLabel.config(text='Laps')

        # determine flag color
        flagColor, meatball = self.getFlag(ir['SessionFlags'])
        if flagColor == 'checkered':
            self.canvas.itemconfig(self.c1, state='normal')
            self.canvas.itemconfig(self.c2, state='normal')
            self.canvas.itemconfig(self.c3, state='normal')
            self.canvas.itemconfig(self.c4, state='normal')
        else:
            self.canvas.itemconfig(self.flag, fill=flagColor)
            self.canvas.itemconfig(self.c1, state='hidden')
            self.canvas.itemconfig(self.c2, state='hidden')
            self.canvas.itemconfig(self.c3, state='hidden')
            self.canvas.itemconfig(self.c4, state='hidden')
        if meatball:
            self.canvas.itemconfig(self.meatball, state='normal')
        else:
            self.canvas.itemconfig(self.meatball, state='hidden')

        # determine shift indicator color
        color = self.getShiftIndicator(revs, ir)
        if color == 'orange':
            self.root.configure(background='red')
        else:
            self.root.configure(background='purple')
        ind = ir['ShiftIndicatorPct']
        self.shiftCanvas.itemconfig(self.shiftInd, fill=color)
        self.shiftCanvas.coords(self.shiftInd, 0, 0, width * ind, shiftHeight)

        # draw input bars
        self.pedalCanvas.itemconfig(self.clutch, fill='blue')
        self.pedalCanvas.coords(self.clutch,   0,              0, inputWidth,     inputHeight * (1 - ir['Clutch']))
        self.pedalCanvas.itemconfig(self.brake, fill='red')
        self.pedalCanvas.coords(self.brake,    inputWidth,     0, inputWidth * 2, inputHeight * ir['Brake'])
        self.pedalCanvas.itemconfig(self.throttle, fill='green')
        self.pedalCanvas.coords(self.throttle, inputWidth * 2, 0, inputWidth * 3, inputHeight * ir['Throttle'])
        self.pedalCanvas.itemconfig(self.steer, fill='orange')
        self.pedalCanvas.coords(self.steer,    inputWidth * 3, 0, inputWidth * 4, (inputHeight * ir['SteeringWheelAngle'] / ir['SteeringWheelAngleMax'] + inputHeight) / 2)

        # determine if this lap should still be counted
        if ir['PaceMode'] != PaceMode.not_pacing or ir['OnPitRoad']:
            if self.lapGreen:
                for tire in self.tireWears:
                    self.sinceTireChange[tire] += ir['LapDistPct'] - self.lastNotGreen
            self.lapValid = False
            self.lastNotGreen = ir['LapDistPct']
        else:
            self.lapGreen = True

        if ir['OnPitRoad']:
            self.onPit(ir)
        else:
            self.frontTire.config(text=f"{round(self.sinceTireChange['LF'], 1)} {round(self.sinceTireChange['RF'], 1)}")
            self.tireWear.config(text=f"Tire Wear (laps)")
            self.rearTire.config(text=f"{round(self.sinceTireChange['LR'], 1)} {round(self.sinceTireChange['RR'], 1)}")

        if ir['Lap'] > self.lastLapNum:
            self.incrementLap(ir['Lap'])

        # log fuel level
        self.thisLap.append(ir['FuelUsePerHour'])

    def onPit(self, ir):
        if ir['PlayerCarInPitStall']:
            for tire in self.tireWears:
                self.tireWears[tire] = ir[f'{tire}wearM']
                if ir[f'dp{tire[0]}TireChange'] or ir[f'dp{tire}TireChange']:
                    self.sinceTireChange[tire] = 0

        self.frontTire.config(text=f"{round(100*self.tireWears['LF'], 1)} {round(100*self.tireWears['RF'], 1)}")
        self.tireWear.config(text=f"Tire Wear (last %)")
        self.rearTire.config(text=f"{round(100*self.tireWears['LR'], 1)} {round(100*self.tireWears['RR'], 1)}")
        
    def getShiftIndicator(self, revs, ir):
        if revs >= ir['DriverInfo']['DriverCarRedLine']:
            return 'blue'
        elif revs >= ir['DriverInfo']['DriverCarSLBlinkRPM']:
            return 'red'
        elif revs >= ir['DriverInfo']['DriverCarSLLastRPM']:
            return 'orange'
        elif revs >= ir['DriverInfo']['DriverCarSLShiftRPM']:
            return 'yellow'
        elif revs >= ir['DriverInfo']['DriverCarSLFirstRPM']:
            return 'green'
        return 'purple'
        
    def getFlag(self, flag):
        if flag & Flags.checkered:
            flagColor = 'checkered'
        else:
            if flag & Flags.blue:
                flagColor = 'blue'
            elif flag & Flags.black:
                flagColor = 'black'
            elif flag & Flags.furled:
                flagColor = 'gray'
            elif flag & Flags.red:
                flagColor = 'red'
            elif flag & Flags.white:
                flagColor = 'white'
            elif flag & Flags.yellow or flag & Flags.yellow_waving or flag & Flags.caution or flag & Flags.caution_waving or flag & Flags.debris:
                flagColor = 'yellow'
            elif flag & Flags.green or flag & Flags.green_held:
                flagColor = 'green'
            else:
                flagColor = 'green'
                
        return flagColor, flag & Flags.repair
        
    def incrementLap(self, lap):
        if self.lapGreen:
            for tire in self.sinceTireChange:
                self.sinceTireChange[tire] += 1 - self.lastNotGreen

        if self.lapValid:
            self.contLaps += 1

            if len(self.thisLap) > 0:
                self.lastUse = sum(self.thisLap) / len(self.thisLap)
                if self.lastUse > self.maxUse:
                    self.maxUse = self.lastUse
        else:
            # TODO: don't reset until starting a valid lap
            self.contLaps = 0

        self.thisLap = []
        self.lapValid = True
        self.lastLapNum = lap
        self.lastNotGreen = 0
        
    def estimateRemainingLaps(self, fuelLevel, usage):
        fpl = self.maxUse * self.lastTime / 3600
        if fpl > 0:
            return round(fuelLevel / fpl, 1)
        return '-'

    def renderThread(self):
        # connect to ir service
        ir = irsdk.IRSDK()
        ir.startup()

        self.hard_reset()
        while self.alive:
            try:
                self.update(ir)
                
            except AttributeError:
                self.root.withdraw()
                self.hard_reset()
                sleep(3)

                ir = irsdk.IRSDK()
                ir.startup()

            except KeyboardInterrupt:
                self.close()
                
    def loop(self):
        self.root.mainloop()

    def close(self):
        self.alive = False
        sleep(3)
        self.root.destroy()


if __name__ == '__main__':
    overlay = overlay()
    overlay.setup_window()
    
    Thread(target=overlay.renderThread, daemon=True).start()
    
    try:
        overlay.loop()
    except KeyboardInterrupt:
        overlay.close()