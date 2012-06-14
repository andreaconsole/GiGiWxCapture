#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# GiGiWxCapture.py: entry point of GiGiWxCapture
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

import os, sys

def run_main():
    os.chdir(sys.path[0]+"/modules")
    from modules import Controller
    Controller.main()

if __name__ == "__main__":
    run_main()
