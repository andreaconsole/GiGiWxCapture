#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# PEsimulator.py: entry point of PEsimulator
#
###############################################################################
###
### This file is part of PEsimulator.
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
        try:
            # pick an image file you have in the working folder
            # you can load .jpg  .png  .bmp  or .gif files
            image_file = '../images/skysimulator.jpg'
            #bmp1 = wx.Image(image_file, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            # image's upper left corner anchors at panel coordinates (0, 0)
            self.im = Image.open(image_file)
            self.bitmap1 = wx.StaticBitmap(self)
        except IOError:
            print "Image file %s not found" % image_file
            raise SystemExit
        
    
        
class Controls(object):
    def __init__(self,parent):
        self.drawSpeed = 300
        controlSpeed = 50
        self.frame1 = wx.Frame(None, -1, "loading title...", size=(500, 400))
        # create the class instance
        self.panel1 = Panel1(self.frame1) 
        self.panel1.setAngle = wx.TextCtrl(self.panel1, -1, "0", (10,0),(30,20))
        self.panel1.setARdrift = wx.TextCtrl(self.panel1, -1, "2", (55,0),(30,20))
        self.panel1.setARtime = wx.TextCtrl(self.panel1, -1, "120", (90,0),(50,20))
        self.panel1.setDECdrift = wx.TextCtrl(self.panel1, -1, "2", (155,0),(30,20))
        self.panel1.setDECtime = wx.TextCtrl(self.panel1, -1, "120", (190,0),(50,20))
        self.panel1.setAll = wx.Button(self.panel1, -1, "Set", (255,0),(35,20))
        self.panel1.setAll.Bind(wx.EVT_BUTTON, self.SetTimeAndDrift)
        self.frame1.Show(True)
        self.drawClock = wx.Timer(self.frame1)
        self.drawClock.Start(self.drawSpeed)
        self.frame1.Bind(wx.EVT_TIMER, self.DrawClock, self.drawClock)
        self.controlClock = wx.Timer(self.frame1)
        self.controlClock.Start(controlSpeed)
        self.frame1.Bind(wx.EVT_TIMER, self.ControlClock, self.controlClock)
        
        self.ARcounter = 0
        self.DECcounter = 0
        self.ARdrift = 0.0
        self.DECdrift = 0.0
        self.ARint = 120 *1000/self.drawSpeed
        self.DECint = 120 *1000/self.drawSpeed
        self.ARtrack = -200.0
        self.DECtrack = -200.0
        self.angolo =   0    *(3.1415/180)#unit = degree
        self.speed0 = 1      /10.0 #unit = pixel/sec
        self.speed1 = 8     /10.0 #unit = pixel/sec
        self.speed2 = 16     /10.0 #unit = pixel/sec
        self.speed = self.speed0
        
        title = str(self.angolo*(-180.0/3.1415))+ " deg; AR:"+str( self.ARdrift)+ " in "+str(round(self.drawSpeed*self.ARint/1000.0)) + "; DEC:" + str(self.DECdrift) + " in " + str(round(self.drawSpeed*self.DECint/1000.0))
        self.frame1.SetTitle(title)
        
    def SetTimeAndDrift(self, evt):
        self.ARcounter = 0
        self.DECcounter = 0
        self.ARdrift = float(self.panel1.setARdrift.Value) 
        self.DECdrift = float(self.panel1.setDECdrift.Value)
        self.ARint = int(int(self.panel1.setARtime.Value)*1000/self.drawSpeed)
        self.DECint = int(int(self.panel1.setDECtime.Value)*1000/self.drawSpeed)
        self.angolo = float(self.panel1.setAngle.Value) * (-3.1415/180)
        title = str(self.angolo*(-180.0/3.1415))+ " deg; AR:"+str( self.ARdrift)+ " in "+str(round(self.drawSpeed*self.ARint/1000.0)) + "; DEC:" + str(self.DECdrift) + " in " + str(round(self.drawSpeed*self.DECint/1000.0))
        self.frame1.SetTitle(title)
        
    def DrawClock(self, evt):
        self.ARcounter += 1
        self.DECcounter += 1
        if self.ARcounter >= self.ARint: self.ARcounter = 0
        if self.DECcounter >= self.DECint: self.DECcounter = 0
               
        self.ARtrack += (self.ARdrift * cos(6.28*self.ARcounter/self.ARint)*6.28/self.ARint)
        self.DECtrack += (self.DECdrift * cos(6.28*self.DECcounter/self.DECint)*6.28/self.DECint)
        #print self.DECtrack, self.speed
        
        x = -(self.ARtrack * cos(self.angolo) - self.DECtrack * sin(self.angolo))
        y = -(self.ARtrack * sin(self.angolo) + self.DECtrack * cos(self.angolo))
        
        im1 = self.panel1.im.transform(self.panel1.im.size, Image.AFFINE, (1,0,x,0,1,y), resample=Image.BICUBIC)        
        image = wx.EmptyImage(im1.size[0], im1.size[1])
        new_image = im1.convert('RGB')
        data = new_image.tostring()
        image.SetData(data)
        # show some image details
        #str1 = "%s  %dx%d" % (image_file, bmp1.GetWidth(), bmp1.GetHeight()) 
        #parent.SetTitle(str1)
        self.panel1.bitmap1.SetBitmap(image.ConvertToBitmap())
        
        
    def ControlClock(self, evt):              
        if (os.path.exists('W')): self.ARtrack -= self.speed
        if (os.path.exists('E')): self.ARtrack += self.speed
        if (os.path.exists('N')): self.DECtrack += self.speed
        if (os.path.exists('S')): self.DECtrack -= self.speed
        if (os.path.exists('s0')): self.speed = self.speed0
        if (os.path.exists('s1')): self.speed = self.speed1
        if (os.path.exists('s2')): self.speed = self.speed2

app = wx.App()
controls = Controls(app)
app.MainLoop()
