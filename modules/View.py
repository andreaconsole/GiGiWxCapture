# -*- coding: utf-8 -*-
# View.pyw: Frame classes for GiGiWxCapture
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

class MainFrame(wx.Frame):
    def __init__(self,parent,resource):
        self.PostCreate(resource.LoadFrame(parent,"gigiwxcapture"))
        self.LeftUpCornerOnScreen()
        self.Show()
        self.VampireFrame = VampireFrame(self,resource)
        self.AboutFrame = AboutFrame(self,resource)
        self.ZoomFrame = ZoomFrame(self,resource)
        self.GraphFrame = GraphFrame(self,resource)
        
    def LeftUpCornerOnScreen(self):
        ds,s = wx.DisplaySize(), self.GetSizeTuple()
        x = 0
        y = 0
        self.Move(wx.Point(x,y))

class VampireFrame(wx.Frame):
    def __init__(self,parent,resource):
        self.PostCreate(resource.LoadFrame(parent,"vampireFrame"))
        self.CentreOnScreen(wx.BOTH)

class AboutFrame(wx.Frame):
    def __init__(self,parent,resource):
        self.PostCreate(resource.LoadFrame(parent,"aboutFrame"))
        self.CentreOnScreen(wx.BOTH)
        
class GraphFrame(wx.Frame):
    def __init__(self,parent,resource):
        self.PostCreate(resource.LoadFrame(parent,"graphFrame"))
        self.LeftDownCornerOnScreen()
        
    def LeftDownCornerOnScreen(self):
        ds,s = wx.DisplaySize(), self.GetSizeTuple()
        x = 0
        y = (ds[1] - s[1])
        self.Move(wx.Point(x,y))

class ZoomFrame(wx.Frame):
    def __init__(self,parent,resource):
        self.PostCreate(resource.LoadFrame(parent,"zoomFrame"))
        self.RightUpCornerOnScreen()

    def RightUpCornerOnScreen(self):
        ds,s = wx.DisplaySize(), self.GetSizeTuple()
        x = (ds[0] - s[0])
        y = 0
        self.Move(wx.Point(x,y))
