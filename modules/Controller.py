# -*- coding: UTF-8 -*-
# Controller.py: Controls management for GiGiWxCapture
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
from wx import xrc
import webbrowser
from string import strip
import thread
import os
path = os.path
listdir = os.listdir
import sys
from time import ctime
from math import sqrt

import View
import Model

class Controller(object):
    def __init__(self,parent):
        #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self.testMode = True
        #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self.testModeCounter = 0
        self.dcScreen=wx.ScreenDC()
        self.dcScreen.SetBrush(wx.TRANSPARENT_BRUSH)
        self.Processes=Model.Processes(self.dcScreen, self.testMode)
        self.Configuration=Model.Configuration("../configuration/GiGiWxConfig.txt", "../configuration/temp", "../language")
        #----------main frame
        resource=xrc.XmlResource(path.abspath("gigiwxGUI.xrc"))
        print path.abspath("gigiwxGUI.xrc")
        self.MainFrame=View.MainFrame(None,resource)
        self.GiGiWxIcon=wx.Icon(path.abspath("../images/GiGiWxCapture.ico"),wx.BITMAP_TYPE_ICO,32,32)
        self.MainFrame.SetIcon(self.GiGiWxIcon)
        self.MainFrame.ZoomFrame.SetIcon(self.GiGiWxIcon)
        self.MainFrame.AboutFrame.SetIcon(self.GiGiWxIcon)
        self.MainFrame.VampireFrame.SetIcon(self.GiGiWxIcon)
        self.MainFrame.GraphFrame.SetIcon(self.GiGiWxIcon)
        self.MainFrame.schede=xrc.XRCCTRL(self.MainFrame, "schede")
        self.MainFrame.petacTab=xrc.XRCCTRL(self.MainFrame, "PET-AC")
        self.MainFrame.Bind(wx.EVT_CLOSE, self.OnCloseMainWindow)
        self.MainFrame.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.ChangedTab, id=xrc.XRCID("schede"))
        #----------conf tab
        self.MainFrame.Bind(wx.EVT_BUTTON, self.OnVampireFrame, id=xrc.XRCID("selectcapturewindow"))
        self.MainFrame.Bind(wx.EVT_BUTTON, self.SaveCurrentConfiguration, id=xrc.XRCID("savecurrentconfig"))
        self.MainFrame.Bind(wx.EVT_BUTTON, self.LoadConfig, id=xrc.XRCID("reloadconfig"))

        self.MainFrame.mountportcombo = xrc.XRCCTRL(self.MainFrame, "mountportcombo")
        self.MainFrame.Bind(wx.EVT_COMBOBOX, self.MountPortSelect, id=xrc.XRCID("mountportcombo"))
        self.MainFrame.mountportcombo.Insert("none",0)
        self.MainFrame.mountportcombo.Insert("audio",1)
        for i in range(0,16):
            self.MainFrame.mountportcombo.Insert("serial "+str(i),i+2)
        self.MainFrame.mountportcombo.SetValue("none")
        
        self.MainFrame.camportcombo = xrc.XRCCTRL(self.MainFrame, "camportcombo")
        self.MainFrame.Bind(wx.EVT_COMBOBOX, self.CamPortSelect, id=xrc.XRCID("camportcombo"))
        self.MainFrame.camportcombo.Insert("none",0)
        self.MainFrame.camportcombo.Insert("audio",1)
        for i in range(0,16):
            self.MainFrame.camportcombo.Insert("serial "+str(i),i+2)
        self.MainFrame.camportcombo.SetValue("none")

        self.MainFrame.languagecombo = xrc.XRCCTRL(self.MainFrame, "languagecombo")
        self.MainFrame.Bind(wx.EVT_COMBOBOX, self.LanguageSelect, id=xrc.XRCID("languagecombo"))
        languageList = self.Configuration.ListFiles("../language")
        languageList.sort()
        for item in languageList:
            self.MainFrame.languagecombo.Append(item)
                #----------align tab
        self.MainFrame.Bind(wx.EVT_RADIOBUTTON, lambda evt, temp="s":
                            self.SetCalType(evt, temp), id=xrc.XRCID("starsouth"))
        self.MainFrame.Bind(wx.EVT_RADIOBUTTON, lambda evt, temp="e":
                            self.SetCalType(evt, temp), id=xrc.XRCID("stareast"))
        self.MainFrame.Bind(wx.EVT_RADIOBUTTON, lambda evt, temp="w":
                            self.SetCalType(evt, temp), id=xrc.XRCID("starwest"))
        self.MainFrame.guideSpeed = xrc.XRCCTRL(self.MainFrame, "speed")
        self.MainFrame.guideSpeed.Bind(wx.EVT_RADIOBOX, self.SetMountSpeed)
        self.MainFrame.Bind(wx.EVT_BUTTON, self.CameraOrientation, id=xrc.XRCID("cameraorientation"))
        self.MainFrame.alignOrientation = xrc.XRCCTRL(self.MainFrame, "cameraorientation")
        self.MainFrame.alignCorrection = xrc.XRCCTRL(self.MainFrame, "correction")
        self.MainFrame.Bind(wx.EVT_BUTTON, self.AlignCorrection, id=xrc.XRCID("correction"))
        self.MainFrame.alignInstr = xrc.XRCCTRL(self.MainFrame, "aligninstr")
        self.MainFrame.Bind(wx.EVT_BUTTON, self.ResetCorrection, id=xrc.XRCID("resetcorrection"))
        self.MainFrame.invertCorrection = xrc.XRCCTRL(self.MainFrame, "invertcorrection")
        self.MainFrame.invertCorrection.Bind(wx.EVT_CHECKBOX, lambda evt: self.MainFrame.VampireFrame.Refresh())
        self.MainFrame.savePE = xrc.XRCCTRL(self.MainFrame, "savepe")
        self.MainFrame.savePE.Bind(wx.EVT_CHECKBOX, self.PEwarning )
        #----------guide tab
        self.MainFrame.Bind(wx.EVT_BUTTON, self.CameraOrientation, id=xrc.XRCID("guidecameraorientation"))
        self.MainFrame.guideCalibrationOnOff = xrc.XRCCTRL(self.MainFrame,"guidecalibration")
        self.MainFrame.guideCalibrationOnOff.Enabled = False
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.GuideCalibrationRoutineStartStop, id=xrc.XRCID("guidecalibration"))
        self.MainFrame.arGuideValue = xrc.XRCCTRL(self.MainFrame,"arguidevalue")
        self.MainFrame.decGuideValue = xrc.XRCCTRL(self.MainFrame,"decguidevalue")
        self.MainFrame.arMinCorr = xrc.XRCCTRL(self.MainFrame,"armincorr")
        self.MainFrame.decMinCorr = xrc.XRCCTRL(self.MainFrame,"decmincorr")
        self.MainFrame.guideInterval = xrc.XRCCTRL(self.MainFrame,"guideinterval")
        self.MainFrame.invertAr = xrc.XRCCTRL(self.MainFrame,"invertar")
        self.MainFrame.invertDec = xrc.XRCCTRL(self.MainFrame,"invertdec")
        self.MainFrame.hiSens = xrc.XRCCTRL(self.MainFrame,"hisens")
        self.MainFrame.pulseguide = xrc.XRCCTRL(self.MainFrame,"pulseguide")
        self.MainFrame.calibrationSize = xrc.XRCCTRL(self.MainFrame,"calibrationsize")
        self.MainFrame.Bind(wx.EVT_BUTTON, self.SetImagesDir, id=xrc.XRCID("imagesdir"))
        self.MainFrame.maxDithering = xrc.XRCCTRL(self.MainFrame,"maxdithering")
        self.MainFrame.dithStep = xrc.XRCCTRL(self.MainFrame,"dithstep")
        self.MainFrame.dithInterval = xrc.XRCCTRL(self.MainFrame, "dithinterval")
        self.MainFrame.guideInstr = xrc.XRCCTRL(self.MainFrame,"guideinstr")
        self.MainFrame.guideOnOff = xrc.XRCCTRL(self.MainFrame,"guideonoff")
        self.MainFrame.guideOnOff.Enabled = False
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.GuideStartStop, id=xrc.XRCID("guideonoff"))
        #----------PET-AC tab
        self.MainFrame.petacguideCalibrationOnOff = xrc.XRCCTRL(self.MainFrame,"petacguidecalibration")
        self.MainFrame.petacguideCalibrationOnOff.Enabled = False
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.GuideCalibrationRoutineStartStop, id=xrc.XRCID("petacguidecalibration"))
        self.MainFrame.petacInvertAr = xrc.XRCCTRL(self.MainFrame,"petacinvertar")
        self.MainFrame.petacInvertDec = xrc.XRCCTRL(self.MainFrame,"petacinvertdec")
        self.MainFrame.petacArGuideValue = xrc.XRCCTRL(self.MainFrame,"petacarguidevalue")
        self.MainFrame.petacDecGuideValue = xrc.XRCCTRL(self.MainFrame,"petacdecguidevalue")
        self.MainFrame.petacCalOnOff = xrc.XRCCTRL(self.MainFrame,"petaccalonoff")
        self.MainFrame.petacCalOnOff.Enabled = False
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.PetacCalStartStop, id=xrc.XRCID("petaccalonoff"))
        self.MainFrame.petacCalOnOff.Bind(wx.EVT_MOTION, self.MouseMovingOnPetacButton)
        self.MainFrame.petacValue = xrc.XRCCTRL(self.MainFrame,"petacvalue")
        self.MainFrame.petacMinCorr = xrc.XRCCTRL(self.MainFrame,"petacmincorr")
        self.MainFrame.petacMountLowSpeed = xrc.XRCCTRL(self.MainFrame,"petacmountlowspeed")
        self.MainFrame.petacMaxDithering = xrc.XRCCTRL(self.MainFrame,"petacmaxdithering")
        self.MainFrame.petacDithStep = xrc.XRCCTRL(self.MainFrame,"petacdithstep")
        self.MainFrame.petacInstr = xrc.XRCCTRL(self.MainFrame,"petacinstr")
        self.MainFrame.petacOnOff = xrc.XRCCTRL(self.MainFrame,"petaconoff")
        self.MainFrame.petacOnOff.Enabled = False
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.PetacStartStop, id=xrc.XRCID("petaconoff"))
        self.MainFrame.petacOnOff.Bind(wx.EVT_MOTION, self.MouseMovingOnPetacButton)
        #----------tools tab
        self.MainFrame.Bind(wx.EVT_BUTTON, self.OnZoomFrame, id=xrc.XRCID("zoom2x"))
        self.MainFrame.zoom2x = xrc.XRCCTRL(self.MainFrame, "zoom2x")
        self.MainFrame.crosshair = xrc.XRCCTRL(self.MainFrame, "crosshair")
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.CrosshairAct, id=xrc.XRCID("crosshair"))
        self.MainFrame.fwhmCalc = xrc.XRCCTRL(self.MainFrame, "fwhm")
        self.MainFrame.Bind(wx.EVT_TOGGLEBUTTON, self.FwhmStart, id=xrc.XRCID("fwhm"))
        self.MainFrame.takePicture = xrc.XRCCTRL(self.MainFrame, "takeapicture")
        self.MainFrame.Bind(wx.EVT_BUTTON, self.SavePicture, id=xrc.XRCID("takeapicture"))
        self.MainFrame.pictureNo = xrc.XRCCTRL(self.MainFrame, "pictureno")
        self.MainFrame.pictureInt = xrc.XRCCTRL(self.MainFrame, "pictureint")
        self.MainFrame.picProgress = xrc.XRCCTRL(self.MainFrame, "picprogress")
        self.MainFrame.picFullScreen = xrc.XRCCTRL(self.MainFrame, "picfullscreen")
        self.MainFrame.picFullScreen.Bind(wx.EVT_CHECKBOX, self.PicFullScreen)
        self.MainFrame.pixelLabel = xrc.XRCCTRL(self.MainFrame, "pixellabel")
        self.MainFrame.ccdW = xrc.XRCCTRL(self.MainFrame, "ccdw")
        self.MainFrame.ccdH = xrc.XRCCTRL(self.MainFrame, "ccdh")
        self.MainFrame.focal = xrc.XRCCTRL(self.MainFrame, "focal")
        self.MainFrame.field = xrc.XRCCTRL(self.MainFrame, "field")
        self.MainFrame.Bind(wx.EVT_TEXT, self.FieldUpdate, id=xrc.XRCID("ccdw"))
        self.MainFrame.Bind(wx.EVT_TEXT, self.FieldUpdate, id=xrc.XRCID("ccdh"))
        self.MainFrame.Bind(wx.EVT_TEXT, self.FieldUpdate, id=xrc.XRCID("focal"))
        self.MainFrame.guideSpeed1 = xrc.XRCCTRL(self.MainFrame, "speed1")
        self.MainFrame.guideSpeed1.Bind(wx.EVT_RADIOBOX, self.SetMountSpeed)
        self.MainFrame.mountStopPic = xrc.XRCCTRL(self.MainFrame, "mountstop")
        self.MainFrame.mountStopPic1 = xrc.XRCCTRL(self.MainFrame, "mountstop1")
        self.MainFrame.mountLeftPic = xrc.XRCCTRL(self.MainFrame, "mountleft")
        self.MainFrame.mountLeftPic1 = xrc.XRCCTRL(self.MainFrame, "mountleft1")
        self.MainFrame.mountRightPic = xrc.XRCCTRL(self.MainFrame, "mountright")
        self.MainFrame.mountRightPic1 = xrc.XRCCTRL(self.MainFrame, "mountright1")
        self.MainFrame.mountUpPic = xrc.XRCCTRL(self.MainFrame, "mountup")
        self.MainFrame.mountUpPic1 = xrc.XRCCTRL(self.MainFrame, "mountup1")
        self.MainFrame.mountDownPic = xrc.XRCCTRL(self.MainFrame, "mountdown")
        self.MainFrame.mountDownPic1 = xrc.XRCCTRL(self.MainFrame, "mountdown1")
        #----------Help tab
        self.MainFrame.Bind(wx.EVT_BUTTON, self.OnAboutFrame, id=xrc.XRCID("helpbutton"))
        self.MainFrame.Bind(wx.EVT_BUTTON, self.OnAboutFrame, id=xrc.XRCID("about"))
        #----------Vampire Frame
        self.MainFrame.VampireFrame.vampirePanel = xrc.XRCCTRL(self.MainFrame.VampireFrame, "vampirepanel")
        self.MainFrame.VampireFrame.vampirePanel.Bind(wx.EVT_MOTION, self.MouseMovingOnVampire)
        self.MainFrame.VampireFrame.vampireLabel = xrc.XRCCTRL(self.MainFrame.VampireFrame, "vampirelabel")
        self.MainFrame.VampireFrame.Bind(wx.EVT_SIZE, self.SizeObserver)
        self.MainFrame.VampireFrame.Bind(wx.EVT_MOVE, self.SizeObserver)
        self.MainFrame.VampireFrame.vampirePanel.Bind(wx.EVT_RIGHT_UP, self.RightClickOnVampire)
        self.MainFrame.VampireFrame.vampirePanel.Bind(wx.EVT_LEFT_UP, self.LeftClickOnVampire)
        self.MainFrame.VampireFrame.windowconfirm = xrc.XRCCTRL(self.MainFrame.VampireFrame, "windowconfirm")
        self.MainFrame.VampireFrame.Bind(wx.EVT_BUTTON, self.WindowConfirm, id=xrc.XRCID("windowconfirm"))
        self.MainFrame.VampireFrame.vampirePanel.Bind(wx.EVT_KEY_DOWN, self.KeyDownVampire)
        self.MainFrame.VampireFrame.vampirePanel.Bind(wx.EVT_KEY_UP, self.KeyUpVampire)
        self.MainFrame.VampireFrame.Bind(wx.EVT_KEY_DOWN, self.KeyDownVampire)
        self.MainFrame.VampireFrame.Bind(wx.EVT_KEY_UP, self.KeyUpVampire)
        #----------Zoom Frame
        self.MainFrame.ZoomFrame.Bind(wx.EVT_SIZE, self.SizeObserver)
        self.MainFrame.ZoomFrame.Bind(wx.EVT_CLOSE, self.OnCloseZoomWindow)
        #----------Graph Frame
        self.MainFrame.GraphFrame.Bind(wx.EVT_CLOSE, self.OnCloseGraphWindow)
        self.MainFrame.GraphFrame.graphPanel = xrc.XRCCTRL(self.MainFrame.GraphFrame, "graphpanel")
        self.MainFrame.GraphFrame.showGraph1 = xrc.XRCCTRL(self.MainFrame.GraphFrame, "showgraph1")
        self.MainFrame.GraphFrame.showGraph2 = xrc.XRCCTRL(self.MainFrame.GraphFrame, "showgraph2")
        self.MainFrame.GraphFrame.showGraph3 = xrc.XRCCTRL(self.MainFrame.GraphFrame, "showgraph3")
        self.MainFrame.GraphFrame.showGraph4 = xrc.XRCCTRL(self.MainFrame.GraphFrame, "showgraph4")
        self.MainFrame.GraphFrame.showGraph1.SetValue(True)
        self.MainFrame.GraphFrame.showGraph2.SetValue(True)
        self.MainFrame.GraphFrame.showGraph3.SetValue(True)
        self.MainFrame.GraphFrame.showGraph4.SetValue(True)
        self.MainFrame.GraphFrame.graphPanel.Bind(wx.EVT_SIZE, self.SizeGraphFrame)
        self.MainFrame.GraphFrame.numPoints = xrc.XRCCTRL(self.MainFrame.GraphFrame, "numpoints")
        #----------About Frame
        self.MainFrame.AboutFrame.description = xrc.XRCCTRL(self.MainFrame.AboutFrame, "description")
        self.MainFrame.AboutFrame.helpText = xrc.XRCCTRL(self.MainFrame.AboutFrame, "helptext")
        self.MainFrame.AboutFrame.name = xrc.XRCCTRL(self.MainFrame.AboutFrame, "name")
        self.MainFrame.AboutFrame.city = xrc.XRCCTRL(self.MainFrame.AboutFrame, "city")
        self.MainFrame.AboutFrame.comment = xrc.XRCCTRL(self.MainFrame.AboutFrame, "comment")
        self.MainFrame.AboutFrame.name.Bind(wx.EVT_LEFT_DOWN, self.OnNameClick)
        self.MainFrame.AboutFrame.city.Bind(wx.EVT_LEFT_DOWN, self.OnCityClick)
        self.MainFrame.AboutFrame.comment.Bind(wx.EVT_LEFT_DOWN, self.OnCommentClick)
        self.MainFrame.AboutFrame.Bind(wx.EVT_BUTTON, self.SendId, id=xrc.XRCID("sendid"))
        self.MainFrame.AboutFrame.Bind(wx.EVT_BUTTON, self.SendHelpReq, id=xrc.XRCID("helpreq"))
        self.MainFrame.AboutFrame.Bind(wx.EVT_CLOSE, self.OnCloseAboutWindow)
        self.MainFrame.GraphFrame.Bind(wx.EVT_CLOSE, self.OnCloseGraphWindow)
        #----------system output
        self.filelog = open('../out.log', 'w')
        if (self.testMode):
            sys.stdout = self.MainFrame.AboutFrame.helpText
        else:
            sys.stdout = self.filelog #redirect text output to log file
            sys.stderr = self.filelog #redirect error output to log file
        #----------constS
        self.MIN_PIX_STEP = 20 #minimum difference between pixel to find window border
        self.CIRCLE_DIAMETER = 20 #px: diameter of the drawn circle
        self.WINDOWBAR_H = 20 #px: height of the window bar 
        self.MIN_CORR_TIME = 5 #secs: time for vibrations dumping
        self.PETAC_CAL_BUTTON_CENTER_X = 80 #px: petac calibration button position
        self.PETAC_CAL_BUTTON_CENTER_Y = 112 #px: petac calibration button position
        self.PETAC_BUTTON_CENTER_X = 80 #px: petac button position
        self.PETAC_BUTTON_CENTER_Y = 293 #px: petac button position
        #self.CALC_INTERVAL = 1000 #millisecs: time between calculations
        self.STAR_TRACK_INTERVAL = 500 #millisecs: time between startrack calls
        self.MIN_CALIBRATION_TIME = 300 #secs: min time for petac calibration
        #----------InitVar
        self.alphaAmount=254
        self.starPosition="s"
        self.timerShowHideVampire = wx.Timer(self.MainFrame)
        self.hideVampire = False
        self.MainFrame.Bind(wx.EVT_TIMER, self.AlphaCycle, self.timerShowHideVampire)

        self.drawClock = wx.Timer(self.MainFrame)
        self.drawClock.Start(10)
        self.MainFrame.Bind(wx.EVT_TIMER, self.DrawClock, self.drawClock)
        
        self.picSaveClock = wx.Timer(self.MainFrame)
        self.MainFrame.Bind(wx.EVT_TIMER, self.PicSaveClock, self.picSaveClock)

        self.calcClock = wx.Timer(self.MainFrame)
        self.MainFrame.Bind(wx.EVT_TIMER, self.CalcClock, self.calcClock)

        self.zoomClock=wx.Timer(self.MainFrame)
        self.MainFrame.Bind(wx.EVT_TIMER, self.TimerToPaint, self.zoomClock)
        self.MainFrame.ZoomFrame.Bind(wx.EVT_PAINT, self.ZoomRefresh)

        self.xs, self.ys=-50, -50
        self.genericCounter = 0 #a class variable for every use...
        self.starTracking = False
        self.crosshairXs, self.crosshairYs=-50, -50
        self.actualX = 320
        self.actualY = 240
        self.vampirePosX = 0
        self.vampirePosY = 0
        self.vampireSizeX = 0
        self.vampireSizeY = 0
        self.timeFromClick = wx.StopWatch() #create stopwatch
        self.timeFromLastGuide = wx.StopWatch() #create stopwatch
        self.controlMode = "none"
        self.camControlMode = "none"
        self.LoadConfig(None)
        self.LoadTemp()
        self.MainFrame.AboutFrame.description.Label = self.testo[24]
        self.MainFrame.AboutFrame.helpText.Value = self.testo[38].replace("//", "\n")
        self.MainFrame.AboutFrame.description.Wrap(280)
        self.MainFrame.VampireFrame.vampireLabel.Label = self.testo[28].replace("//", "\n")
        self.MainFrame.VampireFrame.vampireLabel.Wrap(400)
        self.MountPortSelect(None)
        self.correzione = 0
        self.ditherCount = 0
        self.lastMoveTime = 0
        self.movementTime = 0
        self.storedImageSignature = 0
        self.graph1List = [(0.0,0.0)]
        self.graph2List = [(0.0,0.0)]
        self.graph3List = [(0.0,0.0)]
        self.graph4List = [(0.0,0.0)]
        self.SetStatus("waiting_for_vampire_victim")

