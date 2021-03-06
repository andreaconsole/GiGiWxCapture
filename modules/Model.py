# -*- coding: UTF-8 -*-
# Model.py: Configuration and Processes classes for GiGiWxCapture
#
###############################################################################
###
### This file is part of GiGiWxCapture.
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

import wx
import time
Sleep = time.sleep
import os
import sys
import socket
import numpy
import wx.lib.plot as plot
import datetime #for speed analysis
import string
strip = string.strip
lower = string.lower
#import serial #import moved in InitSerial function
import math
sqrt = math.sqrt
sin = math.sin
cos = math.cos
tan = math.tan
atan = math.atan
pi = math.pi
atan2 = math.atan2
hypot = math.hypot #Return the Euclidean norm, sqrt(x*x + y*y). This is the length of the vector from the origin to point (x, y).

import SkySimulator

class Configuration(object):
    def __init__(self, configFileName, tempFileName, languageFileName):
        self.configFileName = configFileName
        self.languageFileName = languageFileName
        self.tempFileName = tempFileName
        self.LANGUAGE_FILE_SIZE = 30

    def LoadConfiguration(self):
        #load configuration file
        size = 50
        try:
            self.configLines = size*[""]
            self.defaultConfig = size*[""]
            inputFile = open(self.configFileName,"r")
            index = 0
            for line in inputFile.readlines():
                self.configLines[index] = strip(line)
                self.defaultConfig[index] = strip(line)
                index += 1
            inputFile.close()
            print self.defaultConfig
        except:
            self.configLines = size*[""]
            self.defaultConfig = size*[""]
            outputFile = open(os.path.abspath(self.configFileName),"w")
            outputFile.close()
    
    def LoadTempFile(self):
        #load temp configuration file (autosaved)
        tempFile = []
        try:
            inputFile = open(self.tempFileName,"r")
            for line in inputFile.readlines():
                tempFile.append(strip(line))
            inputFile.close()
        except:
            print "error while attempting to read", self.tempFileName
            outputFile = open(os.path.abspath(self.tempFileName),"w")
            outputFile.close()
        return tempFile

    def LoadLanguage(self,which):
        #load language file
        try:
            self.textLines = []
            inputFile = open(os.path.abspath(self.languageFileName+"/"+which),"r")
            for line in inputFile.readlines():
                u = line.decode("utf-8")
                self.textLines.append(u[3:]) # remove first 3 chars since they are just the line number
            inputFile.close()
            if len(self.textLines)<self.LANGUAGE_FILE_SIZE:
                return False #file too short and so not valid
            else:
                return True
        except:
            print os.path.abspath(self.languageFileName+"/"+which)
            return False #file not valid
                
    def SaveConfiguration(self):
        #save configuration file
        outputFile=open(os.path.abspath(self.configFileName),"w")
        self.defaultConfig = self.configLines
        for line in self.configLines:
            outputFile.write(line)
            outputFile.write("\n")
        outputFile.close()
        
    def SaveTempFile(self, tempFile):
        #save temp file
        outputFile=open(os.path.abspath(self.tempFileName),"w")
        for line in tempFile:
            outputFile.write(line)
            outputFile.write("\n")
        outputFile.close()

    def IsConfigurationChanged(self):
        #check if configuration values are changed from the loaded ones
        if self.configLines != self.defaultConfig:
            print self.defaultConfig
            print self.configLines
        return self.configLines != self.defaultConfig

    def ConfigLines(self):
        #method to get config values
        return self.configLines

    def TextLines(self):
        #method to get language lines
        return self.textLines

    def ConfigLinesUpdate(self, configLines):
        #method to set config values
        self.configLines = configLines

    def ListFiles(self,directory):
        #method to get the list of files in directory
        dirList=os.listdir(os.path.abspath(directory))
        return dirList


