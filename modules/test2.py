
import wx
import os


def dirchoose():
#Gives the user selected path. Use: dirchoose()'
    global _selectedDir , _userCancel #you should define them before
    userPath = '/home/andrea/workspace/GiGiWxCapture/gigiwxcapture12/pippolo/ascci/dede'
    app = wx.App()
    dialog = wx.DirDialog(None, "Please choose your project directory:",\
    style=1 ,defaultPath=userPath, pos = (10,10))
    if dialog.ShowModal() == wx.ID_OK:
        _selectedDir = dialog.GetPath()
        return _selectedDir, os.path.abspath(_selectedDir)
    
    else:
        #app.Close()
        dialog.Destroy()
        return _selectedDir
    
def run_main():
    a,b = dirchoose()
    print a,b

if __name__ == "__main__":
    run_main()