#---- config&load
    def LoadConfig(self,evt):
        if evt != None:
            dial = wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[18], 'Question',
               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            ret = dial.ShowModal()
            if ret == wx.ID_YES:
                self.Configuration.LoadConfiguration()
                self.ValuesFromConfig()
                self.LanguageSelect("none")
        else:
            self.Configuration.LoadConfiguration()
            self.ValuesFromConfig()
            self.LanguageSelect("none")

    def SaveCurrentConfiguration(self,evt):
        self.ValuesToConfig()
        if self.Configuration.IsConfigurationChanged():
            dial = wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[19], 'Question',
               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            ret = dial.ShowModal()
            if ret == wx.ID_YES:
                self.Configuration.SaveConfiguration()
                dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[26], 'Info', wx.OK | wx.ICON_INFORMATION)
                dial.ShowModal()
        else:
            dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[25], 'Info', wx.OK | wx.ICON_INFORMATION)
            dial.ShowModal()

    def ValuesFromConfig(self):
        #read values from config file
        self.MainFrame.languagecombo.Value = "eng"
        self.MainFrame.mountportcombo.Value = "none"
        self.MainFrame.camportcombo.Value = "none"
        self.MainFrame.invertCorrection.Value = False
        self.MainFrame.arMinCorr.Value = "50"
        self.MainFrame.decMinCorr.Value = "50"
        self.MainFrame.guideInterval.Value = "2"
        self.MainFrame.maxDithering.Value = "2"
        self.MainFrame.petacMaxDithering.Value = "2"
        self.MainFrame.dithStep.Value = "0"
        self.MainFrame.petacDithStep.Value = "0"
        self.MainFrame.dithInterval.Value = "10"
        self.MainFrame.petacMinCorr.Value = "50"
        self.MainFrame.petacMountLowSpeed.Value = "1.0"
        self.MainFrame.hiSens.Value = False
        self.MainFrame.pulseguide.Value = False
        self.MainFrame.calibrationSize.Value = "150"
        self.configLines = self.Configuration.ConfigLines()
        try:
            if self.configLines[5]<>"": self.MainFrame.languagecombo.Value = strip(self.configLines[5])
            if self.configLines[7]<>"": self.MainFrame.mountportcombo.Value = strip(self.configLines[7])
            if self.configLines[9]<>"": self.MainFrame.camportcombo.Value = strip(self.configLines[9])
            if self.configLines[11]<>"": self.MainFrame.invertCorrection.Value = bool(self.Processes.ExtractInt(self.configLines[11]))
            if self.configLines[13]<>"": self.MainFrame.arMinCorr.Value = str(self.Processes.ExtractInt(self.configLines[13]))
            if self.configLines[15]<>"": self.MainFrame.decMinCorr.Value = str(self.Processes.ExtractInt(self.configLines[15]))
            if self.configLines[17]<>"": self.MainFrame.guideInterval.Value = str(self.Processes.ExtractInt(self.configLines[17]))
            if self.configLines[19]<>"": self.MainFrame.maxDithering.Value = str(self.Processes.ExtractInt(self.configLines[19]))
            if self.configLines[19]<>"": self.MainFrame.petacMaxDithering.Value = str(self.Processes.ExtractInt(self.configLines[19]))
            if self.configLines[21]<>"": self.MainFrame.dithStep.Value = str(self.Processes.ExtractInt(self.configLines[21]))
            if self.configLines[21]<>"": self.MainFrame.petacDithStep.Value = str(self.Processes.ExtractInt(self.configLines[21]))
            if self.configLines[23]<>"": self.MainFrame.dithInterval.Value = str(self.Processes.ExtractInt(self.configLines[23]))
            if self.configLines[25]<>"": self.MainFrame.petacMinCorr.Value = str(self.Processes.ExtractInt(self.configLines[25]))
            if self.configLines[27]<>"": self.MainFrame.petacMountLowSpeed.Value = str(self.Processes.ExtractFloat(self.configLines[27]))
            if self.configLines[29]<>"": self.MainFrame.hiSens.Value = bool(self.Processes.ExtractInt(self.configLines[29]))
            if self.configLines[31]<>"": self.MainFrame.pulseguide.Value = bool(self.Processes.ExtractInt(self.configLines[31]))
            if self.configLines[33]<>"": self.MainFrame.calibrationSize.Value = str(self.Processes.ExtractInt(self.configLines[33]))
            if self.configLines[35]<>"": self.R = self.Processes.ExtractFloat(self.configLines[35])
            if self.configLines[36]<>"": self.Q = self.Processes.ExtractFloat(self.configLines[36])
            if self.configLines[38]<>"": self.k1 = self.Processes.ExtractFloat(self.configLines[38])
            if self.configLines[39]<>"": self.k2 = self.Processes.ExtractFloat(self.configLines[39])
        except:
            pass
            
    def ValuesToConfig(self):
        #write values to config file
        self.configLines[5] = str(self.MainFrame.languagecombo.Value)
        self.configLines[7] = str(self.MainFrame.mountportcombo.Value)
        self.configLines[9] = str(self.MainFrame.camportcombo.Value)
        self.configLines[11] = str(self.Processes.ExtractInt(str(int(self.MainFrame.invertCorrection.Value))))    
        self.configLines[13] = str(self.Processes.ExtractInt(self.MainFrame.arMinCorr.Value))
        self.configLines[15] = str(self.Processes.ExtractInt(self.MainFrame.decMinCorr.Value))
        self.configLines[17] = str(self.Processes.ExtractInt(self.MainFrame.guideInterval.Value))
        self.configLines[19] = str(self.Processes.ExtractInt(self.MainFrame.maxDithering.Value))
        self.configLines[21] = str(self.Processes.ExtractInt(self.MainFrame.dithStep.Value))
        self.configLines[23] = str(self.Processes.ExtractInt(self.MainFrame.dithInterval.Value))
        self.configLines[25] = str(self.Processes.ExtractInt(self.MainFrame.petacMinCorr.Value))
        self.configLines[27] = str(self.Processes.ExtractFloat(self.MainFrame.petacMountLowSpeed.Value))
        self.configLines[29] = str(self.Processes.ExtractInt(str(int(self.MainFrame.hiSens.Value))))
        self.configLines[31] = str(self.Processes.ExtractInt(str(int(self.MainFrame.pulseguide.Value))))
        self.configLines[33] = str(self.Processes.ExtractInt(self.MainFrame.calibrationSize.Value))
        self.configLines[35] = str(self.R)
        self.configLines[36] = str(self.Q)
        self.configLines[38] = str(self.k1)
        self.configLines[39] = str(self.k2)
        self.Configuration.ConfigLinesUpdate(self.configLines)
    
    def LoadTemp(self):
        #read values from temp file (auto updated without asking)
        tempLines = self.Configuration.LoadTempFile()
        self.MainFrame.arGuideValue.Value = "0"
        self.MainFrame.petacArGuideValue.Value = "0"
        self.MainFrame.decGuideValue.Value = "0"
        self.MainFrame.petacDecGuideValue.Value = "0"
        self.MainFrame.invertAr.Value = False
        self.MainFrame.petacInvertAr.Value = False
        self.MainFrame.invertDec.Value = False
        self.MainFrame.petacInvertDec.Value = False
        self.MainFrame.petacValue.Value = "0"
        self.MainFrame.ccdW.Value = "0"
        self.MainFrame.ccdH.Value = "0"
        self.MainFrame.focal.Value = "0"
        self.angolo = 0.0
        self.imagesPath = ""
        self.collimatorSize = "0"
        self.crosshairColorCode = "0"
        try:
            self.MainFrame.arGuideValue.Value = str(self.Processes.ExtractFloat(tempLines[0]))
            self.MainFrame.petacArGuideValue.Value = str(self.Processes.ExtractFloat(tempLines[0]))
            self.MainFrame.decGuideValue.Value = str(self.Processes.ExtractFloat(tempLines[1]))
            self.MainFrame.petacDecGuideValue.Value = str(self.Processes.ExtractFloat(tempLines[1]))
            self.MainFrame.invertAr.Value = bool(self.Processes.ExtractInt(tempLines[2]))
            self.MainFrame.petacInvertAr.Value = bool(self.Processes.ExtractInt(tempLines[2]))
            self.MainFrame.invertDec.Value = bool(self.Processes.ExtractInt(tempLines[3]))
            self.MainFrame.petacInvertDec.Value = bool(self.Processes.ExtractInt(tempLines[3]))
            self.MainFrame.petacValue.Value = str(self.Processes.ExtractFloat(tempLines[4]))
            self.MainFrame.ccdW.Value = str(self.Processes.ExtractFloat(tempLines[5]))
            self.MainFrame.ccdH.Value = str(self.Processes.ExtractFloat(tempLines[6]))
            self.MainFrame.focal.Value = str(self.Processes.ExtractInt(tempLines[7]))
            self.angolo = self.Processes.ExtractFloat(tempLines[8])
            self.imagesPath = str(tempLines[9])
            self.collimatorSize = self.Processes.ExtractInt(tempLines[10])
            self.crosshairColorCode = self.Processes.ExtractInt(tempLines[11])
        except:
            pass

    def SaveTemp(self):
        #save values to temp configuration file
        tempLines = []
        tempLines.append(str(self.Processes.ExtractFloat(self.MainFrame.arGuideValue.Value)))
        tempLines.append(str(self.Processes.ExtractFloat(self.MainFrame.decGuideValue.Value)))
        tempLines.append(str(self.Processes.ExtractInt(str(int(self.MainFrame.invertAr.Value)))))
        tempLines.append(str(self.Processes.ExtractInt(str(int(self.MainFrame.invertDec.Value)))))
        tempLines.append(str(self.Processes.ExtractFloat(self.MainFrame.petacValue.Value)))
        tempLines.append(str(self.Processes.ExtractFloat(self.MainFrame.ccdW.Value)))
        tempLines.append(str(self.Processes.ExtractFloat(self.MainFrame.ccdH.Value)))
        tempLines.append(str(self.Processes.ExtractInt(self.MainFrame.focal.Value)))
        tempLines.append(str(self.angolo))
        tempLines.append(str(self.imagesPath))
        tempLines.append(str(self.collimatorSize))
        tempLines.append(str(self.crosshairColorCode))
        self.Configuration.SaveTempFile(tempLines)
        
