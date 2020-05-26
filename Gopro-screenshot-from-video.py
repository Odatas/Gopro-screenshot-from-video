import wx
import wx.media
import subprocess
import gopro2gpx
import xmltodict


"""
Created on Fri May 22 19:42:18 2020

@author: Paddy
"""


class VideoCapture(wx.Frame):
    def __init__(self, mediapath, parent=None):
        wx.Frame.__init__(self, parent=parent, size=(1000, 1000))
        self.picturenumber = 0
        self.panel = wx.Panel(self)
        self.media = mediapath
        self.Knopp = wx.Button(self.panel, label='Save Screenshot')
        self.Knopp.Bind(wx.EVT_BUTTON, self.screenshot)
        self.testMedia = wx.media.MediaCtrl(self.panel, 
                                            style=wx.SIMPLE_BORDER, 
                                            szBackend=wx.media.MEDIABACKEND_WMP10)
        wx.media.MediaCtrl.ShowPlayerControls(self.testMedia,flags=wx.media.MEDIACTRLPLAYERCONTROLS_DEFAULT)

        self.testMedia.Bind(wx.media.EVT_MEDIA_LOADED, self.play)
        self.testMedia.Bind(wx.media.EVT_MEDIA_FINISHED, self.quit)

        self.sizer=wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.Knopp,0,wx.ALL,5)
        self.sizer.Add(self.testMedia,0,wx.ALL,5)


        self.panel.SetSizer(self.sizer)

        try:
            self.rawgps=gopro2gpx.extract(self.media,skip=False, verbose=2)
            self.gpsdict=xmltodict.parse(self.rawgps)
            self.gps=True
        except Exception as e:
            wx.MessageBox('Konnte GPS Daten nicht lesen. Error: '+str(e), 'Èrror')
            self.gps=False


        if self.testMedia.Load(self.media):
            pass
        else:
            print("Media not found")
            self.quit(None)

        self.Show()




    def play(self, event):
        self.testMedia.Play()

    def screenshot(self,event):
        millis=self.testMedia.Tell()+200
        seconds=(millis/1000)%60
        seconds = int(seconds)
        minutes=(millis/(1000*60))%60
        minutes = int(minutes)
        hours=(millis/(1000*60*60))%24
        hours=int(hours)
        time=str(hours).zfill(2)+':'+str(minutes).zfill(2)+':'+str(seconds).zfill(2)

        onlyseconds=int(millis/1000)

        if self.gps:

            lat='Lat'+self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["@lat"]
            long='Long'+self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["@lon"]
        else:
            lat=''
            long=''


        folder=r'F:\\'

        command='ffmpeg -y -ss '+time+' -i "'+self.media+'" -frames:v 1 -q:v 2 image'+str(self.picturenumber)+'-'+lat+'-'+long+'.jpg'
        print(subprocess.run(command))
        self.picturenumber+=1

    def quit(self, event):
        self.Destroy()


class mainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.panel = wx.Panel(self)


        self.BrowseButton=wx.Button(self.panel,label="Mp4 Datei Auswählen")
        self.BrowseButton.Bind(wx.EVT_BUTTON,self.onBrowse)

        self.sizer=wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.BrowseButton,0, wx.ALL,200)


        self.panel.SetSizer(self.sizer)
        self.sizer.SetSizeHints(self)



    def quit(self, event):
        self.Destroy()





    def onBrowse(self, event):
        """
        Opens Dialog to Browse for a file
        """
        dialog = wx.FileDialog(None, "MP4 auswählen",wildcard="MP4 files (*.mp4)|*.mp4",style= wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            VideoCapture(dialog.GetPath())
        else:
            wx.MessageBox('Unbekannter Fehler beim Auswählen des Ordners. Ist der Ordner Verfügbar?', 'Èrror',)
        dialog.Destroy()


if __name__ == '__main__':
    app = wx.App()
    Frame = mainWindow()
    Frame.Show()
    app.MainLoop()