# -*- coding: UTF-8 -*-
# Model.py: Configuration and Processes classes for GiGiWxCapture
#
###############################################################################
###
### This file is part of GiGiWxCapture.
###
###    Copyright (C) 2011 Andrea Console  <andreaconsole@gmail.com>
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
#import datetime #for speed analysis
import string
strip = string.strip
lower = string.lower
#import serial
import operator
add = operator.add
sub = operator.sub
import math
sqrt = math.sqrt
sin = math.sin
cos = math.cos
tan = math.tan
atan = math.atan
pi = math.pi

class Configuration(object):
    def __init__(self, configFileName, tempFileName, languageFileName):
        self.configFileName = configFileName
        self.languageFileName = languageFileName
        self.tempFileName = tempFileName
        self.LANGUAGE_FILE_SIZE = 30

    def LoadConfiguration(self):
        try:
            self.configLines = []
            self.defaultConfig = []
            inputFile = open(self.configFileName,"r")
            for line in inputFile.readlines():
                self.configLines.append(strip(line))
                self.defaultConfig.append(strip(line))
            inputFile.close()
            print self.defaultConfig
        except:
            outputFile = open(os.path.abspath(self.configFileName),"w")
            outputFile.close()
    
    def LoadTempFile(self):
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
            outputFile=open(os.path.abspath(self.languageFileName+"/"+which),"w")
            outputFile.close()
            return False #file not valid
        
    def SaveTempFile(self, tempFile):
        outputFile=open(os.path.abspath(self.tempFileName),"w")
        for line in tempFile:
            outputFile.write(line)
            outputFile.write("\n")
        outputFile.close()
        
    def SaveConfiguration(self):
        outputFile=open(os.path.abspath(self.configFileName),"w")
        self.defaultConfig = self.configLines
        for line in self.configLines:
            outputFile.write(line)
            outputFile.write("\n")
        outputFile.close()

    def IsConfigurationChanged(self):
        if self.configLines != self.defaultConfig:
            print self.defaultConfig
            print self.configLines
        return self.configLines != self.defaultConfig

    def ConfigLines(self):
        return self.configLines

    def TextLines(self):
        return self.textLines

    def ConfigLinesUpdate(self, configLines):
        self.configLines = configLines

    def ListFiles(self,directory):
        dirList=os.listdir(os.path.abspath(directory))
        return dirList