#---- Status
    def SetStatus(self, status):
        #set the variables and call methods when the status changes
        print status
        self.status = status
        if status == "camera_orientation_begin":
            self.starTracking = False
            self.correzione = 0
            self.verso = 0
            self.MainFrame.alignInstr.Value = self.testo[1]
            self.MainFrame.guideInstr.Value = self.testo[1]

        elif status == "camera_orientation_first_star":
            self.starTracking = False
            self.dcScreen.SetPen(wx.Pen(wx.RED,2))
            self.dcScreen.DrawLineList(self.Processes.CrossList(round(self.actualX),round(self.actualY),21, 30))
            self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY)
            self.dcScreen.DrawLineList(self.Processes.CrossList(round(self.actualX),round(self.actualY),21, 30))
            self.xo, self.yo = self.actualX, self.actualY
            self.SetStatus("camera_orientation_first_star_acq")

        elif status == "camera_orientation_first_star_acq":
            self.MainFrame.alignInstr.Value = self.testo[2]
            self.MainFrame.guideInstr.Value = self.testo[2]

        elif status == "camera_orientation_second_star_acq":
            self.dcScreen.SetPen(wx.Pen(wx.RED,2))
            self.dcScreen.DrawLineList(self.Processes.CrossList(round(self.actualX),round(self.actualY),21, 30))
            self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY)
            self.dcScreen.DrawLineList(self.Processes.CrossList(round(self.actualX),round(self.actualY),21, 30))
            self.xf, self.yf = self.actualX, self.actualY
            a = self.xf - self.xo
            b = self.yf - self.yo
            if abs(a)>100 or abs(b)>100:
                self.angolo = self.Processes.Angolo(a, b)
                self.SaveTemp()
                self.SetStatus("alignment_cam_calibrated")
            else:
                dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[20], 'Info', wx.OK | wx.ICON_INFORMATION)
                dial.ShowModal()
                self.SetStatus("idle")

        elif status == "alignment_cam_calibrated":
            if self.correzione==0: self.MainFrame.alignInstr.Value = str(round(-self.angolo*180/3.14,1)) + " " + self.testo[3]
            self.MainFrame.guideInstr.Value = str(round(-self.angolo*180/3.14,1)) + " " + self.testo[14]
            self.MainFrame.alignCorrection.Enabled = True
            self.timeFromClick.Start() #reset stopwatch
            self.starTracking = False
            if self.starPosition=="s":
                self.MainFrame.alignCorrection.SetLabel(label="Azimuth Correction")
            else:
                self.MainFrame.alignCorrection.SetLabel(label="Elevation Correction")

        elif status == "alignment_star_waiting":
            self.MainFrame.alignInstr.Value = self.testo[4]
            self.MainFrame.alignCorrection.Label ="Undo"
            self.xo = -1

        elif status == "alignment_star_tracking":
            self.starTracking = True
            self.OnGraphFrame(None, 50) #graph for fwhm
            self.calcClock.Start(self.STAR_TRACK_INTERVAL)
            self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY)
            self.xo = -1

        elif status == "alignment_calc_ready":
            pass

        elif self.status == "fwhm_wait":
            pass

        elif self.status == "fwhm_calc":
            self.starTracking = True
            self.graph1List = [(0.0,0.0)]
            self.OnGraphFrame(None, 10) #graph for fwhm
            self.calcClock.Start(self.STAR_TRACK_INTERVAL)
            self.timeFromClick.Start() #reset stopwatch

        elif self.status == "guide_calibration_waiting":
            self.MainFrame.guideInstr.Value = self.testo[12]
            self.MainFrame.petacInstr.Value = self.testo[12]

        elif self.status == "guide_calibrating":
            self.starTracking = True
            self.calibrationSize = float(self.MainFrame.calibrationSize.Value)
            self.calcClock.Start(self.STAR_TRACK_INTERVAL)
            self.MainFrame.guideSpeed.SetSelection(0)
            self.MainFrame.guideSpeed1.SetSelection(0)
            self.Processes.GuideCalibrationRoutineStart()
            self.MainFrame.guideInstr.Value = self.testo[21]
            self.MainFrame.petacInstr.Value = self.testo[21]
            
        elif self.status == "guide_star_waiting":
            self.MainFrame.guideInstr.Value = self.testo[15]

        elif self.status == "guiding":
            print "GUIDE VALUES: ", self.MainFrame.arGuideValue.Value, self.MainFrame.decGuideValue.Value, "; invar-dec:", self.MainFrame.invertAr.Value, self.MainFrame.invertDec.Value, "; angle:", self.angolo*57.3
            self.Processes.KalmanFilterReset(self.R, self.Q)
            self.Processes.GuideCalcReset(self.k1, self.k2)
            self.MainFrame.guideCalibrationOnOff.Enabled = False
            self.MainFrame.arGuideValue.Enabled = False
            self.MainFrame.decGuideValue.Enabled = False
            self.MainFrame.arMinCorr.Enabled = False
            self.MainFrame.decMinCorr.Enabled = False
            self.MainFrame.guideInterval.Enabled = False
            self.MainFrame.invertAr.Enabled = False
            self.MainFrame.invertDec.Enabled = False
            self.MainFrame.maxDithering.Enabled = False
            self.MainFrame.dithStep.Enabled = False
            self.MainFrame.dithInterval.Enabled = False
            self.MainFrame.hiSens.Enabled = False
            self.MainFrame.pulseguide.Enabled = False
            self.meanARdrift = 0
            self.meanDECdrift = 0
            self.MainFrame.guideSpeed.SetSelection(0)
            self.MainFrame.guideSpeed1.SetSelection(0)
            self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY)
            self.guideCenterX, self.guideCenterY = self.actualX, self.actualY
            self.dithInterval = max(float(self.MainFrame.dithInterval.Value),1)
            self.MainFrame.dithInterval.Value = str(int(self.dithInterval))
            self.Processes.DitheringInit(float(self.MainFrame.maxDithering.Value), float(self.MainFrame.dithStep.Value))
            self.starTracking = True
            self.ditherCount = self.Processes.CountFiles(self.imagesPath)
            self.guideIntervalSec = float(self.MainFrame.guideInterval.Value)
            self.Processes.SetCamLE(True, self.camControlMode)
            self.Processes.GuideRoutineStart(self.MainFrame.invertAr.Value, self.MainFrame.invertDec.Value,
                                             float(self.MainFrame.arMinCorr.Value), float(self.MainFrame.decMinCorr.Value), 
                                             float(self.MainFrame.arGuideValue.Value), float(self.MainFrame.decGuideValue.Value), 
                                             1000*self.guideIntervalSec, self.MainFrame.pulseguide.Value)
            if self.guideIntervalSec > 0:
                self.OnGraphFrame(None, 100)
                self.calcClock.Stop()
                self.calcClock.Start(self.STAR_TRACK_INTERVAL)
                self.timeFromLastGuide.Start() #reset stopwatch
                self.timeFromClick.Start() #reset stopwatch
            else:
                self.MainFrame.guideInstr.Value = "bad guide interval"
                self.SetStatus("idle")

        elif self.status == "petac_calibration":
            self.MainFrame.petacInstr.Value = self.testo[34]
            self.MainFrame.petacguideCalibrationOnOff.Enabled = False
            self.MainFrame.petacArGuideValue.Enabled = False
            self.MainFrame.petacDecGuideValue.Enabled = False
            self.MainFrame.petacInvertAr.Enabled = False
            self.MainFrame.petacInvertDec.Enabled = False
            self.MainFrame.petacMinCorr.Enabled = False
            self.MainFrame.petacMountLowSpeed.Enabled = False
            self.MainFrame.petacMaxDithering.Enabled = False
            self.MainFrame.petacDithStep.Enabled = False
            self.MainFrame.petacValue.Enabled = True
            self.MainFrame.petacOnOff.Enabled = False
            self.petacVal = float(self.MainFrame.petacValue.Value) #retrieve last petac value
            self.calcClock.Stop()
            self.timeFromClick.Start()
            self.movementCounter = 0

        elif self.status == "petac_star_waiting":
            self.MainFrame.petacInstr.Value = self.testo[15]

        elif self.status == "petac_operating":
            self.MainFrame.petacTab.WarpPointer(self.PETAC_BUTTON_CENTER_X, self.PETAC_BUTTON_CENTER_Y) #center the mouse in the button
            self.MainFrame.petacInstr.Value = self.testo[37]
            self.MainFrame.petacguideCalibrationOnOff.Enabled = False
            self.MainFrame.petacArGuideValue.Enabled = False
            self.MainFrame.petacDecGuideValue.Enabled = False
            self.MainFrame.petacInvertAr.Enabled = False
            self.MainFrame.petacInvertDec.Enabled = False
            self.MainFrame.petacCalOnOff.Enabled = False
            self.MainFrame.petacValue.Enabled = False
            self.MainFrame.petacMinCorr.Enabled = False
            self.MainFrame.petacMountLowSpeed.Enabled = False
            self.MainFrame.petacMaxDithering.Enabled = False
            self.MainFrame.petacDithStep.Enabled = False
            self.guideCenterX, self.guideCenterY = self.actualX, self.actualY
            self.Processes.DitheringInit(float(self.MainFrame.petacMaxDithering.Value), float(self.MainFrame.petacDithStep.Value))
            self.guideIntervalSec = float(self.MainFrame.guideInterval.Value)
            self.petacVal = float(self.MainFrame.petacValue.Value) #retrieve last petac value
            self.calcClock.Stop()
            self.starTracking = True
            self.movementCounter = 0
            
        elif self.status == "waiting_for_vampire_victim":
            self.CtrlEnable(False)
            self.calcClock.Stop()
            self.ShowVampire(None)
            self.MainFrame.VampireFrame.Maximize()
            self.MainFrame.VampireFrame.windowconfirm.Hide()
        
        elif self.status == "waiting_for_vampire_victim_confirm":
            xmin, ymin, xmax, ymax = self.Processes.EnlargeToWindow(self.actualX, self.actualY, self.MIN_PIX_STEP, 100)
            self.MainFrame.VampireFrame.SetPosition((xmin, ymin))
            self.MainFrame.VampireFrame.SetSize((xmax-xmin, ymax-ymin-self.WINDOWBAR_H))
            self.MainFrame.VampireFrame.Show()
            self.MainFrame.VampireFrame.Maximize(0)
            self.MainFrame.VampireFrame.windowconfirm.Show()
        #----
        elif self.status == "idle":
            #guide idle
            self.Processes.SendMountCommand("q", False)
            self.MainFrame.guideSpeed.SetSelection(1)
            self.MainFrame.guideSpeed1.SetSelection(1)
            self.Processes.SendMountCommand("1", False) #set speed to "min speed" (min)
            self.MainFrame.guideCalibrationOnOff.Value = False
            self.MainFrame.guideOnOff.Value = False
            self.MainFrame.petacCalOnOff.Value = False
            self.MainFrame.petacOnOff.Value = False
            self.starTracking = False
            self.calcClock.Stop()
            self.MainFrame.guideCalibrationOnOff.Enabled = True
            self.MainFrame.arGuideValue.Enabled = True
            self.MainFrame.decGuideValue.Enabled = True
            self.MainFrame.arMinCorr.Enabled = True
            self.MainFrame.decMinCorr.Enabled = True
            self.MainFrame.guideInterval.Enabled = True
            self.MainFrame.invertAr.Enabled = True
            self.MainFrame.invertDec.Enabled = True
            self.MainFrame.hiSens.Enabled = True
            self.MainFrame.pulseguide.Enabled = True
            self.MainFrame.maxDithering.Enabled = True
            self.MainFrame.dithStep.Enabled = True
            self.MainFrame.dithInterval.Enabled = True
            self.MainFrame.petacguideCalibrationOnOff.Enabled = True
            self.MainFrame.petacOnOff.Enabled = True
            self.MainFrame.petacCalOnOff.Enabled = True
            self.MainFrame.petacArGuideValue.Enabled = True
            self.MainFrame.petacDecGuideValue.Enabled = True
            self.MainFrame.petacInvertAr.Enabled = True
            self.MainFrame.petacInvertDec.Enabled = True
            self.MainFrame.petacValue.Enabled = True
            self.MainFrame.petacMinCorr.Enabled = True
            self.MainFrame.petacMountLowSpeed.Enabled = True
            self.MainFrame.petacMaxDithering.Enabled = True
            self.MainFrame.petacDithStep.Enabled = True
            self.MainFrame.crosshair.SetValue(False)
            self.petacFlag = False
            self.MainFrame.fwhmCalc.Label = "FWHM measure"
            self.MainFrame.guideInstr.Value = self.testo[13]
            self.MainFrame.alignInstr.Value = self.testo[0]
            self.MainFrame.petacInstr.Value = self.testo[36]
            self.CtrlEnable(self.hideVampire)
            self.ResetCorrection(None)
            self.deltaX, self.deltaY = 0,0
            self.graph1List = [(0.0,0.0)]
            self.graph2List = [(0.0,0.0)]
            self.graph3List = [(0.0,0.0)]
            self.graph4List = [(0.0,0.0)]
            
        else: print "error - status " + status + " not valid"
        self.SaveTemp()

