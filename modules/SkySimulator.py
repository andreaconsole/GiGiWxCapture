#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# SkySimulator.py: entry point of SkySimulator
#
###############################################################################
###
### This file is part of SkySimulator.
###
###    Copyright (C) 2011-2013 Andrea Console  <andreaconsole@gmail.com>
###
###    This program is free software: you can redistribute it and/or modify
###    it under the terms of the GNU General Public License as published by
###    the Free Software Foundation, either version 3 of the License, or
###    (at your option) any later version.
###
###    This program is distributed in the hope that it will be useful,
###    but WITHOUT ANY WARRANTY; without even the implied warranty of
###    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
###    GNU General Public License for more details.
###
###    You should have received a copy of the GNU General Public License
###    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###
###    If you find any part of this code useful and suitable for any software
###    developed by you, I would appreciate if you mentioned me in your code.
###
################################################################################

import os
import wx
import math
sin = math.sin
cos = math.cos
import random
from PIL import Image
import time
 
class Panel1(wx.Panel):
    """class Panel1 creates a panel with an image on it, inherits wx.Panel"""
    def __init__(self, parent):
        # create the panel
        wx.Panel.__init__(self, parent)
        #wx.Panel(parent, -1, (0,0),(4000,25))
        self.SetSize((4000,4000))
        self.SetPosition((0,30))
        
        try:
            # pick an image file you have in the working folder
            # you can load .jpg  .png  .bmp  or .gif files
            image_file = '../images/skysimulator.jpg'
            self.pilImage = Image.open(image_file)
            self.bgImage = wx.EmptyImage(self.pilImage.size[0],self.pilImage.size[1])
            self.bgImage.SetData(self.pilImage.convert("RGB").tostring())
        
            bitmap = wx.BitmapFromImage(self.bgImage)
            self.bgBitmap = wx.StaticBitmap(self)
            self.bgBitmap.SetBitmap(bitmap)
        except IOError:
            print "Image file %s not found" % image_file
            raise SystemExit
        
    
        