class Processes(object):

    def __init__(self, dcScreen, testMode = False):
        if testMode: self.Simulator = SkySimulator.Controls()
        self.dcScreen = dcScreen
        self.ser = None #initialize the serial port variable
        self.deviazione = 0
        self.DitheringInit(0,0)
        self.status = -1
        self.mediaPesata = -1
        self.ultimaCorrezione = 0
        self.ultimaSemiCorrezione = 100
        self.ultimoVerso = 0
        self.fattCorr = 1 # correct for 45degree declination (default)
        self.screenSizeX, self.screenSizeY = wx.DisplaySize()
        self.pixelBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.single)
        self.pixelTempBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.uint8)#numpy.uint8)  
        self.bitmap=wx.EmptyBitmap(self.screenSizeX, self.screenSizeY,-1)
        self.memory = wx.MemoryDC()
        self.memory1 = wx.MemoryDC()
        self.memory2 = wx.MemoryDC()
        self.FWHM = 0
        self.testMode = testMode
        self.multiplier = 1
        self.R = 0
        self.Q = 0
        self.k1 = 0
        self.k2 = 0
        #----------constS
        
    def Close(self):
        #destroy the class
        self.CloseSerial()
        if self.testMode: self.Simulator.frame1.Destroy()
        
    def InitSerial(self,which,baudrateVal = 9600):
        #init serial link
        try:
            import serial
        except:
            print "pyserial not installed"
        try: #if which is a numerical value for port
            self.ser = serial.Serial(int(which), baudrate = baudrateVal, timeout=1)
        except: # if which is port name
            self.ser = serial.Serial(strip(str(which)), baudrate = baudrateVal, timeout=1)
        print self.ser.portstr

    def InitAudio(self):
        #init audio control
        self.soundCamera = wx.Sound(os.path.abspath("../audio/camera.wav"))
        self.soundN = wx.Sound(os.path.abspath("../audio/c1.wav"))
        self.soundS = wx.Sound(os.path.abspath("../audio/c4.wav"))
        self.soundW = wx.Sound(os.path.abspath("../audio/c8.wav"))
        self.soundE = wx.Sound(os.path.abspath("../audio/c2.wav"))
        self.soundQ = wx.Sound(os.path.abspath("../audio/c0.wav"))
        self.soundQ.Play(wx.SOUND_ASYNC)

    def CloseSerial(self):
        #close serial link
        if (self.ser != None):
            if (self.ser.isOpen()):
                self.ser.close()
                self.ser = None
            
    def SetControlMode(self, controlMode):
        #method to set controlMode class variable
        self.controlMode = controlMode

    def EnlargeToWindow(self, x0, y0, MIN_PIX_STEP, MIN_WIDTH):
        #procedure to find "vampirized" window boundaries
        print "searching for borders from (",x0,y0,")"
        #create a copy of screen image in memory
        pixelTempBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.uint8)
        self.memory.SelectObject(self.bitmap)
        self.memory.Blit(0,0,self.screenSizeX,self.screenSizeY,self.dcScreen,0,0)
        self.bitmap.CopyToBuffer(pixelTempBuffer, wx.BitmapBufferFormat_RGB) 
        pixelTempBuffer = pixelTempBuffer.astype(numpy.single)
        #img=wx.ImageFromBitmap(self.bitmap) #test code
        #img.SaveFile("test.bmp",1) #test code
            
        def pixelRedVal(x,y): #returns red value of the pixel x y (displaced by dispX, dispY)
            if 3*(x+self.screenSizeX*(y)) < len(pixelTempBuffer):
                output = pixelTempBuffer[3*(x+self.screenSizeX*(y))]
            else:
                output = 0
            return output
        
        thr = MIN_PIX_STEP + (pixelRedVal(x0-MIN_WIDTH//2, y0+1)+pixelRedVal(x0-MIN_WIDTH//2, y0-1)+
                              pixelRedVal(x0+MIN_WIDTH//2, y0+1)+pixelRedVal(x0+MIN_WIDTH//2, y0-1))//4
        print "with threshold = ", thr
        #up
        pix1 = pix2  = 0
        x1 = x0 - MIN_WIDTH//2
        x2 = x0 + MIN_WIDTH//2
        y1 = y0
        y2 = y0
        while (y1>0) and (pix1<thr or pix2<thr):# or pix1<>pix2):
            y1 -= 1
            y2 -= 1
            pix1 = pixelRedVal(x1,y1)
            pix2 = pixelRedVal(x2,y2)
        ymin = y1
        #down
        pix1 = pix2  = 0
        x1 = x0 - MIN_WIDTH//2
        x2 = x0 + MIN_WIDTH//2
        y1 = y0
        y2 = y0
        while (y1<self.screenSizeY) and (pix1<thr or pix2<thr):# or pix1<>pix2):
            y1 += 1
            y2 += 1
            pix1 = pixelRedVal(x1,y1)
            pix2 = pixelRedVal(x2,y2)
        ymax = y1
        #left
        pix1 = pix2  = 0
        x1 = x0
        x2 = x0
        y1 = ymin+MIN_WIDTH//2
        y2 = ymax-MIN_WIDTH//2
        while (x1>0) and (pix1<thr or pix2<thr):# or pix1<>pix2):
            x1 -= 1
            x2 -= 1
            pix1 = pixelRedVal(x1,y1)
            pix2 = pixelRedVal(x2,y2)
        xmin = x1
        #right
        pix1 = pix2  = 0
        x1 = x0
        x2 = x0
        y1 = ymin+MIN_WIDTH//2
        y2 = ymax-MIN_WIDTH//2
        while (x1<self.screenSizeX) and (pix1<thr or pix2<thr):# or pix1<>pix2):
            x1 += 1
            x2 += 1
            pix1 = pixelRedVal(x1,y1)
            pix2 = pixelRedVal(x2,y2)
        xmax = x1
        self.memory.SelectObject(wx.NullBitmap) #erase memory copy of screen image 
        return xmin, ymin, xmax, ymax

    def ZoomRefresh(self, ZoomFrame, zoomSizeX, zoomSizeY, xs, ys):
        #refresh zoom window
        bitmap=wx.EmptyBitmap(zoomSizeX//2 ,zoomSizeY//2,-1)
        self.memory1.SelectObject(bitmap)
        self.memory1.Blit(0,0,zoomSizeX//2,zoomSizeY//2,self.dcScreen,
                    xs-zoomSizeX//4,ys-zoomSizeY//4)
        self.memory1.SelectObject(wx.NullBitmap)
        dcZoom = wx.PaintDC(ZoomFrame)
        dcZoom.SetUserScale(2,2)
        dcZoom.DrawBitmap(bitmap, 0, 0, False)

    def SetCrosshair(self, winPosX, winPosY, winSizeX, winSizeY, crosshairXs, crosshairYs, bigLinePosizion):
        #method to build crosshair line structure
        largeLine = 50
        crosshairList = [
            (winPosX,crosshairYs,winPosX+winSizeX,crosshairYs),
            (crosshairXs,winPosY,crosshairXs,winPosY+winSizeY)
            ]

        x=crosshairXs-50
        large = 1
        while x>winPosX:
            crosshairList.append((x,crosshairYs-(7+3*large),x,crosshairYs+(7+3*large)))
            x-=50
            large = -large

        x=crosshairXs+50
        large = 1
        while x<winPosX+winSizeX:
            crosshairList.append((x,crosshairYs-(7+3*large),x,crosshairYs+(7+3*large)))
            x+=50
            large = -large

        y=crosshairYs-50
        large = 1
        while y>winPosY:
            crosshairList.append((crosshairXs-(7+3*large),y,crosshairXs+(7+3*large),y))
            y-=50
            large = -large

        y=crosshairYs+50
        large = 1
        while y<winPosY+winSizeY:
            crosshairList.append((crosshairXs-(7+3*large),y,crosshairXs+(7+3*large),y))
            y+=50
            large = -large          
        crosshairList.append((crosshairXs-largeLine, crosshairYs-bigLinePosizion,crosshairXs+largeLine,crosshairYs-bigLinePosizion))
        crosshairList.append((crosshairXs-largeLine, crosshairYs+bigLinePosizion,crosshairXs+largeLine,crosshairYs+bigLinePosizion))
        crosshairList.append((crosshairXs-bigLinePosizion, crosshairYs-largeLine,crosshairXs-bigLinePosizion,crosshairYs+largeLine))
        crosshairList.append((crosshairXs+bigLinePosizion, crosshairYs-largeLine,crosshairXs+bigLinePosizion,crosshairYs+largeLine))
        return crosshairList

    def CalcId(self):
        #calculate a unique PC/USER id
        idString=""
        try:
            idString += sys.platform
        except:
            idString += "noplat"
        try:
            idString += os.environ['USER']
        except:
            idString += "nouser"
        try:
            idString += socket.gethostname()
        except:
            idString += "nohostname"
        idString = str(hash(idString))
        return idString

    def FieldUpdate(self, width, height, focal):
        #update the field calculator output
        if focal != 0:
            field = str(round(((width * 3437.75) / focal), 1))+"' x "+str(round(((height * 3437.75) / focal), 1))+"'"
        else:
            field="ERROR"
        return field

    def SavePicture(self, winPosX, winPosY, winSizeX, winSizeY, nomefile):
        #save a screenshot (part of screen) as nomefile
        try:
            bitmap=wx.EmptyBitmap(winSizeX, winSizeY,-1)
            self.memory2.SelectObject(bitmap)
            self.memory2.Blit(0,0,winSizeX,winSizeY,self.dcScreen,winPosX,winPosY)
            self.memory2.SelectObject(wx.NullBitmap)
            img=wx.ImageFromBitmap(bitmap)
            img.SaveFile(nomefile,1)
        except:
            print "cannot save image"

    
    def StarTrack(self, actualX, actualY, winPosX, winPosY, winSizeX, winSizeY, iterations = 1):
        #centers the star and finds fwhm; track radius = 9px
        MIN_DISTANCE = 35 #minimum distance from the border of window
        TRACK_RADIUS = 10
        NO_STAR_LIMIT = 100 #minimunm sum pixel values in star area (TRACK_RADIUS x TRACK_RADIUS)
        #create a copy of screen image in memory
        self.memory.SelectObject(self.bitmap)
        self.memory.Blit(0,0,self.screenSizeX,self.screenSizeY,self.dcScreen,0,0)
        self.bitmap.CopyToBuffer(self.pixelTempBuffer, wx.BitmapBufferFormat_RGB) 
        self.pixelBuffer += self.pixelTempBuffer.astype(numpy.single)
        resetBuffer = True
        if iterations == 0: #when iter = 0, startrack bufferize and add image data so to improve signal to noise ratio
            iterations = 1
            resetBuffer = False;
            print "accumulating..."
            
        def pixelRedVal(x,y): #returns red value of the pixel x y (displaced by dispX, dispY)
            if 3*(x+self.screenSizeX*(y)) < len(self.pixelBuffer):
                output = self.pixelBuffer[3*(x+self.screenSizeX*(y))]
            else:
                output = 0
            return output
        
        def subtr(x,y):
            return x-y
        
        def mult(x,y):
            return x*y
        
        def div(x,y):
            return x/y
        
        def multquad(x,y):
            return x*(y**2)
        
        def multandsum(a,b,c):
            return int(a+b*c)
        
        def calcSignature(winPosX, winPosY, winSizeX, winSizeY):
            testpoints = [0.10,0.15,0.30,0.45,0.50,0,65,0.70,0.85,0.90]
            winPosX = len(testpoints)*[winPosX]
            winSizeX = len(testpoints)*[winSizeX]
            winPosY = len(testpoints)*[winPosY]
            winSizeY = len(testpoints)*[winSizeY]
            Xarray = map(multandsum, winPosX, winSizeX, testpoints)
            Yarray = map(multandsum, winPosY, winSizeY, testpoints)
            signature = sum(map(pixelRedVal,Xarray,Yarray))
            return signature
        
        def calcArrays(x0, y0, radius):
            arrX = (2*radius+1)*range(x0-radius, x0+radius+1)
            arrY = [];
            for i in xrange(y0-radius, y0+radius+1):
                arrY += (2*radius+1)*[i]
            borderX = (x0-radius, x0+radius, x0-radius, x0+radius)
            borderY = (y0-radius, y0-radius, y0+radius, y0+radius) 
            #borderX = range(x0-radius, x0+radius+1)+range(x0-radius, x0+radius+1)+(2*radius-1)*[x0-radius]+(2*radius-1)*[x0+radius]
            
            #borderY = (2*radius+1)*[x0-radius]+(2*radius+1)*[x0+radius]+range(x0-radius+1, x0+radius)+range(x0-radius+1, x0+radius)
            return arrX, arrY, borderX, borderY
            
        imageSignature = calcSignature(winPosX, winPosY, winSizeX, winSizeY)        
        for _ in xrange(iterations): #iterations
            actualXr, actualYr = int(actualX), int(actualY)
            Xarray, Yarray, Xborder, Yborder = calcArrays(actualXr, actualYr, TRACK_RADIUS*self.multiplier)  
            bgList = map(pixelRedVal, Xborder, Yborder)
            bg = (sum(bgList)-max(bgList)-min(bgList))/2
            pixelValues = map(subtr,map(pixelRedVal, Xarray, Yarray),len(Xarray)*[bg])
            pixelSum = sum(pixelValues)+0.1
#             if pixelSum<NO_STAR_LIMIT:
#                 pdf = self.oldPdf
#             else:
            pdf = map(div,pixelValues,len(Xarray)*[pixelSum])
            actualX = sum(map(mult, pdf, Xarray)) # E(x)
            actualY = sum(map(mult, pdf, Yarray)) # E(y)
        #FMHM = 2,355*sigma; sigma^2 = E(x^2) - E(x)^2
        fwhmX = 2.355*(abs(sum(map(multquad, pdf, Xarray)) - actualX**2)**0.5)
        fwhmY = 2.355*(abs(sum(map(multquad, pdf, Yarray)) - actualY**2)**0.5)
        if self.FWHM == 0:
            self.FWHM = 0.5*(fwhmX+fwhmY)
        else:
            self.FWHM = 0.6 * self.FWHM + 0.2 * (fwhmX+fwhmY)
        if self.FWHM>15: #if the star goes out of the TRACK_RADIUS box
            print "star not found " + str(sum(pixelValues))
            self.multiplier = 1
        self.memory.SelectObject(wx.NullBitmap) #erase memory copy of screen image
        if resetBuffer: self.pixelBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.single)
        actualX = max(actualX, winPosX+MIN_DISTANCE)
        actualX = min(actualX, winPosX+winSizeX-MIN_DISTANCE)
        actualY = max(actualY, winPosY+MIN_DISTANCE)
        actualY = min(actualY, winPosY+winSizeY-MIN_DISTANCE)
        return actualX, actualY, self.FWHM, imageSignature

    def Angolo(self,a,b):
        #calculates angle
        angolo = -atan2(b,a) #because y is from top to bottom
        return angolo
    
    def CoordConvert(self,x,y,angolo): 
        #converts x and y coord between two ref. sys with same origin and rotated of "-angolo" 
        x1 = round(x * cos(angolo) - y * sin(angolo),2)
        y1 = round(x * sin(angolo) + y * cos(angolo),2)
        return x1, y1

    def SetFattCorr(self,value):
        #method to set fattCorr class variable (for alignment - related to star declination)
        self.fattCorr = value

    def GetFattCorr(self):
        #method to get fattCorr class variable (for alignment - related to star declination)
        return self.fattCorr

    def ResetUltimaCorrezione(self):
        #method to reset ultimaCorrezione class variable (for alignment - last correction applied)
        self.ultimaCorrezione = 0

    def ResetCorrezione(self):
        #method to reset correzione class variable (for alignment - last correction applied)
        self.ultimaSemiCorrezione = 100
        self.deviazione = 0

    def UpdateCorrection(self, xo, yo, xf, yf, angolo, trueCorrectionElapsedTime):
        #calculate needed correction for polar alignment
        a = 1.0
        b = math.tan(-angolo)
        if b==0: b=0.01
        c = hypot(1,b)
        decDiff = (a*yo-a*yf+b*xf-b*xo)/c
        arDiff = (decDiff*a+yf*c-yo*c)/b
        semiCorrezione = (decDiff)/(trueCorrectionElapsedTime + 0.1)
        print decDiff, semiCorrezione
        deviazione = 100*(semiCorrezione-self.ultimaSemiCorrezione)/self.ultimaSemiCorrezione
        self.ultimaSemiCorrezione = semiCorrezione
        return semiCorrezione, deviazione, self.fattCorr, arDiff

    def CalcCorrection (self, angolo, xo, yo, xf, yf, window, warningtext):
        #convert needed correction for polar alignment in pixels
        correzione = abs(round(self.ultimaSemiCorrezione * 86164 * self.fattCorr / (2 * pi)))
        #calculate direction of correction
        verso = cmp(0,(yf * cos(angolo) - xf * sin(angolo)) - (yo * cos(angolo) - xo * sin(angolo))) #invert correction
        # verifies if error has become bigger
        if (correzione > self.ultimaCorrezione) and (verso == self.ultimoVerso) and (self.ultimaCorrezione != 0):
            dial=wx.MessageDialog(window, warningtext, 'Warning', wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()
        # corrects the correction basing on last correction (fattCorr)
        elif self.ultimaCorrezione != 0:
            print "fattcorr:", abs((abs(self.ultimaCorrezione) - abs(correzione)) / self.ultimaCorrezione), correzione
            if abs((abs(self.ultimaCorrezione) - abs(correzione)) / self.ultimaCorrezione) > 0.1 and abs(correzione) < 1000:
                self.fattCorr = self.fattCorr * abs(self.ultimaCorrezione / (self.ultimaCorrezione * self.ultimoVerso - correzione * verso))
                print "fattCorr=" + str(self.fattCorr)
                if self.fattCorr == 0: self.fattCorr = 1
                correzione = abs(round(self.mediaPesata * 86164 * self.fattCorr / (2 * pi)))
        else:
            print "lastCorr="+str(self.ultimaCorrezione)
        # store this correction for next confrontation
        self.ultimaCorrezione = correzione
        self.ultimoVerso = verso
        self.mediaPesata = -1
        return correzione, verso

    def DrawCorrectionCalc(self, angolo, correzione, verso, winPosX, winPosY, winSizeX, winSizeY, xf, yf):
        #draw correction lines
        winRatio=float(winSizeY)/float(winSizeX)
        # optimization of correction circle drawing
        # first checks if it is possible to center the circle on the star (if the circle remains in the window)
        # if not, it chooses the best position in the screen
        xfi,yfi=xf,yf

        # calculate max window size
        if abs(tan(angolo)) < winRatio :
            diagonale = 0.8 * abs(float(winSizeX) / cos(angolo))
        else:
            diagonale = 0.8 * abs(float(winSizeY) / sin(angolo))

        # if window is too small for correction, divides the correction (multiple steps correction)
        numCorr = round((abs(correzione) // diagonale) + 1)
        correzione = correzione / numCorr

        if not (xf + (correzione * verso) * cos(angolo)>winPosX and
                yf + (correzione * verso) * sin(angolo)>winPosY and
                xf + (correzione * verso) * cos(angolo)<winPosX + winSizeX and
                yf + (correzione * verso) * sin(angolo)<winPosY + winSizeY):
            # move the start point to the edge
            xf = (0.5 * winSizeX + winPosX) - 0.5 * verso * correzione * cos(angolo)
            yf = (0.5 * winSizeY + winPosY) - 0.5 * verso * correzione * sin(angolo)

        if not (xfi - (correzione * verso) * cos(angolo)>winPosX and
                yfi - (correzione * verso) * sin(angolo)>winPosY and
                xfi - (correzione * verso) * cos(angolo)<winPosX + winSizeX and
                yfi - (correzione * verso) * sin(angolo)<winPosY + winSizeY):
            # move the start point to the edge
            xfi = (0.5 * winSizeX + winPosX) + 0.5 * verso * correzione * cos(angolo)
            yfi = (0.5 * winSizeY + winPosY) + 0.5 * verso * correzione * sin(angolo)

        print numCorr, correzione, diagonale
        x1,y1 = xf, yf
        x2,y2 = xf + (correzione * verso) * cos(angolo),yf + (correzione * verso) * sin(angolo)
        x3,y3 = xfi, yfi
        x4,y4 = xfi - (correzione * verso) * cos(angolo),yfi - (correzione * verso) * sin(angolo)

        a1 = winPosX
        a2 = winPosX + winSizeX
        b1 = winPosY
        b2 = winPosY + winSizeY
        tang=tan(angolo+pi/2)

        if abs(tang)>1000:
            x11,y11 = x1,b1
            x12,y12 = x1,b2
            x21,y21 = x2,b1
            x22,y22 = x2,b2
            x31,y31 = x3,b1
            x32,y32 = x3,b2
            x41,y41 = x4,b1
            x42,y42 = x4,b2
        elif abs(tang)<0.001:
            x11,y11 = a1,y1
            x12,y12 = a2,y1
            x21,y21 = a1,y2
            x22,y22 = a2,y2
            x31,y31 = a1,y3
            x32,y32 = a2,y3
            x41,y41 = a1,y4
            x42,y42 = a2,y4
        else:
            if (a1-x1)*tang+y1>b1 and (a1-x1)*tang+y1<b2: x11,y11 = a1,(a1-x1)*tang+y1
            if (a2-x1)*tang+y1>b1 and (a2-x1)*tang+y1<b2: x11,y11 = a2,(a2-x1)*tang+y1
            if (b1-y1)/tang+x1>a1 and (b1-y1)/tang+x1<a2: x11,y11 = (b1-y1)/tang+x1,b1
            if (b2-y1)/tang+x1>a1 and (b2-y1)/tang+x1<a2: x11,y11 = (b2-y1)/tang+x1,b2

            if (b2-y1)/tang+x1>a1 and (b2-y1)/tang+x1<a2: x12,y12 = (b2-y1)/tang+x1,b2
            if (b1-y1)/tang+x1>a1 and (b1-y1)/tang+x1<a2: x12,y12 = (b1-y1)/tang+x1,b1
            if (a2-x1)*tang+y1>b1 and (a2-x1)*tang+y1<b2: x12,y12 = a2,(a2-x1)*tang+y1
            if (a1-x1)*tang+y1>b1 and (a1-x1)*tang+y1<b2: x12,y12 = a1,(a1-x1)*tang+y1

            if (a1-x2)*tang+y2>b1 and (a1-x2)*tang+y2<b2: x21,y21 = a1,(a1-x2)*tang+y2
            if (a2-x2)*tang+y2>b1 and (a2-x2)*tang+y2<b2: x21,y21 = a2,(a2-x2)*tang+y2
            if (b1-y2)/tang+x2>a1 and (b1-y2)/tang+x2<a2: x21,y21 = (b1-y2)/tang+x2,b1
            if (b2-y2)/tang+x2>a1 and (b2-y2)/tang+x2<a2: x21,y21 = (b2-y2)/tang+x2,b2

            if (b2-y2)/tang+x2>a1 and (b2-y2)/tang+x2<a2: x22,y22 = (b2-y2)/tang+x2,b2
            if (b1-y2)/tang+x2>a1 and (b1-y2)/tang+x2<a2: x22,y22 = (b1-y2)/tang+x2,b1
            if (a2-x2)*tang+y2>b1 and (a2-x2)*tang+y2<b2: x22,y22 = a2,(a2-x2)*tang+y2
            if (a1-x2)*tang+y2>b1 and (a1-x2)*tang+y2<b2: x22,y22 = a1,(a1-x2)*tang+y2

            if (a1-x3)*tang+y3>b1 and (a1-x3)*tang+y3<b2: x31,y31 = a1,(a1-x3)*tang+y3
            if (a2-x3)*tang+y3>b1 and (a2-x3)*tang+y3<b2: x31,y31 = a2,(a2-x3)*tang+y3
            if (b1-y3)/tang+x3>a1 and (b1-y3)/tang+x3<a2: x31,y31 = (b1-y3)/tang+x3,b1
            if (b2-y3)/tang+x3>a1 and (b2-y3)/tang+x3<a2: x31,y31 = (b2-y3)/tang+x3,b2

            if (b2-y3)/tang+x3>a1 and (b2-y3)/tang+x3<a2: x32,y32 = (b2-y3)/tang+x3,b2
            if (b1-y3)/tang+x3>a1 and (b1-y3)/tang+x3<a2: x32,y32 = (b1-y3)/tang+x3,b1
            if (a2-x3)*tang+y3>b1 and (a2-x3)*tang+y3<b2: x32,y32 = a2,(a2-x3)*tang+y3
            if (a1-x3)*tang+y3>b1 and (a1-x3)*tang+y3<b2: x32,y32 = a1,(a1-x3)*tang+y3

            if (a1-x4)*tang+y4>b1 and (a1-x4)*tang+y4<b2: x41,y41 = a1,(a1-x4)*tang+y4
            if (a2-x4)*tang+y4>b1 and (a2-x4)*tang+y4<b2: x41,y41 = a2,(a2-x4)*tang+y4
            if (b1-y4)/tang+x4>a1 and (b1-y4)/tang+x4<a2: x41,y41 = (b1-y4)/tang+x4,b1
            if (b2-y4)/tang+x4>a1 and (b2-y4)/tang+x4<a2: x41,y41 = (b2-y4)/tang+x4,b2

            if (b2-y4)/tang+x4>a1 and (b2-y4)/tang+x4<a2: x42,y42 = (b2-y4)/tang+x4,b2
            if (b1-y4)/tang+x4>a1 and (b1-y4)/tang+x4<a2: x42,y42 = (b1-y4)/tang+x4,b1
            if (a2-x4)*tang+y4>b1 and (a2-x4)*tang+y4<b2: x42,y42 = a2,(a2-x4)*tang+y4
            if (a1-x4)*tang+y4>b1 and (a1-x4)*tang+y4<b2: x42,y42 = a1,(a1-x4)*tang+y4

        alignCorrList = [
            # starting line
            (x11,y11,x12,y12),
            #box
            (x1-10,y1-10,x1+10,y1-10),
            (x1-10,y1+10,x1+10,y1+10),
            (x1-10,y1-10,x1-10,y1+10),
            (x1+10,y1-10,x1+10,y1+10),
            # direction line
            (x1,y1,x2,y2),
             # destination line
            (x21,y21,x22,y22),
            ]

        alignCorrListInv = [
            # starting line
            (x31,y31,x32,y32),
            #box
            (x3-10,y3-10,x3+10,y3-10),
            (x3-10,y3+10,x3+10,y3+10),
            (x3-10,y3-10,x3-10,y3+10),
            (x3+10,y3-10,x3+10,y3+10),
            # direction line
            (x3,y3,x4,y4),
             # destination line
            (x41,y41,x42,y42),
            ]
        return alignCorrList, alignCorrListInv, numCorr, x1, y1, x3, y3

    def CrossList (self, centerX, centerY, lineStart, lineEnd):
        #return coordinates to draw the cross around the star you are tracking
            CrossList = [
            (centerX-lineStart,centerY,centerX-lineEnd,centerY),
            (centerX+lineStart,centerY,centerX+lineEnd,centerY),
            (centerX,centerY-lineStart,centerX,centerY-lineEnd),
            (centerX,centerY+lineStart,centerX,centerY+lineEnd),
            ]
            return CrossList

    def SaveList(self, filename, listToSave):
        #save an array as a list text file (e.g. for PE analysis)
        outputFile=open(os.path.abspath(filename),"w")
        n = 0
        while n < len(listToSave):
            outputFile.write(str(listToSave[n][0])+" "+str(listToSave[n][1])+"\n")
            n+=1
        outputFile.close()

    def DitheringInit(self, maxDith, dithStep):
        #method to reset dithering variables
        self.dithIncrX, self.dithIncrY = 0, 0
        self.dithFactX, self.dithFactY = dithStep, dithStep
        self.maxDith = maxDith

    def DitheringUpdate(self):
        #method to update dithering variables when dithering occurs
        if self.maxDith>0 and self.dithFactX<>0:
            self.dithIncrX += self.dithFactX
            self.dithIncrY += self.dithFactY
        if abs(self.dithIncrX) >= self.maxDith:
            self.dithFactX *= -1
        if abs(self.dithIncrY) >= self.maxDith+1:
            self.dithFactY *= -1
        print "Dithering NOW: ", self.dithIncrX, self.dithIncrY
    
    def DitheringAdd(self, guideCenterX, guideCenterY):
        #method to get guide center point after dithering
        guideCenterX += self.dithIncrX
        guideCenterY += self.dithIncrY
        #print "center moved of: ", self.dithIncrX, self.dithIncrY
        return guideCenterX, guideCenterY

    def SendMountCommand(self, direction, inv, interval = -1):
        # if interval < 0: send simply the command to the mount, else: move, sleeps msTimeCorr milliseconds, and stops
        if (inv and (direction == "w")): direction = "e"
        elif (inv and (direction == "e")): direction = "w"
        elif (inv and (direction == "n")): direction = "s"
        elif (inv and (direction == "s")): direction = "n"
        elif (inv and (direction == "qe")):direction = "qw"
        elif (inv and (direction == "qw")):direction = "qe"
        elif (inv and (direction == "qn")):direction = "qs"
        elif (inv and (direction == "qs")):direction = "qn"
        print "mount command: ", direction
        
        if self.testMode:
            self.Simulator.SendCommand(direction, -1)
        else:
            if  self.controlMode == "serial": #serial control
                try:
                    if   direction == "qw": Stringa = "#:Qw#"
                    elif direction == "qe": Stringa = "#:Qe#"
                    elif direction == "qn": Stringa = "#:Qn#"
                    elif direction == "qs": Stringa = "#:Qs#"
                    elif direction == "q": Stringa = "#:Q#"
                    elif direction == "0": Stringa = "#:RG#"
                    elif direction == "1": Stringa = "#:RC#"
                    elif direction == "2": Stringa = "#:RM#"
                    elif interval > 0:
                        if   direction == "w": Stringa = "#:Mgw"+'{0:04}'.format(int(interval))+"#"
                        elif direction == "e": Stringa = "#:Mge"+'{0:04}'.format(int(interval))+"#"
                        elif direction == "n": Stringa = "#:Mgn"+'{0:04}'.format(int(interval))+"#"
                        elif direction == "s": Stringa = "#:Mgs"+'{0:04}'.format(int(interval))+"#"
                        else: return
                        print Stringa
                    elif interval < 0:                
                        if   direction == "w": Stringa = "#:Mw#"
                        elif direction == "e": Stringa = "#:Me#"
                        elif direction == "n": Stringa = "#:Mn#"
                        elif direction == "s": Stringa = "#:Ms#"
                        else: return
                    else: return
                    self.ser.write(Stringa)
                except:
                    try:
                        self.ser.write("#:Q#")
                    except:
                        pass
    
            elif self.controlMode == "audio": # audio control
                if direction == "w": self.soundW.Play(wx.SOUND_ASYNC)
                elif direction == "e": self.soundE.Play(wx.SOUND_ASYNC)
                elif direction == "n": self.soundN.Play(wx.SOUND_ASYNC)
                elif direction == "s": self.soundS.Play(wx.SOUND_ASYNC)
                elif direction == "q": self.soundQ.Play(wx.SOUND_ASYNC)
                elif direction == "qw" or direction == "qe": self.soundQ.Play(wx.SOUND_ASYNC)
                elif direction == "qn" or direction == "qs": self.soundQ.Play(wx.SOUND_ASYNC)
                else: return
             
                
    def SetCamLE(self, value, camControlMode):
        #method to set Long Exposure ON or OFF
        if  camControlMode == "serial": #serial control
            try:            
                self.ser.setDTR(value)
            except:
                print "serial error"

        elif camControlMode == "audio": # audio control
            print "LE=", value
            try:
                if value:
                    self.soundCamera.Play(wx.SOUND_LOOP)
                else:
                    self.soundCamera.Stop()
            except:
                print "audio error"
            
    def KalmanFilterReset(self, R, Q):
        #method to reset the kalman filter
        P = numpy.matrix('1 1; 1 1')
        K = numpy.matrix('0 0; 0 0')
        self.kdeltaX = 0
        self.kdeltaY = 0
        self.R = R
        self.Q = Q
        print "Kalman Filter reset done"
        
    
    def KalmanFilter(self, deltaXmeas, deltaYmeas):
        #method to calculate and get kalman filtered values
        #
        # state variable X = [Dx; Dy]
        # measured value M = [Mx; My]
        # A = B = C = [1,0;0,1] = I
        # U = [0;0]
        # X = I*X + I*U + W = I*X + W
        # M = I*X + Z
        #
        #set filter parameters
        if self.kdeltaX == 0: self.kdeltaX = deltaXmeas
        if self.kdeltaY == 0: self.kdeltaY = deltaYmeas
        #
        R = numpy.matrix('self.R; self.R')
        Q = numpy.matrix('self.Q self.Q; self.Q self.Q')
        X = numpy.matrix('self.kdeltaX; self.kdeltaY')
        D = numpy.matrix('0;0')
        M = numpy.matrix('deltaXmeas; deltaXmeas')
        #PREDICTION
        #x = (A*x) + (B*u); %calculate x predicted
        #INNOVATION
        #reality against prediction (innovation)  
        D = M - X
        #P = (A*P*A') + Q; %calculate P predicted
        P += Q
        #S = (C*P*C') + R; %innovation covariance
        S = P + R
        #K = P*C'*(S^-1); %calculate Kalman gain
        K = P*S.getI()
        #x += K*dy; %status update
        X += K*D
        #P -= K*S*K'; %covariance update
        P -= K*S*K.getT() 
        return X[0,0], X[1,0]
       
    def GuideCalcReset(self, k1, k2):
        #method to reset guide PID controller
        self.cdeltaXold = 0
        self.cdeltaYold = 0
        self.k1 = k1
        self.k2 = k2
        print "GuideCalc reset done"
    
    def GuideCalc(self, cdeltaX, cdeltaY):   # px, px
        #method to calc guide corrections (kalman + PID)
        #a1 = datetime.datetime.now() #for speed analysis     
        if self.Q <> 0 and self.R <> 0: deltaX, deltaY = self.KalmanFilter(self, deltaX, deltaY)   
        def sign(x):
            if x>0:
                y = 1
            elif x==0:
                y = 0
            else:
                y = -1
            return y
        
        def absSign(x):
            if x==0:
                y = 0
            else:
                y = 1
            return y 
        
        correctionX = -int((1 + self.k1*(1+sign(cdeltaX)*sign(self.cdeltaXold))) * cdeltaX * self.corrRateAR)
        correctionY = -int((1 + self.k1*(1+sign(cdeltaY)*sign(self.cdeltaYold))) * cdeltaY * self.corrRateDEC)
        self.cdeltaXold = cdeltaX
        self.cdeltaYold = cdeltaY
        #b1 = datetime.datetime.now() #for speed analysis
        #print "guidecalc", b1-a1 #for speed analysis
        return correctionX, correctionY     
            
    def GenericGraphInit(self, frm):
        #method for initializing graph window
        self.client = plot.PlotCanvas(frm)
        frame_size = frm.GetClientSize()
        self.client.SetInitialSize(size=frame_size)
        self.client.SetEnableGrid(True)
        self.client.SetEnableLegend(True)
        self.client.SetBackgroundColour("#401010")
        self.client.SetForegroundColour("#ADD8E6")
               
    def GenericGraphDraw(self, frm, data1, data2, data3, data4, descriptions):
        #method for graph drawing
        frm.showGraph1.SetLabel(descriptions[0])
        frm.showGraph2.SetLabel(descriptions[1])
        frm.showGraph3.SetLabel(descriptions[2])
        frm.showGraph4.SetLabel(descriptions[3])
        lines = []
        if len(data1)>1: 
            line1 = plot.PolyLine(data1, legend=descriptions[0], colour='red', width=1)
            lines.append(line1)
        if len(data2)>1: 
            line2 = plot.PolyLine(data2, legend=descriptions[1], colour='blue', width=1)
            lines.append(line2)
        if len(data3)>1: 
            line3 = plot.PolyLine(data3, legend=descriptions[2], colour='orange', width=1)
            lines.append(line3)
        if len(data4)>1: 
            line4 = plot.PolyLine(data4, legend=descriptions[3], colour='cyan', width=1)
            lines.append(line4)
        gc = plot.PlotGraphics(lines)
        try:
            self.client.Draw(gc)
        except:
            pass
        
    def GuideRoutineStart(self, invAR, invDEC, minARcorr, minDECcorr, corrRateAR, corrRateDEC, guideInterval, pulseGuideOn):
        #method for initializing guide routine
        self.SendMountCommand("0", False) #set speed to "min speed" (min)
        self.ARcorr, self.DECcorr = 0, 0 #ARcorr and DECcorr are class level beacause are returned by GuideLastARcorr methods
        self.invAR, self.invDEC = invAR, invDEC #used by GuideRoutine
        self.minARcorr, self.minDECcorr = minARcorr, minDECcorr #used by GuideRoutine
        self.guideInterval = guideInterval #used by GuideRoutine
        self.corrRateAR, self.corrRateDEC = corrRateAR, corrRateDEC #used by GuideCalc
        self.pulseGuideOn = pulseGuideOn  #used by GuideRoutine
        print "guide params (invAR, invDEC, minAR, minDEC, controlmode, pguide): ", self.invAR, self.invDEC, self.minARcorr, self.minDECcorr, self.controlMode, self.pulseGuideOn
        
    def GuideLastARcorr(self):
        #method to get last AR correction
        return self.ARcorr
    
    def GuideLastDECcorr(self):
        #method to get last DEC correction
        return self.DECcorr

    def GuideRoutine(self, ARdrift, DECdrift):
        #method to guide the mount
        maxAcceptedCorrectionInMilliSec = 10000 #if is requested a correction bigger than this limit, then there is a problem! Better no move
        def sign(x):
            if x>0:
                y = 1
            elif x==0:
                y = 0
            else:
                y = -1
            return y
        #calculate correction
        self.ARcorr, self.DECcorr = self.GuideCalc(ARdrift, DECdrift)
        if ((self.ARcorr>maxAcceptedCorrectionInMilliSec) or (self.DECcorr>maxAcceptedCorrectionInMilliSec)):
            print "too big correction required! check your system! " + str(self.ARcorr) + ", " + str(self.DECcorr)
            return
        else:
#             totalCorr = abs(correctionX) + abs(correctionY)
#             if totalCorr > 900 * self.guideInterval:
#                 correctionX *= (900 * self.guideInterval/totalCorr)
#                 correctionY *= (900 * self.guideInterval/totalCorr)
#                 print "corr reduced by factor ", totalCorr/(900 * self.guideInterval) 
            if abs(self.ARcorr) > self.guideInterval: self.ARcorr = self.guideInterval * sign(self.ARcorr)
            if abs(self.DECcorr) > self.guideInterval: self.DECcorr = self.guideInterval * sign(self.DECcorr)

        print "Drift: ",round(ARdrift,2), round(DECdrift,2),  "; Corrections in ms:",round(self.ARcorr), round(self.DECcorr)
        #use inv to cope with negative corrections
        invAR = ((self.ARcorr<0)<>self.invAR)
        invDEC = ((self.DECcorr<0)<>self.invDEC)
        ARcorr = abs(self.ARcorr)
        DECcorr = abs(self.DECcorr)
        if ARcorr < self.minARcorr: ARcorr = 0
        if DECcorr < self.minDECcorr: DECcorr = 0
        #---send corrections
        if self.pulseGuideOn and not(self.testMode):
            self.SendMountCommand("e", invAR, ARcorr)
            self.SendMountCommand("s", invDEC, DECcorr)
        else:
            if ARcorr > DECcorr:
                if ARcorr> 0: self.SendMountCommand("e", invAR)
                Sleep(abs(ARcorr-DECcorr)/1000)
                if DECcorr> 0: self.SendMountCommand("s", invDEC)
                Sleep(DECcorr/1000)
            else:
                if DECcorr> 0: self.SendMountCommand("s", invDEC)
                Sleep(abs(ARcorr-DECcorr)/1000)
                if ARcorr> 0: self.SendMountCommand("e", invAR)
                Sleep(ARcorr/1000)
            self.SendMountCommand("q", False)
        
    def GuideCalibrationRoutineStart(self):
        #method for initializing guide calibration routine
        self.SendMountCommand("0", False) #set speed to "min speed" (min)
        self.status = 0
        self.timeForCalSizeAlongX, self.timeForCalSizeAlongY = 0, 0
        self.corrRateAR, self.corrRateDEC = -1, -1
        self.gapPass = False

    def GuideCalibrationRoutine(self, actualX, actualY, invAR, invDEC, calibrationSize):
        #method for guide calibration routine
        GAP_SIZE = max(round(calibrationSize*0.1), 5) # length of no-calculation track (in order to avoid to compute backlash); min 2px
        angolo = 0.0
        if self.status == 0:
            self.newInvAR = invAR
            self.newInvDEC = invDEC
            self.startX, self.startY = actualX, actualY
            self.SendMountCommand("n", invDEC)
            self.status = 1
            self.gapPass = False
        if self.status > 0:
            if hypot((actualX-self.startX),(actualY-self.startY)) >= GAP_SIZE and not self.gapPass:
                self.startTime = round(1000*time.time()) #self.startTime = wx.GetLocalTimeMillis() --
                self.gapPass = True
                print "gap passed"
                self.startX, self.startY = actualX, actualY
            if hypot((actualX-self.startX),(actualY-self.startY)) >= calibrationSize and self.gapPass:
                self.gapPass = False
                self.stopTime = round(1000*time.time()) #self.stopTime = wx.GetLocalTimeMillis() --
                self.status += 1
                deltatime = self.stopTime - self.startTime
                deltaspace = hypot((actualX-self.startX),(actualY-self.startY))
                print "calibration status = " + str(self.status)
                print "deltatime, deltaspace =" + str(deltatime) + ", " + str(deltaspace)
                if self.status == 2:
                    self.corrRateDEC = deltatime/deltaspace
                    if actualY > self.startY: self.newInvDEC = not invDEC 
                    self.SendMountCommand("q", False)
                    Sleep(1)
                    self.SendMountCommand("s", invDEC)
                if self.status == 3:
                    self.corrRateDEC = 0.5*(self.corrRateDEC + deltatime/deltaspace)
                    if actualY < self.startY: self.newInvDEC = not invDEC 
                    self.SendMountCommand("q", False)
                    Sleep(1)
                    self.SendMountCommand("w", invAR)
                if self.status == 4:
                    self.corrRateAR = deltatime/deltaspace
                    if actualX > self.startX: self.newInvAR = not invAR 
                    self.SendMountCommand("q", False)
                    Sleep(1)
                    self.SendMountCommand("e", invAR)
                if self.status == 5:
                    self.corrRateAR = 0.5*(self.corrRateAR + deltatime/deltaspace)
                    if actualX < self.startX: self.newInvAR = not invAR 
                    self.SendMountCommand("q", False)
                    angolo = self.Angolo(actualX-self.startX, actualY-self.startY)
                    # if only one direction is changed, then change angolo sign
                    if (self.newInvAR == self.newInvDEC) != (invAR == invDEC): angolo = -angolo
                self.startX, self.startY = actualX, actualY
        #print and return correction rate in msec/pixel
        print round(self.corrRateAR), round(self.corrRateDEC), "; invar-dec:", self.newInvAR, self.newInvDEC, "; angle:", angolo*57.3
        return self.corrRateAR, self.corrRateDEC, self.newInvAR, self.newInvDEC, angolo, 5 - self.status

    def SendPetacCorrection(self, lastInterval, petacVal, mountSpeed):
        #method to apply PETAC correction
        MAX_CORRECTION_FACT = 0.8
        MAX_RATIO = 2
        if lastInterval > 0 and petacVal > 0 and mountSpeed > 0:
            ratio = petacVal/lastInterval
            if ratio > 1/MAX_RATIO and ratio < 1:
                millisec = lastInterval*((ratio-1)/(1-ratio*(1+mountSpeed)))
                print ratio,": moving west for ", millisec, "millisecs"
                #no correction bigger than default interval
                if millisec < 0 or millisec > MAX_CORRECTION_FACT * petacVal:
                    millisec = MAX_CORRECTION_FACT * petacVal
                self.SendMountCommand("w", False)
                self.SendMountCommand("q", False)
            elif ratio > 1 and ratio < MAX_RATIO:
                millisec = lastInterval*((ratio-1)/(1-ratio*(1-mountSpeed)))
                print ratio,": moving east for ", millisec, "millisecs"
                #no correction bigger than default interval
                if millisec < 0 or millisec > MAX_CORRECTION_FACT * petacVal:
                    millisec = MAX_CORRECTION_FACT * petacVal
                self.SendMountCommand("e", False)
                self.SendMountCommand("q", False)

    def UpdatePetacValue(self, petacVal, petacIntervals, arDrift, corrRateAR, corrSpeed, invAR):
        #remember that petacVal(msec) is the right (medium) time interval b/w two mouse movements,
        #arDrift is the star shift (in AR) in pixel and corrRateAR is the correction speed in millisec/pixel
        if invAR:
            inv = -1
        else:
            inv = 1
        petacVal = petacVal + (arDrift*corrRateAR*(corrSpeed-1)*inv)/petacIntervals
        return petacVal

    def ExtractInt(self, stringa):
        #extract an integer from a string
        l=0
        for t in stringa.split():
            try:
                l=int(float(t))
            except ValueError:
                pass
        return l

    def ExtractFloat(self, stringa):
        #extract a float from a string
        l=0
        for t in stringa.split():
            try:
                l=float(t)
            except ValueError:
                pass
        return l
    
    def DirChoose(self, startPath, testo):
        #open the dialog to choose a directory
        selectedDir = startPath
        dialog = wx.DirDialog(None, testo, style=1 ,defaultPath=startPath, pos = (10,10))
        if dialog.ShowModal() == wx.ID_OK:
            selectedDir = dialog.GetPath()
        dialog.Destroy()
        return selectedDir
    
    def CountFiles(self, dirPath):
        #count the files in a directory
        try:
            num = len(os.listdir(dirPath))
        except:
            num = 0
        return num
    