#---- frames management
    def OnCloseMainWindow(self, evt):
        #what to do when you close main window
        self.ValuesToConfig()
        if self.Configuration.IsConfigurationChanged():
            dial = wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[27], 'Question',
               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            ret = dial.ShowModal()
            if ret == wx.ID_YES:
                self.Configuration.SaveConfiguration()
        self.SetStatus("idle")
        self.filelog.close()
        self.timerShowHideVampire.Destroy()
        self.drawClock.Destroy()
        self.calcClock.Destroy()
        self.zoomClock.Destroy()
        self.Processes.Close()
        self.MainFrame.Destroy()

    def OnVampireFrame(self,evt):
        #what to do when you open vampire window
        self.SetStatus("waiting_for_vampire_victim")

    def HideVampire(self):
        #hide vampire window
        self.hideVampire = True
        self.CtrlEnable(True)
        self.timerShowHideVampire.Start(50)
        self.MainFrame.VampireFrame.vampirePanel.SetFocusIgnoringChildren()

    def ShowVampire(self,evt):
        #show vampire window
        self.hideVampire = False
        self.MainFrame.VampireFrame.Show()
        self.MainFrame.VampireFrame.windowconfirm.Enable(True)
        self.MainFrame.VampireFrame.windowconfirm.Show()
        self.timerShowHideVampire.Start(50)
        self.MainFrame.VampireFrame.vampirePanel.SetFocusIgnoringChildren()

    def SizeObserver(self,evt):
        #update size and position of vampire window
        self.vampirePosX, self.vampirePosY = self.MainFrame.VampireFrame.GetPosition()
        self.vampireSizeX,self.vampireSizeY = self.MainFrame.VampireFrame.GetSize()
        self.vampireSizeY += self.WINDOWBAR_H
        self.zoomSizeX,self.zoomSizeY = self.MainFrame.ZoomFrame.GetSize()
        self.errorGraphX = self.vampirePosX+40
        self.errorGraphY = self.vampirePosY+40

    def AlphaCycle(self,evt):
        #set transparency of vampire window
        if (self.hideVampire):
            self.alphaAmount=self.alphaAmount-10 #make the vampire frame transparent
            if (self.alphaAmount>0):
                self.MainFrame.VampireFrame.SetTransparent(self.alphaAmount)
            else:
                self.alphaAmount = 1 #transparent final value
                self.MainFrame.VampireFrame.SetTransparent(self.alphaAmount)
                self.MainFrame.VampireFrame.windowconfirm.Enable(False)
                #self.MainFrame.VampireFrame.windowconfirm.Hide()
                self.timerShowHideVampire.Stop()
                self.MainFrame.VampireFrame.vampirePanel.SetFocusIgnoringChildren()
        else:
            self.alphaAmount=self.alphaAmount+10 #make the vampire frame visible
            if (self.alphaAmount<200):
                self.MainFrame.VampireFrame.SetTransparent(self.alphaAmount)
            else:
                self.timerShowHideVampire.Stop()
                self.alphaAmount = 200 #visible final value
                self.MainFrame.VampireFrame.SetTransparent(self.alphaAmount)
                x,y = self.MainFrame.VampireFrame.GetPosition()
                self.MainFrame.VampireFrame.SetPosition((x+10, y+10))
                self.MainFrame.VampireFrame.SetSize((self.vampireSizeX-20, self.vampireSizeY-20))

    def KeyDownVampire(self,evt):
        #manage keypressed (keydown event) while the focus is on vampire windows
        keycode = evt.GetKeyCode()
        if self.controlMode != "none" and self.lastMountCommand == "quit":
            self.lastMountCommand = "move"
            if keycode == wx.WXK_UP:
                self.MainFrame.mountUpPic.Show(True)
                self.MainFrame.mountDownPic.Show(False)
                self.MainFrame.mountLeftPic.Show(False)
                self.MainFrame.mountRightPic.Show(False)
                self.MainFrame.mountStopPic.Show(False)
                self.MainFrame.mountUpPic1.Show(True)
                self.MainFrame.mountDownPic1.Show(False)
                self.MainFrame.mountLeftPic1.Show(False)
                self.MainFrame.mountRightPic1.Show(False)
                self.MainFrame.mountStopPic1.Show(False)
                self.Processes.SendMountCommand("n", self.MainFrame.invertDec.Value)
            elif keycode == wx.WXK_DOWN:
                self.MainFrame.mountUpPic.Show(False)
                self.MainFrame.mountDownPic.Show(True)
                self.MainFrame.mountLeftPic.Show(False)
                self.MainFrame.mountRightPic.Show(False)
                self.MainFrame.mountStopPic.Show(False)
                self.MainFrame.mountUpPic1.Show(False)
                self.MainFrame.mountDownPic1.Show(True)
                self.MainFrame.mountLeftPic1.Show(False)
                self.MainFrame.mountRightPic1.Show(False)
                self.MainFrame.mountStopPic1.Show(False)
                self.Processes.SendMountCommand("s", self.MainFrame.invertDec.Value)
            elif keycode == wx.WXK_LEFT:
                self.MainFrame.mountUpPic.Show(False)
                self.MainFrame.mountDownPic.Show(False)
                self.MainFrame.mountLeftPic.Show(True)
                self.MainFrame.mountRightPic.Show(False)
                self.MainFrame.mountStopPic.Show(False)
                self.MainFrame.mountUpPic1.Show(False)
                self.MainFrame.mountDownPic1.Show(False)
                self.MainFrame.mountLeftPic1.Show(True)
                self.MainFrame.mountRightPic1.Show(False)
                self.MainFrame.mountStopPic1.Show(False)
                self.Processes.SendMountCommand("w", self.MainFrame.invertAr.Value)
            elif keycode == wx.WXK_RIGHT:
                self.MainFrame.mountUpPic.Show(False)
                self.MainFrame.mountDownPic.Show(False)
                self.MainFrame.mountLeftPic.Show(False)
                self.MainFrame.mountRightPic.Show(True)
                self.MainFrame.mountStopPic.Show(False)
                self.MainFrame.mountUpPic1.Show(False)
                self.MainFrame.mountDownPic1.Show(False)
                self.MainFrame.mountLeftPic1.Show(False)
                self.MainFrame.mountRightPic1.Show(True)
                self.MainFrame.mountStopPic1.Show(False)
                self.Processes.SendMountCommand("e", self.MainFrame.invertAr.Value)
            elif keycode == wx.WXK_PAGEDOWN:
                self.collimatorSize -= 1
                self.crosshairList = self.Processes.SetCrosshair(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, self.crosshairXs, self.crosshairYs, self.collimatorSize)
            elif keycode == wx.WXK_PAGEUP:
                self.collimatorSize += 1  
                self.crosshairList = self.Processes.SetCrosshair(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, self.crosshairXs, self.crosshairYs, self.collimatorSize)  
            elif keycode == wx.WXK_SPACE:
                self.crosshairColorCode += 1
                if self.crosshairColorCode > 7: self.crosshairColorCode = 0
                print self.crosshairColorCode
            else:
                self.lastMountCommand = "quit"

    def KeyUpVampire(self,evt):
        #manage keypressed (keyup event) while the focus is on vampire windows
        if self.controlMode != "none":
            self.MainFrame.mountUpPic.Show(False)
            self.MainFrame.mountDownPic.Show(False)
            self.MainFrame.mountLeftPic.Show(False)
            self.MainFrame.mountRightPic.Show(False)
            self.MainFrame.mountStopPic.Show(True)
            self.MainFrame.mountUpPic1.Show(False)
            self.MainFrame.mountDownPic1.Show(False)
            self.MainFrame.mountLeftPic1.Show(False)
            self.MainFrame.mountRightPic1.Show(False)
            self.MainFrame.mountStopPic1.Show(True)
            self.lastMountCommand = "quit"
            self.Processes.SendMountCommand("q", False)

    def LeftClickOnVampire(self,evt):
        #manage left mouse click on the vampire windows
        print "left click"
        xs, ys = wx.Window.ClientToScreenXY(self.MainFrame.VampireFrame, evt.X, evt.Y)
        self.MainFrame.VampireFrame.SetFocus()
        print xs, ys
        if self.status == "waiting_for_vampire_victim":
            self.actualX, self.actualY =  xs, ys
            self.MainFrame.VampireFrame.Hide()
            self.calcClock.Start(1000)
        elif (xs>self.CIRCLE_DIAMETER+self.vampirePosX and ys>self.CIRCLE_DIAMETER+self.vampirePosY and
            xs<self.vampirePosX+self.vampireSizeX-self.CIRCLE_DIAMETER and ys<self.vampirePosY+self.vampireSizeY-self.CIRCLE_DIAMETER): #if it's not too close to borders
            self.actualX, self.actualY =  xs, ys
            self.timeFromClick.Start() #reset stopwatch
            if self.status == "camera_orientation_begin": self.SetStatus("camera_orientation_first_star")
            elif self.status == "camera_orientation_first_star_acq": self.SetStatus("camera_orientation_second_star_acq")
            elif self.status == "alignment_star_waiting": self.SetStatus("alignment_star_tracking")
            elif self.status == "alignment_calc_ready": self.SetStatus("alignment_star_tracking")
            elif self.status == "fwhm_wait": self.SetStatus("fwhm_calc")
            elif self.status == "fwhm_calc": self.SetStatus("fwhm_calc")
            elif self.status == "guide_star_waiting": self.SetStatus("guiding")
            elif self.status == "guiding": self.SetStatus("guiding") #reset guide if click again
            elif self.status == "petac_star_waiting": self.SetStatus("petac_operating")
            elif self.status == "guide_calibration_waiting": self.SetStatus("guide_calibrating")

    def RightClickOnVampire(self,evt):
        #manage right mouse click on the vampire windows
        print "right click"
        xs, ys = wx.Window.ClientToScreenXY(self.MainFrame.VampireFrame, evt.X, evt.Y)
        if (xs>self.CIRCLE_DIAMETER+self.vampirePosX and ys>self.CIRCLE_DIAMETER+self.vampirePosY and
            xs<self.vampirePosX+self.vampireSizeX-self.CIRCLE_DIAMETER and ys<self.vampirePosY+self.vampireSizeY-self.CIRCLE_DIAMETER and
            self.hideVampire):
            self.crosshairXs, self.crosshairYs= xs, ys
            self.crosshairList = self.Processes.SetCrosshair(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, self.crosshairXs, self.crosshairYs, self.collimatorSize)

    def MouseMovingOnVampire(self,evt):
        #manage mouse moving event on the vampire windows
        xs, ys = wx.GetMousePosition()
        colore = self.dcScreen.GetPixel(xs,ys)
        if (xs>self.CIRCLE_DIAMETER+self.vampirePosX and ys>self.CIRCLE_DIAMETER+self.vampirePosY and
            xs<self.vampirePosX+self.vampireSizeX-self.CIRCLE_DIAMETER and ys<self.vampirePosY+self.vampireSizeY-self.CIRCLE_DIAMETER and
            self.hideVampire):
            self.xs, self.ys = xs, ys
            self.MainFrame.pixelLabel.Label =  "R:"+str(colore[0])+" G:"+str(colore[1])+" B:"+str(colore[2])
            self.MainFrame.ZoomFrame.Title = "R:"+str(colore[0])+" G:"+str(colore[1])+" B:"+str(colore[2])

    def OnAboutFrame(self,evt):
        #open about window
        self.MainFrame.AboutFrame.Show()

    def OnCloseAboutWindow(self, evt):
        #what to do when you close the about window
        evt.Veto()
        self.MainFrame.AboutFrame.Hide()
        
    def OnGraphFrame(self, evt, numpoints=0 ):
        #open graph window
        self.Processes.GenericGraphInit(self.MainFrame.GraphFrame.graphPanel)
        self.MainFrame.GraphFrame.Show()
        self.GenericGraphUpdate(numpoints)
    
    def SizeGraphFrame(self,evt):
        #what to do when you resize graph window
        self.Processes.GenericGraphInit(self.MainFrame.GraphFrame.graphPanel)
        
    def OnCloseGraphWindow(self, evt):
        #what to do when you close graph window
        evt.Veto()
        self.MainFrame.GraphFrame.Hide()

    def OnZoomFrame(self,evt):
        #what to do when you open zoom window
        if self.hideVampire:
            self.MainFrame.ZoomFrame.Show()
            self.zoomClock.Start(200)

    def OnCloseZoomWindow(self, evt):
        #what to do when you close zoom window
        evt.Veto()
        self.zoomClock.Stop()
        self.MainFrame.ZoomFrame.Hide()

    def TimerToPaint(self, evt):
        # transforms a timer event in a paint event in order to use PaintDC on Windows
        self.MainFrame.ZoomFrame.Refresh()
        self.MainFrame.ZoomFrame.Update()

    def ZoomRefresh(self, evt):
        #refresh zoom window
        if self.hideVampire:
            self.Processes.ZoomRefresh(self.MainFrame.ZoomFrame, self.zoomSizeX, self.zoomSizeY, self.xs, self.ys)

