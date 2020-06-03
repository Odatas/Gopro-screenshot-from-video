import wx
import wx.media
import subprocess
import gopro2gpx
import xmltodict
import piexif
import os
from fractions import Fraction
from datetime import datetime
from sys import platform
from pathlib import Path

"""
Created on Fri May 22 19:42:18 2020

@author: Paddy
"""

class VideoCapture(wx.Frame):
    """
    mediapath as str path to the mp4 medium

    opens a media widget to play the video. Extracts gps from the video a
    and pares it to the screenshot that gets created
    """
    def __init__(self, mediapath, parent=None):
        wx.Frame.__init__(self, parent=parent, size=(1000, 1000))
        self.picturenumber = 0
        self.panel = wx.Panel(self)
        self.index=0
        self.mediapath=mediapath
        try:
            self.media = str(mediapath[self.index])
        except Exception:
            wx.MessageBox('Kein MP4 File gefunden ', 'Error')
            self.quit(None)
            
        self.Knopp = wx.Button(self.panel, label='Save Screenshot')
        self.Knopp.Bind(wx.EVT_BUTTON, self.screenshot)
        self.prevButton = wx.Button(self.panel,label='Previous Video')
        self.prevButton.Bind(wx.EVT_BUTTON, self.prevVideo)
        self.nextButton = wx.Button(self.panel,label='Next Video')
        self.nextButton.Bind(wx.EVT_BUTTON, self.nextVideo)
        
        if platform == "linux" or platform == "linux2":
            # linux
            backend=wx.media.MEDIABACKEND_GSTREAMER            
        elif platform == "darwin":
            # OS X
            backend=wx.media.MEDIABACKEND_QUICKTIME
        elif platform == "win32":
            # Windows...
            backend=wx.media.MEDIABACKEND_WMP10
            
            
        
        self.testMedia = wx.media.MediaCtrl(self.panel,
                                            style=wx.SIMPLE_BORDER,
                                            szBackend=backend)
        wx.media.MediaCtrl.ShowPlayerControls(self.testMedia,
                                              flags=wx.media.MEDIACTRLPLAYERCONTROLS_DEFAULT)

        self.testMedia.Bind(wx.media.EVT_MEDIA_LOADED, self.play)
        #self.testMedia.Bind(wx.media.EVT_MEDIA_FINISHED, self.quit)
        
        self.ButtonSizer=wx.BoxSizer(wx.HORIZONTAL)
        
        self.ButtonSizer.Add(self.prevButton, 0, wx.ALL, 5)
        self.ButtonSizer.Add(self.Knopp, 0, wx.ALL, 5)
        self.ButtonSizer.Add(self.nextButton, 0, wx.ALL, 5)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.ButtonSizer, 0, wx.ALL, 5)
        self.sizer.Add(self.testMedia, 0, wx.ALL, 5)

        self.panel.SetSizer(self.sizer)

        self.load()

        self.Show()
        
        
    def load(self, event=None):
        try:
            self.rawgps = gopro2gpx.extract(self.media, skip=False)
            self.gpsdict = xmltodict.parse(self.rawgps)
            self.gps = True
        except Exception as e:
            wx.MessageBox('Konnte GPS Daten nicht lesen. Error: '
                          + str(e), 'Èrror')
            self.gps = False

        if self.testMedia.Load(self.media):
            pass
        else:
            print("Media not found")
            self.quit(None)
        

    
    def nextVideo(self, event=None):
        if self.index < len(self.mediapath)-1:
            self.index+=1
            self.media=str(self.mediapath[self.index])
            self.load()
        
    def prevVideo(self, event=None):
        if self.index > 0:            
            self.index-=1
            self.media=str(self.mediapath[self.index])
            self.load()
        

    def play(self, event):
        self.testMedia.Play()

    def screenshot(self, event):
        millis = self.testMedia.Tell() + 200
        seconds = (millis / 1000) % 60
        seconds = int(seconds)
        minutes = (millis / (1000 * 60)) % 60
        minutes = int(minutes)
        hours = (millis / (1000 * 60 * 60)) % 24
        hours = int(hours)
        time = str(hours).zfill(2) + ':' + str(minutes).zfill(2) + ':' + str(seconds).zfill(2)

        onlyseconds = int(millis / 1000)
        if onlyseconds == 0:
            onlyseconds = 1

        if self.gps:
            
            try:

                lat = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["@lat"]
                long = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["@lon"]
                ele = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["ele"]
                #timeformat 2019-05-10T13:17:28Z
                picturetime = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"][onlyseconds-1]["time"]
            except Exception:
                lat = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"]["@lat"]
                long = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"]["@lon"]
                ele = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"]["ele"]
                picturetime = self.gpsdict["gpx"]["trk"]["trkseg"]["trkpt"]["time"]
                
            if float(ele) < 0:
                ele=0
            print("ele: " + str(ele))
            
            
            format_str = '%Y-%m-%dT%H:%M:%SZ'
            datetime_obj = datetime.strptime(picturetime, format_str)
            name ='image'+str(self.picturenumber) + '.jpg'
            while os.path.exists(name):
                self.picturenumber+=1
                name ='image'+str(self.picturenumber) + '.jpg'
            command='ffmpeg -y -ss '+time+' -i "'+self.media+'" -frames:v 1 -q:v 2 ' + name
            print(command)
            print('\n')
            print(subprocess.run(command))
            self.set_gps_location(name,float(lat),float(long),float(ele),datetime_obj)
        else:
            name='image'+str(self.picturenumber) + 'no_geodata' +'.jpg'
            command='ffmpeg -y -ss '+time+' -i "'+self.media+'" -frames:v 1 -q:v 2 ' + name
            print(subprocess.run(command))
            
            #command='ffmpeg -y -ss '+time+' -i "'+self.media+'" -frames:v 1 -q:v 2 image'+str(self.picturenumber)+'-'+lat+'-'+long+'.jpg'

        
        self.picturenumber+=1
        
        
    def to_deg(self, value, loc):
        """convert decimal coordinates into degrees, munutes and seconds tuple
        Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
        return: tuple like (25, 13, 48.343 ,'N')
        """
        if value < 0:
            loc_value = loc[0]
        elif value > 0:
            loc_value = loc[1]
        else:
            loc_value = ""
        abs_value = abs(value)
        deg =  int(abs_value)
        t1 = (abs_value-deg)*60
        min = int(t1)
        sec = round((t1 - min)* 60, 5)
        return (deg, min, sec, loc_value)


    def change_to_rational(self, number):
        """convert a number to rantional
        Keyword arguments: number
        return: tuple like (1, 2), (numerator, denominator)
        """
        f = Fraction(str(number))
        return (f.numerator, f.denominator)


    def set_gps_location(self, file_name, lat, lng, altitude,datetime_obj):
        """Adds GPS position as EXIF metadata
        Keyword arguments:
        file_name -- image file
        lat -- latitude (as float)
        lng -- longitude (as float)
        altitude -- altitude (as float)
        """
        lat_deg = self.to_deg(lat, ["S", "N"])
        lng_deg = self.to_deg(lng, ["W", "E"])
    
        exiv_lat = (self.change_to_rational(lat_deg[0]), self.change_to_rational(lat_deg[1]), self.change_to_rational(lat_deg[2]))
        exiv_lng = (self.change_to_rational(lng_deg[0]), self.change_to_rational(lng_deg[1]), self.change_to_rational(lng_deg[2]))
    
        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: self.change_to_rational(round(altitude)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
            
        }
        print(datetime_obj.strftime("%Y:%m:%d %H:%M:%S"))
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: datetime_obj.strftime("%Y:%m:%d %H:%M:%S"),
            }
        # exif_dict = {"GPS": gps_ifd}
        # exif_bytes = piexif.dump(exif_dict)
        # piexif.insert(exif_bytes, file_name)
        
        exif_exif = {"Exif":exif_ifd}
        gps_exif = {"GPS": gps_ifd}

        # get original exif data first!
        exif_data = piexif.load(file_name)
    
        # update original exif data to include GPS tag
        exif_data.update(gps_exif)
        exif_data.update(exif_exif)
        exif_bytes = piexif.dump(exif_data)
    
        piexif.insert(exif_bytes, file_name)

    def quit(self, event):
        self.Destroy()


class mainWindow(wx.Frame):
    """
    Creates Bare Bone Video Selection Window
    """
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
        dialog = wx.DirDialog(None, "Ordner auswählen",style= wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            self.path=Path(dialog.GetPath())
            self.files=os.listdir(self.path)
            print("BEFORE")
            print(self.files)
            self.files= [self.path / i for i in self.files if i.endswith('mp4') or i.endswith('MP4')]
            print("AFTER")
            print(self.files)
            print("-----------------------------------")
            print(self.files)
            VideoCapture(self.files)
        else:
            wx.MessageBox('Unbekannter Fehler beim Auswählen des Ordners. Ist der Ordner Verfügbar?', 'Èrror',)
        dialog.Destroy()



if __name__ == '__main__':
    app = wx.App()
    Frame = mainWindow()
    Frame.Show()
    app.MainLoop()