class Controls(object):
    def __init__(self):
        drawSpeed = 500
        controlSpeed = 50
        self.frame1 = wx.Frame(None, -1, "loading title...", size=(500, 400), pos=(500,20))
        # create the class instance
        self.panel1 = wx.Panel(self.frame1,-1)
        #Panel1(self.frame1) 
        self.panel1.bg = Panel1(self.panel1)
        self.panel1.setAngle = wx.TextCtrl(self.panel1, -1, "0", (10,0),(30,22))
        self.panel1.setARdrift = wx.TextCtrl(self.panel1, -1, "5", (55,0),(30,22))
        self.panel1.setARtime = wx.TextCtrl(self.panel1, -1, "100", (90,0),(50,22))
        self.panel1.setDECdrift = wx.TextCtrl(self.panel1, -1, "10", (155,0),(30,22))
        self.panel1.setDECtime = wx.TextCtrl(self.panel1, -1, "2000", (190,0),(50,22))
        self.panel1.setAll = wx.Button(self.panel1, -1, "Set", (255,0),(35,22))
        self.panel1.setAll.Bind(wx.EVT_BUTTON, self.SetTimeAndDrift)
        self.frame1.Show(True)
        self.drawClock = wx.Timer(self.frame1)
        self.drawClock.Start(drawSpeed)
        self.frame1.Bind(wx.EVT_TIMER, self.DrawClock, self.drawClock)
        self.controlClock = wx.Timer(self.frame1)
        self.frame1.Bind(wx.EVT_TIMER, self.ControlClock, self.controlClock)
        self.controlClock.Start(controlSpeed)
        self.driftTimer = wx.StopWatch()
        
        self.ARdirection = 1
        self.DECdirection = 1
        self.commandARduration = 0
        self.commandDECduration = 0
        self.commandARstart = 0
        self.commandDECstart = 0
        self.ARdrift = -200
        self.DECdrift = -200
        low = 1      /10.0 #unit = pixel/sec
        med = 8     /10.0 #unit = pixel/sec
        hi = 16     /10.0 #unit = pixel/sec
        self.speed = [low, med, hi]
        self.actualSpeed = self.speed[0]
        self.SetTimeAndDrift(None)
        
    def SetTimeAndDrift(self, evt):
        self.maxARdrift = float(self.panel1.setARdrift.Value) 
        self.maxDECdrift = float(self.panel1.setDECdrift.Value)
        self.ARperiod = float(self.panel1.setARtime.Value)
        self.DECperiod = float(self.panel1.setDECtime.Value)
        self.angolo = float(self.panel1.setAngle.Value) * (-3.1415/180)
        title = str(round(self.angolo*(-180.0/3.1415),1))+ " deg; max AR: "+str(round(self.maxARdrift,1))+ "px in "+str(round(self.ARperiod,1)) + "sec; max DEC: " + str(round(self.DECperiod,1)) + "px in " + str(round(self.DECperiod)) + "sec"
        self.frame1.SetTitle(title)
        self.ARstart = self.ARdrift
        self.DECstart = self.DECdrift
        self.driftTimer.Start()

    def DrawClock(self, evt):       
        x = -(self.ARdrift * cos(self.angolo) - self.DECdrift * sin(self.angolo))
        y = -(self.ARdrift * sin(self.angolo) + self.DECdrift * cos(self.angolo))
        #self.panel1.bg.bitmap1.SetPosition((round(x),round(y)))
        NewPilImage = self.panel1.bg.pilImage.transform(self.panel1.bg.pilImage.size, Image.AFFINE, (1,0,x,0,1,y), resample=Image.LINEAR)
        #self.panel1.bg.bgBitmap.SetBitmap(im1.ConvertToBitmap())
        self.panel1.bg.bgImage.SetData(NewPilImage.convert("RGB").tostring())
        
        bitmap = wx.BitmapFromImage(self.panel1.bg.bgImage)
        self.panel1.bg.bgBitmap.SetBitmap(bitmap)
        #print im1     
        #self.panel1.bitmap1.SetBitmap(self.panel1.im.ConvertToBitmap())
        #image = wx.EmptyImage(im1.size[0], im1.size[1])
        #new_image = im1.convert('RGB')
        #data = new_image.tostring()
        #image.SetData(data)
        # show some image details
        #str1 = "%s  %dx%d" % (image_file, bmp1.GetWidth(), bmp1.GetHeight()) 
        #parent.SetTitle(str1)
        #self.panel1.bitmap1.SetBitmap(image.ConvertToBitmap())
    
    def SendCommand(self, direction, interval):
        #print "received",direction,interval
        t = self.driftTimer.Time()
        if direction == "w" or direction == "e":
            self.commandARstart = t
            if interval < 0: interval = 1000000
            self.commandARduration = interval
            self.ARdirection = 2*(int(direction=="e")-0.5)
        if direction == "n" or direction == "s":
            self.commandDECstart = t
            self.DECdirection = 2*(int(direction=="s")-0.5)
            if interval < 0: interval = 1000000
            self.commandDECduration = interval
        # set duration
        if direction == "q" or direction == "qw" or direction == "qe" or direction == "qs" or direction == "qn":
            self.commandARduration = 0
            self.commandDECduration = 0
        if direction == "0" or direction == "1" or direction == "2":
            print "set speed to ", direction
            self.actualSpeed = self.speed[int(direction)]
        
                 
    def ControlClock(self, evt):
        t = self.driftTimer.Time()      
        self.ARdrift = self.ARstart + self.maxARdrift * sin(6.28*t/(2000*self.ARperiod))
        self.DECdrift = self.DECstart + self.maxDECdrift * (2*abs(t/(self.DECperiod*2000) - int(t/(self.DECperiod*2000)+0.5))-0.5)
        if t - self.commandARstart < self.commandARduration: 
            self.ARstart += self.actualSpeed * self.ARdirection
            #print self.ARstart, self.DECstart
        if t - self.commandDECstart < self.commandDECduration: 
            self.DECstart += self.actualSpeed * self.DECdirection
            #print self.ARstart, self.DECstart

    def ExtractFloat(self, stringa):
        l=0
        for t in stringa.split():
            try:
                l=float(t)
            except ValueError:
                pass
        return l

# app = wx.App()
# controls = Controls(app)
# app.MainLoop()