#---- controls - main frame
    def ChangedTab(self, evt):
        #manage changetab event
        if self.MainFrame.schede.GetSelection() == 2:
            self.GuideChangeCommonControl(None)
        if self.MainFrame.schede.GetSelection() == 3:
            self.PetacChangeCommonControl(None)
        if (self.status<>"waiting_for_vampire_victim") and (self.status<>"waiting_for_vampire_victim_confirm"): self.SetStatus("idle")

    def CtrlEnable(self, value):
        #enable main window controls
        if self.controlMode != "none": self.MainFrame.guideCalibrationOnOff.Enabled = value
        if self.controlMode != "none": self.MainFrame.petacguideCalibrationOnOff.Enabled = value
        if self.controlMode != "none": self.MainFrame.guideOnOff.Enabled = value
        if self.controlMode != "none": self.MainFrame.petacOnOff.Enabled = value
        if self.controlMode != "none": self.MainFrame.petacCalOnOff.Enabled = value
        self.MainFrame.alignOrientation.Enabled = value
        self.MainFrame.alignCorrection.Enabled = value
        self.MainFrame.crosshair.Enabled = value
        self.MainFrame.fwhmCalc.Enabled = value
        self.MainFrame.zoom2x.Enabled = value
        self.MainFrame.takePicture.Enabled = value

    def LanguageSelect(self,evt):
        #manage language change event
        success = self.Configuration.LoadLanguage(self.MainFrame.languagecombo.Value)
        if success:
            self.testo = tuple(self.Configuration.TextLines())
            print "language ", self.MainFrame.languagecombo.Value, " loaded"
        else:
            dial=wx.MessageDialog(self.MainFrame, "Language file not valid - no text available", 'Info', wx.ICON_ERROR | wx.OK)
            dial.SetIcon(self.GiGiWxIcon)
            dial.ShowModal()
            #empty testo tuple bigger than ever possible
            self.testo = ("no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text",
                         "no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text",
                         "no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text",
                         "no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text",
                         "no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text","no-text")

    def CameraOrientation(self,evt):
        #start camera orientation procedure
        self.SetStatus("camera_orientation_begin")

    def PEwarning(self,evt):
        #show text about PE saving
        if self.MainFrame.savePE.Value:
            dial = wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[33], 'Info', wx.ICON_INFORMATION | wx.OK)
            dial.SetIcon(self.GiGiWxIcon)
            dial.ShowModal()

    def AlignCorrection(self,evt):
        #manage "correction" button event
        self.MainFrame.VampireFrame.Refresh()
        if self.status == "alignment_calc_ready":
            if self.MainFrame.savePE.Value:
                c = ctime()
                c = c.replace(" ","_")
                c = c.replace(":","-")
                filename ="../stored_data/PE_" + c + ".txt"
                self.Processes.SaveList(filename,self.graph1List)
            self.correzione, self.verso = self.Processes.CalcCorrection (self.angolo, self.xo, self.yo, self.xf, self.yf, self.MainFrame.VampireFrame, self.testo[10])
            # show text about making correction
            self.alignCorrList, self.alignCorrListInv, numCorr, self.xf, self.yf, self.xo, self.yo = self.Processes.DrawCorrectionCalc (self.angolo, self.correzione, self.verso,
                                                                             self.vampirePosX, self.vampirePosY, self.vampireSizeX,
                                                                             self.vampireSizeY, self.xf, self.yf)
            if self.starPosition == "s":
                self.MainFrame.alignInstr.Value = self.testo[6]
            else:
                self.MainFrame.alignInstr.Value = self.testo[7]
            if numCorr > 1:
                self.MainFrame.alignInstr.Value += " " + self.testo[8] + " " + str(int(numCorr)) + " " + self.testo[9]
            self.MainFrame.alignInstr.Value += " " + self.testo[11]
            self.SetStatus("alignment_cam_calibrated")
        # undo alignment
        elif (self.status == "alignment_star_waiting" or
            self.status == "alignment_star_tracking"):
            self.SetStatus("alignment_cam_calibrated")
        # start alignment
        elif self.status == "alignment_cam_calibrated":
            self.SetStatus("alignment_star_waiting")

        elif self.status == "idle":
            self.SetStatus("alignment_star_waiting")

    def ResetCorrection(self,evt):
        #manage "reset correction" button event
        if self.starPosition == "s":
            self.Processes.SetFattCorr(1)
        else:
            self.Processes.SetFattCorr(0.5)
        #because, for elevation correction, a low declination star is usually chosen
        self.Processes.ResetUltimaCorrezione()

    def GuideChangeCommonControl(self,evt):
        #conform guide tab settings to petac tab settings
        self.MainFrame.invertAr.Value = self.MainFrame.petacInvertAr.Value
        self.MainFrame.invertDec.Value = self.MainFrame.petacInvertDec.Value
        self.MainFrame.arGuideValue.Value = self.MainFrame.petacArGuideValue.Value
        self.MainFrame.decGuideValue.Value = self.MainFrame.petacDecGuideValue.Value
        self.MainFrame.maxDithering.Value = self.MainFrame.petacMaxDithering.Value
        self.MainFrame.dithStep.Value = self.MainFrame.petacDithStep.Value

    def PetacChangeCommonControl(self,evt):
        #conform petac tab settings to guide tab settings
        self.MainFrame.petacInvertAr.Value = self.MainFrame.invertAr.Value
        self.MainFrame.petacInvertDec.Value = self.MainFrame.invertDec.Value
        self.MainFrame.petacArGuideValue.Value = self.MainFrame.arGuideValue.Value
        self.MainFrame.petacDecGuideValue.Value = self.MainFrame.decGuideValue.Value
        self.MainFrame.petacMaxDithering.Value = self.MainFrame.maxDithering.Value
        self.MainFrame.petacDithStep.Value = self.MainFrame.dithStep.Value

    def SetCalType(self,evt,which):
        #manage the change of correction type
        if which=="s":
            self.MainFrame.alignCorrection.SetLabel(label="Azimuth Correction")
        elif which=="e":
            self.MainFrame.alignCorrection.SetLabel(label="Elevation Correction")
        elif which=="w":
            self.MainFrame.alignCorrection.SetLabel(label="Elevation Correction")
        self.starPosition = which
        # reset alignment vars
        self.ResetCorrection(None)

    def MountPortSelect(self,evt):
        #manage the change of mount port
        if self.MainFrame.mountportcombo.Value == "none":
            self.MainFrame.guideCalibrationOnOff.Enabled = False
            self.MainFrame.petacguideCalibrationOnOff.Enabled = False
            self.MainFrame.guideOnOff.Enabled = False
            self.MainFrame.petacOnOff.Enabled = False
            self.controlMode = "none"

        elif self.MainFrame.mountportcombo.Value == "audio":
            try:
                self.Processes.InitAudio()
                self.MainFrame.guideCalibrationOnOff.Enabled = True
                self.MainFrame.petacguideCalibrationOnOff.Enabled = True
                self.MainFrame.guideOnOff.Enabled = True
                self.MainFrame.petacOnOff.Enabled = True
                self.controlMode = "audio"
            except:
                print "problem with audio configuration"
                self.MainFrame.mountportcombo.Value = "none"
        
        elif self.MainFrame.mountportcombo.Value[0:6] == "serial":
            try:
                self.Processes.CloseSerial()
                self.Processes.InitSerial(self.MainFrame.mountportcombo.Value[6:])
                self.MainFrame.guideCalibrationOnOff.Enabled = True
                self.MainFrame.petacguideCalibrationOnOff.Enabled = True
                self.MainFrame.guideOnOff.Enabled = True
                self.MainFrame.petacOnOff.Enabled = True
                self.controlMode = "serial"
            except:
                try:
                    stringa = "/dev/ttyUSB"+strip(str(self.MainFrame.mountportcombo.Value[6:]))
                    self.Processes.InitSerial(stringa)
                    self.MainFrame.guideCalibrationOnOff.Enabled = True
                    self.MainFrame.petacguideCalibrationOnOff.Enabled = True
                    self.MainFrame.guideOnOff.Enabled = True
                    self.MainFrame.petacOnOff.Enabled = True
                    self.controlMode = "serial"
                except:
                    dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[17], 'Info', wx.ICON_ERROR | wx.OK)
                    dial.ShowModal()
                    self.MainFrame.mountportcombo.Value = "none"
        self.Processes.SetControlMode(self.controlMode)
        self.Processes.SendMountCommand("1", False) #set speed to "center speed" (mid)
        self.lastMountCommand = "quit"              
            
    def CamPortSelect(self,evt):
        #manage the change of camera control port (long exposure)
        if self.MainFrame.camportcombo.Value == "none":
            self.camControlMode = "none"

        elif self.MainFrame.camportcombo.Value == "audio":
            try:
                self.Processes.InitAudio()
                self.camControlMode = "audio"
            except:
                print "problem with audio configuration"
                self.MainFrame.camportcombo.Value = "none"
        
        elif self.MainFrame.camportcombo.Value[0:6] == "serial":
            try:
                self.Processes.CloseSerial()
                self.Processes.InitSerial(self.MainFrame.camportcombo.Value[6:])
                self.camControlMode = "serial"
            except:
                try:
                    stringa = "/dev/ttyUSB"+strip(str(self.MainFrame.camportcombo.Value[6:]))
                    self.Processes.InitSerial(stringa)
                    self.camControlMode = "serial"
                except:
                    dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[17], 'Info', wx.ICON_ERROR | wx.OK)
                    dial.ShowModal()
                    self.MainFrame.camportcombo.Value = "none"              

    
    def SetMountSpeed(self,evt):
        #manage the change of mount speed
        self.Processes.SendMountCommand(str(evt.GetInt()), False)
        
    def SetImagesDir(self,evt):
        #manage the change of image saving directory
        self.imagesPath = self.Processes.DirChoose(self.imagesPath, self.testo[39])
        print self.imagesPath

    def GuideCalibrationRoutineStartStop(self,evt):
        #manage start/stop of full automatic calibration routine
        if self.hideVampire:
            if self.status == "guide_calibrating" or self.status == "guide_calibration_waiting":
                self.SetStatus("idle")
                self.Processes.SendMountCommand("q", False)
                self.MainFrame.guideInstr.Value = self.testo[23]
            else:
                self.SetStatus("guide_calibration_waiting")

    def GuideStartStop(self,evt):
        #manage guiding start/stop
        if self.hideVampire:
            if self.status == "guiding" or self.status == "guide_star_waiting":
                self.SetStatus("idle")
                self.Processes.SaveList("../stored_data/error_AR.txt",self.graph1List)
                self.Processes.SaveList("../stored_data/error_DEC.txt",self.graph2List)
                self.Processes.SaveList("../stored_data/correction_AR.txt",self.graph3List)
                self.Processes.SaveList("../stored_data/correction_DEC.txt",self.graph4List)          
            else:
                self.SaveTemp()
                self.SetStatus("guide_star_waiting")
                
    def GenericGraphUpdate(self, numpoints, desc1="", desc2="", desc3="", desc4=""):
        #update the graph of desc1, desc2, etc with numpoints points. No desc => no graph; if numpoints=0,
        #read from numpoints textarea in graph windows
        if numpoints>1:
            self.MainFrame.GraphFrame.numPoints.SetValue(str(numpoints))
        else:
            numpoints = min(int(self.Processes.ExtractInt(self.MainFrame.GraphFrame.numPoints.Value)),max(len(self.graph1List)-1, len(self.graph1List)-1))
            numpoints = max(numpoints,1)
        descriptions = [desc1, desc2, desc3, desc4]
        if self.MainFrame.GraphFrame.showGraph1.GetValue():
            data1 = self.graph1List[-numpoints:]
        else: 
            data1 = []
        if self.MainFrame.GraphFrame.showGraph2.GetValue():
            data2 = self.graph2List[-numpoints:]
        else: 
            data2 = []
        if self.MainFrame.GraphFrame.showGraph3.GetValue():
            data3 = self.graph3List[-numpoints:]
        else: 
            data3 = []
        if self.MainFrame.GraphFrame.showGraph4.GetValue():
            data4 = self.graph4List[-numpoints:]
        else: 
            data4 = []
        self.Processes.GenericGraphDraw(self.MainFrame.GraphFrame, data1, data2, data3, data4, descriptions )

    def PetacCalStartStop(self,evt):
        #manage PETAC calibration routine start/stop
        if self.hideVampire:
            if self.status == "petac_calibration":
                self.SetStatus("idle")
            else:
                self.SetStatus("petac_calibration")

    def PetacStartStop(self,evt):
        #manage PETAC routine start/stop
        if self.hideVampire:
            if self.status == "petac_operating" or self.status == "petac_star_waiting":
                self.SetStatus("idle")
            else:
                self.SaveTemp()
                self.SetStatus("petac_star_waiting")

    def MouseMovingOnPetacButton(self,evt):
        #manage mouse moving event on PETAC control button
        self.petacFlag = not(self.petacFlag) #take one movement over two, because one is fake since it comes from WarpPointer function
        if (self.timeFromClick.Time()//1000-self.MIN_CORR_TIME >= 0) and (
           self.status == "petac_calibration" or self.status == "petac_operating") and (self.petacFlag):
            self.movementCounter +=1
            self.lastMoveTime = self.movementTime
            self.movementTime = self.timeFromClick.Time()            
            if (self.status == "petac_calibration"):
                self.oldPetacVal = self.petacVal
                if self.movementCounter != 0: self.petacVal = (self.movementTime-self.MIN_CORR_TIME*1000)//self.movementCounter
                self.MainFrame.petacValue.Value = str(round(self.petacVal))
                if self.oldPetacVal == 0: self.oldPetacVal = 1 #protects from division by zero
                var = float(self.petacVal-self.oldPetacVal)/float(self.oldPetacVal)
                print "petac_calibration: last movement at ",(self.movementTime), "; movement no: ", self.movementCounter,"; var: ", var
                self.MainFrame.petacInstr.Value = self.testo[34] + "\n" + "Var =" + str(round(var*100,1)) + "%"        
                self.MainFrame.petacTab.WarpPointer(self.PETAC_CAL_BUTTON_CENTER_X, self.PETAC_CAL_BUTTON_CENTER_Y) #center the mouse in the button
                if abs(var) < 0.05 and self.timeFromClick.Time()//1000 > self.MIN_CALIBRATION_TIME:
                    self.MainFrame.petacCalOnOff.SetValue(False)
                    self.PetacCalStartStop(None)
                    dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[35], 'Info', wx.OK | wx.ICON_INFORMATION)
                    dial.ShowModal()
            else:
                #check if picture is changed in order to apply guide and dithering (a startrack will eventually show a difference)
                latestX, latestY = self.actualX, self.actualY
                self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY)
                #apply pet-ac correction if needed
                if self.lastMoveTime > 0 and self.petacVal > 0:
                    print "movement interval: ", self.movementTime-self.lastMoveTime
                    self.Processes.SendPetacCorrection(self.movementTime-self.lastMoveTime, self.petacVal, float(self.MainFrame.petacMountLowSpeed.Value))
                self.MainFrame.petacTab.WarpPointer(self.PETAC_BUTTON_CENTER_X, self.PETAC_BUTTON_CENTER_Y) #center the mouse in the button
            
    def SavePicture(self,evt):
        #save a picture from vampire window
        if self.hideVampire or self.MainFrame.picFullScreen.Value:
            dial = wx.MessageDialog(self.MainFrame, self.testo[31], 'Question', wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            ret = dial.ShowModal()
            if ret == wx.ID_YES:
                self.picTime = ctime()
                self.picTime = self.picTime.replace(" ","_")
                self.picTime = self.picTime.replace(":","-")
                self.picTotal = self.Processes.ExtractInt(self.MainFrame.pictureNo.Value)
                self.picSaveClock.Start(50+1000*self.Processes.ExtractInt(self.MainFrame.pictureInt.Value))              
    
    def PicFullScreen(self,evt):
        #manage the possibility of taking a full screenshot
        self.MainFrame.takePicture.Enabled = self.MainFrame.picFullScreen.Value or self.hideVampire
        
    def FieldUpdate(self,evt):
        #updates field calculator output
        try:
            width=float(self.MainFrame.ccdW.GetValue())
        except:
            width=0
        try:
            height=float(self.MainFrame.ccdH.GetValue())
        except:
            height=0
        try:
            focal=float(self.MainFrame.focal.GetValue())
        except:
            focal=0
        self.MainFrame.field.SetValue(self.Processes.FieldUpdate(width,height,focal))
        
    def ColorFromCode(self, code):
        #returns color value for crosshair
        if code == 0: color = "#000000"
        if code == 1: color = "#FF0000"
        if code == 2: color = "#00FF00"
        if code == 3: color = "#0000FF"
        if code == 4: color = "#FFAAAA"
        if code == 5: color = "#AAFFAA"
        if code == 6: color = "#AAAAFF"
        if code == 7: color = "#FFFFFF"
        return color

    def FwhmStart(self, evt):
        #manage the FWHM calculation start
        if self.MainFrame.fwhmCalc.Value:
            dial=wx.MessageDialog(self.MainFrame.VampireFrame, self.testo[30], 'Info', wx.OK | wx.ICON_INFORMATION)
            dial.ShowModal()
            self.SetStatus("fwhm_wait")
        else:
            self.SetStatus("idle")
    
    def CrosshairAct(self, evt):
        #give crosshai use instructions
        if self.MainFrame.crosshair.Value:
            dial=wx.MessageDialog(self.MainFrame, self.testo[40], 'Info', wx.OK | wx.ICON_INFORMATION)
            dial.ShowModal()       

#---- controls - vampire frame
    def WindowConfirm(self,evt):
        #manage the confirmation of vampire window size and position
        self.HideVampire()
        self.vampirePosX, self.vampirePosY = self.MainFrame.VampireFrame.GetPosition()
        self.crosshairXs,self.crosshairYs = wx.Window.ClientToScreenXY(self.MainFrame.VampireFrame, self.vampireSizeX//2, self.vampireSizeY//2)
        self.crosshairList = self.Processes.SetCrosshair(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, self.crosshairXs, self.crosshairYs, self.collimatorSize)
        self.SetStatus("idle")

#---- controls - about frame
    def OnNameClick(self, event):
        #manage left click on "name" textarea
        self.MainFrame.AboutFrame.name.SetValue('')
        event.Skip()

    def OnCityClick(self, event):
        #manage left click on "city" textarea
        self.MainFrame.AboutFrame.city.SetValue('')
        event.Skip()

    def OnCommentClick(self, evt):
        #manage left click on "comment" textarea
        self.MainFrame.AboutFrame.comment.SetValue('')
        evt.Skip()

    def SendId(self,evt):
        #manage confirmation request for feedback sending
        dial = wx.MessageDialog(self.MainFrame.AboutFrame, self.testo[29], 'Question',
               wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        ret = dial.ShowModal()
        if ret == wx.ID_YES:
            idPC = self.Processes.CalcId()
            webbrowser.open_new_tab("http://andreaconsole.altervista.org/index.php?webpage=feedbackwx&codice="+idPC+
                                    "&name="+self.MainFrame.AboutFrame.name.Value+
                                    "&city="+self.MainFrame.AboutFrame.city.Value+
                                    "&comment="+self.MainFrame.AboutFrame.comment.Value)
            self.MainFrame.AboutFrame.Hide()
    
    def SendHelpReq(self,evt):
        #manage help requests
        idPC = self.Processes.CalcId()
        webbrowser.open_new_tab("http://andreaconsole.altervista.org/index.php?webpage=gigiwxcapture&codice="+idPC)
        self.MainFrame.AboutFrame.Hide()

#---- clocks and other methods
    def CalcClock(self,evt):
        #manage calculation clock event
        if self.hideVampire:
            #action depending on status
            if self.starTracking:
                if self.MainFrame.hiSens.Value and self.status == "guiding":
                    iter = 0 #when iter = 0, startrack bufferize and add image data so to improve signal to noise ratio
                else:
                    iter = 1
                self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, iter)
                
            if self.status == "fwhm_calc":
                self.MainFrame.fwhmCalc.Label = "FWHM = "+str(round(self.FWHM,2))
                if self.timeFromClick.Time()//1000 >5:
                    self.graph1List.append((self.timeFromClick.Time()//1000-5, round(self.FWHM,1)))
                    self.GenericGraphUpdate(0, "FWHM") #graph for fwhm

            elif self.status == "alignment_star_tracking" and self.timeFromClick.Time()//1000 >= self.MIN_CORR_TIME:
                self.xo, self.yo = self.actualX, self.actualY
                self.Processes.ResetCorrezione()
                self.xf, self.yf = self.actualX, self.actualY
                self.graph1List = [(0,0)]
                self.MainFrame.alignCorrection.Label = "Calc Correction"
                self.SetStatus ("alignment_calc_ready")

            elif self.status == "alignment_calc_ready" and imageSignature != self.storedImageSignature:
                correctionElapsedTime = self.timeFromClick.Time()//1000
                self.storedImageSignature = imageSignature
                self.xf, self.yf = self.actualX, self.actualY
                semicorr, deviazione, fattCorr, arDiff = self.Processes.UpdateCorrection(self.xo,self.yo,self.xf,self.yf, self.angolo,
                                                                          correctionElapsedTime - self.MIN_CORR_TIME)
                self.MainFrame.alignInstr.Value = ("Elapsed Time=" + str(correctionElapsedTime - self.MIN_CORR_TIME) +
                                                   ";\nCorrection=" + str(int(semicorr * 86164 * fattCorr / 6.28)) +
                                                   ";\nDelta=" + str(round(deviazione)) + ";\nLatest Corr. Weight=" +
                                                    str(round(fattCorr,4)) + "\n" + self.testo[5])
                self.graph1List.append((correctionElapsedTime, int(semicorr * 86164 * fattCorr / 6.28)))
                self.GenericGraphUpdate(0, "Correction") #graph for fwhm

                if self.MainFrame.savePE.Value:
                    #append arDiff values to PE dictionary (saved on procedure exit)
                    self.graph1List.append((timeFromLastGuide.Time()//1000 - self.MIN_CORR_TIME, round(arDiff, 1)))
                    #print self.graph1List[-1]

            elif self.status == "guiding":
                #check if an image has been added (dithinterval will be always > 0)
                if (self.dithInterval != 0):
                    imageAdded = False
                    if (self.Processes.CountFiles(self.imagesPath) >= (self.ditherCount + self.dithInterval)):
                        self.ditherCount = self.Processes.CountFiles(self.imagesPath)
                        self.Processes.DitheringUpdate()
                        imageAdded = True
                        print "new "+str(self.dithInterval) + " image/s saved - dithering applied"
                #check if is time to guide
                if (self.timeFromLastGuide.Time()//1000 > self.guideIntervalSec > 0 and (
                    self.MainFrame.hiSens.Value or imageSignature != self.storedImageSignature)): 
                    self.storedImageSignature = imageSignature
                    self.actualX, self.actualY, self.FWHM, imageSignature = self.Processes.StarTrack(self.actualX, self.actualY, self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, 20)
                    self.Processes.SetCamLE(False, self.camControlMode) #add here some code for image storing!!!
                    self.Processes.SetCamLE(True, self.camControlMode)
                    guideCenterX, guideCenterY = self.Processes.DitheringAdd(self.guideCenterX, self.guideCenterY)
                    self.deltaX, self.deltaY = self.actualX-guideCenterX, self.actualY-guideCenterY
                    deltaAR, deltaDEC = self.Processes.CoordConvert(self.deltaX, self.deltaY, self.angolo)
                    #apply guide                
                    thread.start_new_thread(self.Processes.GuideRoutine,(deltaAR, deltaDEC))
                    #--- guiding statS
                    if self.meanDECdrift == 0 and self.meanARdrift == 0:
                        self.meanARdrift,self.meanDECdrift = deltaAR*deltaAR, deltaDEC*deltaDEC
                    else:
                        self.meanARdrift = 0.9 * self.meanARdrift + 0.1 * deltaAR*deltaAR
                        self.meanDECdrift = 0.9 * self.meanDECdrift + 0.1 * deltaDEC*deltaDEC
                    self.MainFrame.guideInstr.Value = self.testo[16] + "\n latest AR error = " + str(round(deltaAR,2)) + ( 
                    "\n latest DEC error = " + str(round(deltaDEC,2)) + "\n Mean AR error = " + str(round(sqrt(self.meanARdrift),2))) + ( 
                    "\n Mean DEC error = " + str(round(sqrt(self.meanDECdrift),2))  + "\n FWHM = " + str(round(self.FWHM,2)
                    ) + "\n Dith = (" + str(round(self.Processes.dithIncrX,1)) + ", " + str(round(self.Processes.dithIncrY,1)) + ")"+ "\n Angle = " + str(round(57.3 * self.angolo)
                    ) + "\n Last corr in ms (AR - DEC) = (" + str(round(self.Processes.GuideLastARcorr(),1)) + ", " + str(round(self.Processes.GuideLastDECcorr(),1)) + ")")
                    ElapsedTime = float(round(self.timeFromClick.Time()/1000,1))
                    self.graph1List.append((ElapsedTime, deltaAR))
                    self.graph2List.append((ElapsedTime, deltaDEC))
                    self.graph3List.append((ElapsedTime, round(float(self.Processes.GuideLastARcorr())/(float(self.MainFrame.arGuideValue.Value)+1),2)))
                    self.graph4List.append((ElapsedTime, round(float(self.Processes.GuideLastDECcorr())/(float(self.MainFrame.decGuideValue.Value)+1),2)))
                    #---save image in testmode
                    if self.testMode:
                        self.testModeCounter += 1
                        if (self.testModeCounter%5 == 0): #every five guiding actions, save file
                            filename = "../savedBMP/testmode_"+str(self.testModeCounter)
                            self.Processes.SavePicture(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, filename)
                            print "saved test image"
                    #------------------------------
                    self.GenericGraphUpdate(0, "AR err", "DEC err", "AR corr", "DEC corr")
                    self.timeFromLastGuide.Start() #reset stopwatch

            elif self.status == "guide_calibration_waiting":
                pass

            elif self.status == "guide_calibrating":
                corrRateAR, corrRateDEC, invAR, invDEC, angolo, countdown = self.Processes.GuideCalibrationRoutine(self.actualX, self.actualY, self.MainFrame.invertAr.Value, self.MainFrame.invertDec.Value, self.calibrationSize)
                self.MainFrame.guideInstr.Value += ". "
                self.genericCounter += 1
                if self.genericCounter >=10:
                    self.MainFrame.guideInstr.Value = self.testo[21]
                    self.genericCounter = 0
                if countdown == 0:
                    self.MainFrame.arGuideValue.Value, self.MainFrame.decGuideValue.Value = str(int(corrRateAR)), str(int(corrRateDEC))
                    self.angolo = angolo
                    self.MainFrame.invertAr.Value, self.MainFrame.invertDec.Value = invAR, invDEC
                    self.SetStatus("idle")
                    self.MainFrame.guideInstr.Value = self.testo[22]
                    print "GUIDE VALUES: ", self.MainFrame.arGuideValue.Value, self.MainFrame.decGuideValue.Value, "; invar-dec:", self.MainFrame.invertAr.Value, self.MainFrame.invertDec.Value, "; angle:", self.angolo*57.3
        else: #with the vampire frame visible
            if self.status == "waiting_for_vampire_victim":
                self.calcClock.Stop()
                self.SetStatus("waiting_for_vampire_victim_confirm")
                
    def PicSaveClock(self,evt):
        #manage the clock event related to multiple image saving
        picCount = self.Processes.ExtractInt(self.MainFrame.pictureNo.Value)
        picIndex = self.picTotal - picCount + 1
        self.MainFrame.picProgress.Value = int(100*(float(picIndex)/float(self.picTotal)))
        filename="../savedBMP/Image_" + str(picIndex) + "__" + self.picTime + ".bmp"
        
        if self.MainFrame.picFullScreen.Value:
            winx, winy = self.dcScreen.GetSize()
            self.Processes.SavePicture(0, 0, winx, winy, filename)
        else:
            self.Processes.SavePicture(self.vampirePosX, self.vampirePosY, self.vampireSizeX, self.vampireSizeY, filename)
        
        if picCount > 1:
            self.MainFrame.pictureNo.Value = str(picCount-1)
        else:
            self.picSaveClock.Stop()
            dial=wx.MessageDialog(self.MainFrame, self.testo[32], 'Info', wx.OK | wx.ICON_INFORMATION)
            dial.ShowModal()
            self.MainFrame.picProgress.Value = 0
        
    def DrawClock(self,evt):
        #manage the clock event related to drawings update
        if self.hideVampire:
            self.dcScreen = wx.ScreenDC()
            self.dcScreen.SetBrush(wx.TRANSPARENT_BRUSH)
            #draw crosshair
            if self.MainFrame.crosshair.GetValue():
                try:
                    self.dcScreen.SetPen(wx.Pen(self.ColorFromCode(self.crosshairColorCode),1))
                    self.dcScreen.DrawLineList(self.crosshairList)
                except:
                    pass
            #star tracking action (calculation & drawing)
            if self.starTracking:
                self.MainFrame.VampireFrame.Refresh()
                self.dcScreen.SetPen(wx.Pen(wx.RED,2))
                self.dcScreen.DrawLineList(self.Processes.CrossList(round(self.actualX),round(self.actualY),21, 30))

            if self.status ==  "alignment_calc_ready":
                self.dcScreen.SetPen(wx.Pen(wx.GREEN,1))
                self.dcScreen.DrawLine(self.errorGraphX, self.errorGraphY, self.errorGraphX+(self.xf-self.xo), self.errorGraphY+(self.yf-self.yo))
                self.dcScreen.DrawCircle(self.errorGraphX,self.errorGraphY,20)

            if self.status == "alignment_cam_calibrated":
            # draw correction lines if calculation completed
                if self.correzione>0: self.DrawCorrection()

    def DrawCorrection(self):
        #draw the line scheme for polar alignment correction
        self.dcScreen.SetBrush(wx.TRANSPARENT_BRUSH)
        self.dcScreen.SetPen(wx.Pen(wx.RED,2))
        # draws little starting circle and lines
        invert = self.MainFrame.invertCorrection.Value
        if self.starPosition == "e": invert = not(invert)
        if invert:
            self.dcScreen.DrawLineList(self.alignCorrListInv,[wx.Pen(wx.RED,2),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.CYAN,1),wx.Pen(wx.GREEN,2)] )
        else:
            self.dcScreen.DrawLineList(self.alignCorrList,[wx.Pen(wx.RED,2),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.RED,1),wx.Pen(wx.CYAN,1),wx.Pen(wx.GREEN,2)] )

class MyApp(wx.App):
    def OnInit(self):
        controller = Controller(self)
        print controller
        return True

def main():
    app = MyApp(0)
    app.MainLoop()

#if __name__ == '__main__':
#    main()