class Processes(object):

    def __init__(self, dcScreen):
        self.dcScreen = dcScreen
        self.ser = None #initialize the serial port variable
        self.deviazione = 0
        self.DitheringInit(0,0)
        self.status = -1
        self.mediaPesata = -1
        self.ultimaCorrezione = 0
        self.ultimoVerso = 0
        self.fattCorr = 1 # correct for 45degree declination (default)
        self.screenSizeX, self.screenSizeY = wx.DisplaySize()
        self.pixelBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.single)
        self.pixelTempBuffer = numpy.zeros((self.screenSizeX*self.screenSizeY*3), dtype=numpy.uint8)#numpy.uint8)  
        self.bitmap=wx.EmptyBitmap(self.screenSizeX, self.screenSizeY,-1)
        self.memory=wx.MemoryDC()
        self.FWHM = 0
        #----------constS
        # Warning: never forget that testMode is incopatible with dithering - always remember
        # to set dith interval to 0
        self.testMode = True
        self.testAngle = 0 * pi / 180
        self.testSpeed = 200

    def InitSerial(self,which,baudrateVal = 9600):
        try: #if which is a numerical value for port
            self.ser = serial.Serial(int(which), baudrate = baudrateVal, timeout=1)
        except: # if which is port name
            self.ser = serial.Serial(strip(str(which)), baudrate = baudrateVal, timeout=1)
        print self.ser.portstr

    def InitAudio(self):
        self.soundN = wx.Sound(os.path.abspath("../audio/decIncr.wav"))
        self.soundS = wx.Sound(os.path.abspath("../audio/decDecr.wav"))
        self.soundE = wx.Sound(os.path.abspath("../audio/arIncr.wav"))
        self.soundW = wx.Sound(os.path.abspath("../audio/arDecr.wav"))
        self.soundQ = wx.Sound(os.path.abspath("../audio/arDecStop.wav"))
        self.soundQ.Play(wx.SOUND_ASYNC)

    def CloseSerial(self):
        if (self.ser != None):
            if (self.ser.isOpen()):
                self.ser.close()
                self.ser = None

    def EnlargeToWindow(self, window, TASKBAR_H, MIN_PIX_STEP):
        x,y = window.GetPosition()
        sizeX, sizeY = window.GetSize()
        window.Hide()
        self.memory.SelectObject(self.bitmap)
        self.memory.Blit(0,0,self.screenSizeX,self.screenSizeY,self.dcScreen,0,0)
        # check these pixels to see when VampireFrame covers exactly video window,
        # and enlarge VampireFrame if not
        #
        #       ------------------
        #       |      pix3      |
        #       |                |
        #       |pix1        pix2|
        #       |                |
        #       |      pix4      |
        #       ------------------
        #
        pix1=pix2=pix3=pix4=0
        centralPix=MIN_PIX_STEP + (self.memory.GetPixel(x,y)[1]+self.memory.GetPixel(x+sizeX,y)[1]+self.memory.GetPixel(x,y+sizeY)[1]+self.memory.GetPixel(x+sizeX,y+sizeY)[1])//4
        x1=x
        x2=x+sizeX+10
        x3=x4=x+sizeX//2

        y1=y2=y+sizeY//2
        y3=y
        y4=y+sizeY+TASKBAR_H+30
        print self.memory.GetPixel(x,y)[1]
        while (x1>0 and y3>0 and x2<self.screenSizeX and y4<self.screenSizeY) and (pix1<centralPix or pix2<centralPix or
                                                           pix3<centralPix or pix4<centralPix):

            if pix1 < centralPix: x1-=2
            if pix2 < centralPix: x2+=2
            if pix3 < centralPix: y3-=2
            if pix4 < centralPix: y4+=2

            pix1=(self.memory.GetPixel(x1,y1)[1]+self.memory.GetPixel(x1,y1-1)[1]+self.memory.GetPixel(x1,y1+1)[1])//3
            pix2=(self.memory.GetPixel(x2,y2)[1]+self.memory.GetPixel(x2,y2-1)[1]+self.memory.GetPixel(x2,y2+1)[1])//3
            pix3=(self.memory.GetPixel(x3,y3)[1]+self.memory.GetPixel(x3-1,y3)[1]+self.memory.GetPixel(x3+1,y3)[1])//3
            pix4=(self.memory.GetPixel(x4,y4)[1]+self.memory.GetPixel(x4-1,y4)[1]+self.memory.GetPixel(x4+1,y4)[1])//3

        window.SetPosition((x1, y3))
        window.SetSize((x2-x1, y4-y3-TASKBAR_H))
        window.Show()
        self.memory.SelectObject(wx.NullBitmap)

    def ZoomRefresh(self, ZoomFrame, zoomSizeX, zoomSizeY, xs, ys):
        bitmap=wx.EmptyBitmap(zoomSizeX//2 ,zoomSizeY//2,-1)
        self.memory.SelectObject(bitmap)
        self.memory.Blit(0,0,zoomSizeX//2,zoomSizeY//2,self.dcScreen,
                    xs-zoomSizeX//4,ys-zoomSizeY//4)
        self.memory.SelectObject(wx.NullBitmap)
        dcZoom = wx.PaintDC(ZoomFrame)
        dcZoom.SetUserScale(2,2)
        dcZoom.DrawBitmap(bitmap, 0, 0, False)

    def SetCrosshair(self, winPosX, winPosY, winSizeX, winSizeY, crosshairXs, crosshairYs):
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

        return crosshairList

    def CalcId(self):
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

    def FieldUpdate(self,width,height,focal):
        if focal != 0:
            field = str(round(((width * 3437.75) / focal), 1))+"' x "+str(round(((height * 3437.75) / focal), 1))+"'"
        else:
            field="ERROR"
        return field

    def SavePicture(self, window, winPosX, winPosY, winSizeX, winSizeY, nomefile, question, confirmation):
            bitmap=wx.EmptyBitmap(winSizeX, winSizeY,-1)
            self.memory.SelectObject(bitmap)
            self.memory.Blit(0,0,winSizeX,winSizeY,self.dcScreen,winPosX,winPosY)
            self.memory.SelectObject(wx.NullBitmap)
            img=wx.ImageFromBitmap(bitmap)
            dial = wx.MessageDialog(window, question, 'Question', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            ret = dial.ShowModal()
            if ret == wx.ID_YES:
                img.SaveFile(nomefile,1)
                dial=wx.MessageDialog(window, confirmation, 'Info', wx.OK | wx.ICON_INFORMATION)
                dial.ShowModal()

    def StarTrack(self, actualX, actualY, iter, reset):
    # centers the star and finds fwhm; track radius = 9px
        #create a copy of screen image in memory
        UPDATE_SPEED = 0.33 # 0<UPDATE_SPEED<=1. It's a filter against noise. The smaller the stronger.
        self.memory.SelectObject(self.bitmap)
        self.memory.Blit(0,0,self.screenSizeX,self.screenSizeY,self.dcScreen,0,0)
        self.bitmap.CopyToBuffer(self.pixelTempBuffer, wx.BitmapBufferFormat_RGB) 
        if reset:
            self.pixelBuffer = self.pixelTempBuffer.astype(numpy.single)
        else:
            self.pixelBuffer += UPDATE_SPEED*(self.pixelTempBuffer.astype(numpy.single)-self.pixelBuffer)
        #pixelRGB = (pixelBuffer[3*(x+screenSizeX*y)], pixelBuffer[3*(x+screenSizeX*y)+1], pixelBuffer[3*(x+screenSizeX*y)+2]) 

        def pixelRedVal(x,y): #returns red value of the pixel x y (displaced by dispX, dispY)
            return self.pixelBuffer[3*(x+self.screenSizeX*(y))]
        
        def incrementalSum(x,y,z): #returns the value of a variable increased step by step
            self.parSum += x+y+z
            return self.parSum  
        
        fwhmX = 0
        fwhmY = 0
        vett10 = range(-9,10) #numbers from -9 to 9
        incr = [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9]
        #a1 = datetime.datetime.now() #for speed analysis
        for _ in xrange(iter-1): #iterations
            actualXr, actualYr = round(actualX), round(actualY)
            xr=[actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr,actualXr]
            yr=[actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr,actualYr]
            xrl=map(sub,xr,incr)
            xrr=map(add,xr,incr)
            yru=map(sub,yr,incr)
            yrd=map(add,yr,incr)
            hh=map(add,xr,vett10) #range(actualXr-9, actualXr+9+1)
            vv=map(add,yr,vett10) #range(actualYr-9, actualYr+9+1)            
            pdfX = map(pixelRedVal,hh,yr)
            pdfXu = map(pixelRedVal,hh,yru)
            pdfXd = map(pixelRedVal,hh,yrd)
            pdfY = map(pixelRedVal,xr,vv)
            pdfYl = map(pixelRedVal,xrl,vv)
            pdfYr = map(pixelRedVal,xrr,vv)
            
            self.parSum = 0
            cdfX=map(incrementalSum,pdfX,pdfXu,pdfXu)
            self.parSum = 0
            cdfY=map(incrementalSum,pdfY,pdfYl,pdfYr)
            actualX = actualXr
            actualY = actualYr
            for j in xrange(0,18):
                if (cdfX[j] <= 0.5 * cdfX[18]) and (cdfX[j + 1] > 0.5 * cdfX[18]):
                    #calculation by interpolation of j / cdf(j)=0.5*cdf(18)
                    actualX = actualXr + j - 9 + (0.5 * cdfX[18] - cdfX[j]) / (cdfX[j + 1] - cdfX[j])
                if (cdfY[j] <= 0.5 * cdfY[18]) and (cdfY[j + 1] > 0.5 * cdfY[18]):
                    #calculation by interpolation of j / cdf(j)=0.5*cdf(18)
                    actualY = actualYr + j - 9 + (0.5 * cdfY[18] - cdfY[j]) / (cdfY[j + 1] - cdfY[j]) 
            
        #---FWHM
        ped = 0.25 * (pdfX[0] + pdfX[18] + pdfY[0] + pdfY[18]) #calculates background value
        pedarray = [ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped,ped] 
        #subtracts background
        pdfX = map(sub,pdfX,pedarray)
        pdfY = map(sub,pdfY,pedarray)
        for j in xrange(1,17):
            if pdfX[j] <= 0.5 * pdfX[9] and pdfX[j + 1] > 0.5 * pdfX[9]:
                fwhmX = j + (0.5 * pdfX[9] - pdfX[j]) / (pdfX[j + 1] - pdfX[j]) 
                #calculation by interpolation of j / pdf(j)=0.5*pdf(10) where pdf is rising
            if pdfX[j] >= 0.5 * pdfX[9] and pdfX[j + 1] < 0.5 * pdfX[9]:
                fwhmX = j + (0.5 * pdfX[9] - pdfX[j]) / (pdfX[j + 1] - pdfX[j]) - fwhmX  
                #calculation by interpolation of j / pdf(j)=0.5*pdf(10) where pdf is decreasing. 
                #By substracting this from the above value, it obtains FWHM
            if pdfY[j] <= 0.5 * pdfY[9] and pdfY[j + 1] > 0.5 * pdfY[9]:
                fwhmY = j + (0.5 * pdfY[9] - pdfY[j]) / (pdfY[j + 1] - pdfY[j]) 
                #calculation by interpolation of j / pdf(j)=0.5*pdf(10) where pdf is rising
            if pdfY[j] >= 0.5 * pdfY[9] and pdfY[j + 1] < 0.5 * pdfY[9]:
                fwhmY = j + (0.5 * pdfY[9] - pdfY[j]) / (pdfY[j + 1] - pdfY[j]) - fwhmY  
                #calculation by interpolation of j / pdf(j)=0.5*pdf(10) where pdf is decreasing. 
                #By substracting this from the above value, it obtains FWHM

        if self.FWHM == 0:
            self.FWHM = 0.5*(fwhmX+fwhmY)
        else:
            self.FWHM = 0.8 * self.FWHM + 0.1 * (fwhmX+fwhmY)
        #b1 = datetime.datetime.now() #for speed analysis
        #print b1-a1 #for speed analysis
        self.memory.SelectObject(wx.NullBitmap) #erase memory copy of screen image
        return actualX, actualY, self.FWHM
    
    def Angolo(self,a,b):
        if a == 0: 
            angolo = pi/2
        else:
            angolo = atan(b/a)
        return angolo
    
    def CoordConvert(self,x,y,angolo): 
        #converts x and y coord between two ref. sys with same origin and rotated of "angolo"
        ipotenuse = sqrt(x**2+y**2)
        deltaAngolo = self.Angolo(x,y) - angolo
        x1 = ipotenuse * cos(deltaAngolo)
        y1 = ipotenuse * sin(deltaAngolo) 
        return x1, y1

    def SetFattCorr(self,value):
        self.fattCorr = value

    def GetFattCorr(self):
        return self.fattCorr

    def ResetUltimaCorrezione(self):
        self.ultimaCorrezione = 0

    def ResetCorrezione(self):
        self.mediaPesata = 0
        self.deviazione = 0

    def UpdateCorrection(self, a ,b , xo, yo, xf, yf, angolo, trueCorrectionElapsedTime):
        c = sqrt(a**2+b**2)
        decDiff = (a*yo-a*yf+b*xf-b*xo)/c
        arDiff = (decDiff*a+yf*c-yo*c)/b
        semiCorrezione = (decDiff)/(trueCorrectionElapsedTime + 0.1)
        self.deviazione += 0.1*(semiCorrezione - self.mediaPesata - self.deviazione)
        self.mediaPesata += 0.1 * (semiCorrezione - self.mediaPesata)
        return self.mediaPesata, self.deviazione, self.fattCorr, arDiff

    def CalcCorrection (self, angolo, xo, yo, xf, yf, window, warningtext ):
        correzione = abs(round(self.mediaPesata * 86164 * self.fattCorr / (2 * pi)))
        #calculate direction of correction
        verso = cmp((yf * cos(angolo) - xf * sin(angolo)) - (yo * cos(angolo) - xo * sin(angolo)),0)
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
            CrossList = [
            (centerX-lineStart,centerY,centerX-lineEnd,centerY),
            (centerX+lineStart,centerY,centerX+lineEnd,centerY),
            (centerX,centerY-lineStart,centerX,centerY-lineEnd),
            (centerX,centerY+lineStart,centerX,centerY+lineEnd),
            ]
            return CrossList

    def SaveList(self, filename, listToSave):
        outputFile=open(os.path.abspath(filename),"w")
        n = 0
        while n < len(listToSave):
            outputFile.write(str(listToSave[n][0])+" "+str(listToSave[n][1])+"\n")
            n+=1
        outputFile.close()

    def DitheringInit(self, maxDitherX, maxDitherY):
        self.dithIncrX, self.dithIncrY = 0, 0
        self.dithFactX, self.dithFactY = 1, 1
        self.maxDitherX, self.maxDitherY = maxDitherX, maxDitherY

    def DitheringUpdate(self):
        if self.maxDitherX>0 and self.maxDitherY>0:
            self.dithIncrX += self.dithFactX
            self.dithIncrY += self.dithFactY
        if abs(self.dithIncrX) >= self.maxDitherX:
            self.dithFactX *= -1
        if abs(self.dithIncrY) >= self.maxDitherY:
            self.dithFactY *= -1
    
    def DitheringAdd(self, guideCenterX, guideCenterY):
        guideCenterX += self.dithIncrX
        guideCenterY += self.dithIncrY
        return guideCenterX, guideCenterY

    def SendMountCommand(self, direction, msTimeCorr, controlMode, invAR, invDEC):
        # if msTimeCorr<0: send simply the command to the mount, else: move, sleeps msTimeCorr milliseconds, and stops
        #print "controlmode-invaAR-invDEC-direction-msTimeCorr",controlMode, invAR, invDEC, direction, msTimeCorr
        if self.testMode: # audio control
            if msTimeCorr != 0:
                cumTime = 0
                if direction == "w":
                    if invAR:
                        while cumTime < msTimecorr:
                            self.dithIncrX -= self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                    else:
                        while cumTime < msTimecorr:
                            self.dithIncrX += self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                elif direction == "e":
                    if invAR:
                        while cumTime < msTimecorr:
                            self.dithIncrX += self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                    else:
                        while cumTime < msTimecorr:
                            self.dithIncrX -= self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                elif direction == "n":
                    if invDEC:
                        while cumTime < msTimecorr:
                            self.dithIncrY -= self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                    else:
                        while cumTime < msTimecorr:
                            self.dithIncrY += self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                elif direction == "s":
                    if invDEC:
                        while cumTime < msTimecorr:
                            self.dithIncrY += self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                    else:
                        while cumTime < msTimecorr:
                            self.dithIncrY -= self.testIncr
                            Sleep(self.testInt)
                            cumTime += self.testInt
                else: return
                
        elif  controlMode == "serial": #serial control
            try:
                if direction == "w":
                    if invAR:
                        Stringa = "#:Me#"
                    else:
                        Stringa = "#:Mw#"
                elif direction == "e":
                    if invAR:
                        Stringa = "#:Mw#"
                    else:
                        Stringa = "#:Me#"
                elif direction == "n":
                    if invDEC:
                        Stringa = "#:Ms#"
                    else:
                        Stringa = "#:Mn#"
                elif direction == "s":
                    if invDEC:
                        Stringa = "#:Mn#"
                    else:
                        Stringa = "#:Ms#"
                elif direction == "q": Stringa = "#:Q#"
                elif direction == "0": Stringa = "#:RG#"
                elif direction == "1": Stringa = "#:RC#"
                elif direction == "2": Stringa = "#:RM#"
                else: return
                if msTimeCorr != 0: self.ser.write(Stringa)
                if msTimeCorr < 0 and direction == "q":
                    Sleep(1) #interval to not saturate serial port
                if msTimeCorr > 0:
                    Sleep(msTimeCorr/1000)
                    self.ser.write("#:Q#")
                    #wx.FutureCall(timeCorr,self.ser.write("#:Q#"))
            except:
                self.ser.write("#:Q#")

        elif controlMode == "audio": # audio control
            if msTimeCorr != 0:
                if direction == "w":
                    if invAR:
                        self.soundE.Play(wx.SOUND_ASYNC)
                    else:
                        self.soundW.Play(wx.SOUND_ASYNC)
                elif direction == "e":
                    if invAR:
                        self.soundW.Play(wx.SOUND_ASYNC)
                    else:
                        self.soundE.Play(wx.SOUND_ASYNC)
                elif direction == "n":
                    if invDEC:
                        self.soundS.Play(wx.SOUND_ASYNC)
                    else:
                        self.soundN.Play(wx.SOUND_ASYNC)
                elif direction == "s":
                    if invDEC:
                        self.soundN.Play(wx.SOUND_ASYNC)
                    else:
                        self.soundS.Play(wx.SOUND_ASYNC)
                elif direction == "q": self.soundQ.Play(wx.SOUND_ASYNC)
                else: return
            if msTimeCorr>0:
                Sleep(msTimeCorr/1000)
                self.soundQ.Play(wx.SOUND_ASYNC)
                #wx.FutureCall(msTimeCorr,self.soundQ.Play(wx.SOUND_ASYNC))
        
    
    def KalmanFilterReset(self):
        self.P11, self.P12, self.P21, self.P22 = 0,0,0,0
        self.K11, self.K12, self.K21, self.K22 = 0,0,0,0
        self.deltaX = 0
        self.deltaY = 0
        print "Kalman Filter reset done"
        
    
    def KalmanFilter(self, deltaXmeasured, deltaYmeasured):
        #
        # state variable X = [Dx; Dy]
        # measured value M = [Mx; My]
        # A = B = C = [1,0;0,1] = I
        # U = [0;0]
        # X = I*X + I*U + W = I*X + W
        # M = I*X + Z
        #
        #set filter parameters
        R = 0.01
        Q11, Q12, Q21, Q22 = 0.0005, 0.0005, 0.0005, 0.0005
        #step1 -> X prediction: X = X; step2 -> P prediction: P(k+1) = A*P(k)*At+Q = P(k)+Q
        #print "P = [", self.P11, ",", self.P12, ";",  self.P21, ",", self.P22, "]"
        self.P11, self.P12, self.P21, self.P22 = self.P11+Q11, self.P12+Q12, self.P21+Q21, self.P22+Q22
        #step3 -> K update: K(k) = P(k)*Ct*(C*P(k)*Ct+R)^-1 = P(k)*(P(k)+R)^-1
        #                   K(k) = (1/det(P+R))* [P11,P12;P21,P22]*[P22+R,-P12;-P21,P11+R]
        determinant = 1/(((self.P11 + R)*(self.P22 + R)) - (self.P12 * self.P21))
        self.K11 = determinant*((self.P11 * self.P22) - (self.P12 * self.P21) + (self.P11 * R))
        self.K12 = determinant*self.P12*R
        self.K21 = determinant*self.P21*R
        self.K22 = determinant*(self.P11*self.P22-self.P12*self.P21+self.P22*R)
        #print "K = [", self.K11, ",", self.K12, ";",  self.K21, ",", self.K22, "]"
        #step4 -> X update: X = X+K*(M-C*X) = X+K*(M-X)
        self.deltaX += self.K11*(deltaXmeasured-self.deltaX)+self.K12*(deltaYmeasured-self.deltaY)
        self.deltaY += self.K21*(deltaXmeasured-self.deltaX)+self.K22*(deltaYmeasured-self.deltaY)
        #step5 -> P update: P(k) = (I-K(k)*C)*P(k) = (I-K(k))*P(k)
        self.P11 = (1-self.K11)*self.P11 + (0-self.K12)*self.P21
        self.P12 = (1-self.K11)*self.P12 + (0-self.K12)*self.P22
        self.P21 = (0-self.K21)*self.P11 + (1-self.K22)*self.P12
        self.P22 = (0-self.K21)*self.P12 + (1-self.K22)*self.P22
        #return state
        return self.deltaX, self.deltaY
       
    def PIDcontrolReset(self):
        self.PIDstopWatch = wx.StopWatch()
        self.PIDintegralX = 0
        self.previousErrorX = 0
        self.PIDintegralY = 0
        self.previousErrorY = 0
        print "PID reset done"
    
    def PIDcontrol(self, deltaX, deltaY, corrRateX, corrRateY, guideIntervalSec):
        guideIntervalms = guideIntervalSec*1000
        deltaTime = self.PIDstopWatch.Time() #in msec
        self.PIDstopWatch.Start() #restart stopwatch
        PIDderivativeX = (deltaX-self.previousErrorX)/deltaTime
        self.previousErrorX = deltaX
        PIDderivativeY = (deltaY-self.previousErrorY)/deltaTime
        self.previousErrorY = deltaY
        Ku = 2 #(Gain for sustained oscillations)
        Tu = 2 * guideIntervalms #(Period of sustained oscillations)
        #
        # Zieger-Nichols 
        #kp = 0.6   * Ku
        #Ti = 0.5   * Tu
        #Td = 0.125 * Tu
        # Pessen Integral Rule
        #kp = 0.7   * Ku
        #Ti = 0.4   * Tu
        #Td = 0.15  * Tu
        # Some overshoot
        #kp = 0.33  * Ku
        #Ti = 0.5   * Tu
        #Td = 0.33  * Tu
        # No Overshoot
        kp = 0.2   * Ku
        Ti = 0.5   * Tu
        Td = 0.33  * Tu
        #
        correctionX = int(kp*(deltaX + self.PIDintegralX/Ti + PIDderivativeX*Td) * corrRateX)
        correctionY = int(kp*(deltaY + self.PIDintegralY/Ti + PIDderivativeY*Td) * corrRateY)
        #correction limiter and anti-windup code
        totalCorr = abs(correctionX) + abs(correctionY)
        if totalCorr > 0.8 * guideIntervalms:
            correctionX *= (0.8 * guideIntervalms/totalCorr)
            correctionY *= (0.8 * guideIntervalms/totalCorr)
            #anti-windup
        else:
            self.PIDintegralX += deltaX*deltaTime
            self.PIDintegralY += deltaY*deltaTime
        # derivative limiter
        return correctionX, correctionY
    
    def GuideGraphDraw(self, frm, data1, data2, data3, data4):
        client = plot.PlotCanvas(frm)
        frame_size = frm.GetClientSize()
        client.SetInitialSize(size=frame_size)
        client.SetBackgroundColour("#401010")
        client.SetForegroundColour("#ADD8E6")
        line1 = plot.PolyLine(data1, legend='', colour='red', width=1)
        line2 = plot.PolyLine(data2, legend='', colour='blue', width=1)
        line3 = plot.PolyLine(data3, legend='', colour='orange', width=1)
        line4 = plot.PolyLine(data4, legend='', colour='lightblue', width=1)
        data = data1+data2+data3+data4
        x = map(lambda c:  c[0] , data)
        y = map(lambda c:  c[1] , data)
        gc = plot.PlotGraphics([line1, line2, line3, line4])
        #client.Draw(gc,  xAxis= (min(x),max(x+[10])), yAxis= (min(y+[-0.5])-0.1,max(y+[0.5])+0.1))
        try:
            client.Draw(gc,  xAxis= (min(x),max(x+[10])), yAxis= (min(y)-0.1,max(y)+0.1))
        except:
            pass

        
    def GuideRoutineStart(self, controlMode):
        self.SendMountCommand("0", -1, controlMode, 0, 0) #set speed to min
        self.ARcorr, self.DECcorr = 0, 0
        
    def GuideLastARcorr(self):
        return self.ARcorr
    
    def GuideLastDECcorr(self):
        return self.DECcorr

    def GuideRoutine(self, ARdrift, DECdrift, corrRateAR, corrRateDEC, enableDecGuide,
                     invAR, invDEC, minARcorr, minDECcorr, controlMode, guideIntervalSec):
        #calculate correction
        self.ARcorr, self.DECcorr = self.PIDcontrol(ARdrift, DECdrift, corrRateAR, corrRateDEC, guideIntervalSec) 
        #print "correction before-after PID;", ARdrift, ";",DECdrift,";",ARdriftPID, ";",DECdriftPID
        if not(enableDecGuide): self.DECcorr = 0
        print "Corrections in ms:",round(self.ARcorr), round(self.DECcorr)
        #---AR correction
        if abs(self.ARcorr) > minARcorr:
            if self.ARcorr > 0:
                self.SendMountCommand("w", self.ARcorr, controlMode, invAR, invDEC)
            else:
                self.SendMountCommand("e", -self.ARcorr, controlMode, invAR, invDEC)
        #---DEC correction
        if abs(self.DECcorr) > minDECcorr:
            if self.DECcorr > 0:
                self.SendMountCommand("n", self.DECcorr, controlMode, invAR, invDEC)
            else:
                self.SendMountCommand("s", -self.DECcorr, controlMode, invAR, invDEC)
        #print self.ARcorr, DECcorr

    def GuideCalibrationRoutineStart(self, controlMode):
        self.status = 0
        self.timeForCalSizeAlongX, self.timeForCalSizeAlongY = 0, 0
        self.corrRateAR, self.corrRateDEC = -1, -1
        self.gapPass = False
        self.SendMountCommand("0", -1, controlMode,0,0) #set speed to min

    def GuideCalibrationRoutine(self, actualX, actualY, controlMode, invAR, invDEC, calibrationSize):
        GAP_SIZE = 20 # length of no-calculation track (in order to avoid to compute backlash)
        ready = False
        if self.status == 0:
            self.startX, self.startY = actualX, actualY
            self.SendMountCommand("n", -1, controlMode, invAR, invDEC)
            self.status = 1
            self.gapPass = False
        if self.status > 0:
            if sqrt((actualX-self.startX)**2+(actualY-self.startY)**2) >= GAP_SIZE and not self.gapPass:
                self.startTime = round(1000*time.clock()) #self.startTime = wx.GetLocalTimeMillis() --
                self.gapPass = True
                print "gap passed"
                self.startX, self.startY = actualX, actualY
            if sqrt((actualX-self.startX)**2+(actualY-self.startY)**2) >= calibrationSize and self.gapPass:
                self.gapPass = False
                self.stopTime = round(1000*time.clock()) #self.stopTime = wx.GetLocalTimeMillis() --
                self.status += 1
                print "calibration status = " + str(self.status)
                if self.status == 2:
                    self.corrRateDEC = (self.stopTime - self.startTime)/sqrt((actualX-self.startX)**2+(actualY-self.startY)**2)
                    if actualY > self.startY: newInvDEC = -invDEC 
                    self.SendMountCommand("q", -1, controlMode, invAR, invDEC)
                    Sleep(1)
                    self.SendMountCommand("s", -1, controlMode, invAR, invDEC)
                if self.status == 3:
                    self.corrRateDEC = 0.5*(self.corrRateDEC + (self.stopTime - self.startTime)/sqrt((actualX-self.startX)**2+(actualY-self.startY)**2))
                    if actualY < self.startY: newInvDEC = -invDEC 
                    self.SendMountCommand("q", -1, controlMode, invAR, invDEC)
                    Sleep(1)
                    self.SendMountCommand("w", -1, controlMode, invAR, invDEC)
                if self.status == 4:
                    self.corrRateAR = (self.stopTime - self.startTime)/sqrt((actualX-self.startX)**2+(actualY-self.startY)**2)
                    if actualX > self.startX: newInvAR = -invAR 
                    self.SendMountCommand("q", -1, controlMode, invAR, invDEC)
                    Sleep(1)
                    self.SendMountCommand("e", -1, controlMode, invAR, invDEC)
                if self.status == 5:
                    self.corrRateAR = 0.5*(self.corrRateAR + (self.stopTime - self.startTime)/sqrt((actualX-self.startX)**2+(actualY-self.startY)**2))
                    if actualX < self.startX: newInvAR = -invAR 
                    self.SendMountCommand("q", -1, controlMode, invAR, invDEC)
                    angolo = self.Angolo(actualX-self.startX, actualY-self.startY)
                    ready = True
                self.startX, self.startY = actualX, actualY
        print round(self.corrRateAR), round(self.corrRateDEC) #correction rate in msec/pixel
        return self.corrRateAR, self.corrRateDEC, newInvAR, newInvDEC, angolo, ready

    def SendPetacCorrection(self, lastInterval, petacVal, mountSpeed, controlMode):
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
                self.SendMountCommand("w", millisec, controlMode, False, False)
            elif ratio > 1 and ratio < MAX_RATIO:
                millisec = lastInterval*((ratio-1)/(1-ratio*(1-mountSpeed)))
                print ratio,": moving east for ", millisec, "millisecs"
                #no correction bigger than default interval
                if millisec < 0 or millisec > MAX_CORRECTION_FACT * petacVal:
                    millisec = MAX_CORRECTION_FACT * petacVal
                self.SendMountCommand("e", millisec, controlMode, False, False)

    def UpdatePetacValue(self, petacVal, petacIntervals, arDrift, corrRateAR, corrSpeed, invAR):
        #remember that petacVal(msec) is the right (medium) time interval b/w two mouse movements,
        #arDrift is the star shift (in AR) in pixel and corrRateAR is the correction speed in millisec/pixel
        if invAR:
            inv = -1
        else:
            inv = 1
        petacVal = petacVal + (arDrift*corrRateAR*(corrSpeed-1)*inv)/petacIntervals
##        TIME_WEIGHT = 600000 #ten minutes
##        TIME_SLOPE = 2
##        petacValueNow = totalTime/totalMouseCount
##        #with this weight function, petacValue will be deeply influenced by petacValueNow only after TIME_WEIGHT milliseconds
##        weight = 0.5*(1+tanh(TIME_SLOPE*(totalTime-TIME_WEIGHT)/TIME_WEIGHT))
##        print "weight = ", weight
##        petacVal += weight * (petacValueNow-petacValue)
        return petacVal

    def ExtractInt(self, stringa):
        l=0
        for t in stringa.split():
            try:
                l=int(float(t))
            except ValueError:
                pass
        return l

    def ExtractFloat(self, stringa):
        l=0
        for t in stringa.split():
            try:
                l=float(t)
            except ValueError:
                pass
        return l
    
    def DirChoose(self, startPath, testo):
        selectedDir = startPath
        dialog = wx.DirDialog(None, testo, style=1 ,defaultPath=startPath, pos = (10,10))
        if dialog.ShowModal() == wx.ID_OK:
            selectedDir = dialog.GetPath()
        dialog.Destroy()
        return selectedDir
