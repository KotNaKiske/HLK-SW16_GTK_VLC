#!/usr/bin/env python3
import signal,os,gi,threading,socket,time,datetime,vlc,pigpio,Adafruit_DHT,requests
from miio import Vacuum
import paho.mqtt.client as pahomqtt
from PerpetualTimer import PerpetualTimer
from socketserver import *
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject
from array import *
from datetime import datetime

#os.system('xinput set-prop 6 "Coordinate Transformation Matrix" -1, 0, 1, 0, -1, 1, 0, 0, 1') os.system("vcgencmd display_power 1 >>/dev/null")
############################################################################################################################################################################################
visible = {"Камера":False,
           "Часы":True,
           "МиниЧасы":False,
           "ОсталосьВремени1":False,
           "ОсталосьВремени2":False,
           "ОсталосьВремени3":False,
           "ОсталосьВремени4":False,
           "ОсталосьВремени5":False,
           "МенюСвета":False,
           "Кнопка11":False,
           "Кнопка12":False,
           "Пылесос":False,
           "Кнопка21":True,
           "Кнопка22":True,
           "Кнопка23":True,
           "Кнопка24":True,
           "Кнопка25":True,
           "Запись":False,
           "Кнопка1":False,
           "Кнопка2":False,
           "Кнопка3":False,
           "Кнопка4":False,
           "Кнопка5":False}
roborock = Vacuum("192.168.0.20", "",0,1)
setting = {"ВремяЗаписи":0,
           "ВремяДопМеню":0,
           "НажатаКнопка":0,
           "НажатаМышка":False,
           "Мышка_X":0,
           "Мышка_Y":0,
           "Экран":1}
button = [[],[7,7],[16,8],[13,13],[3,3],[7,7]]
vlcInstance = vlc.Instance(['--logfile=/dev/null', '--quiet', '--no-video-on-top','--no-video-title-show','--no-xlib','--no-plugins-cache'])
player = False
def elemvisible(el,b):
   global visible 
   if(b!=visible[el]):
      visible[el]=b
      if(b):
         GLib.idle_add(builder.get_object(el).show)
      else:
         GLib.idle_add(builder.get_object(el).hide)
def elemclass(el,b):
   global visible 
   if(b!=visible[el]):
      visible[el]=b
      if(b):
         GLib.idle_add(builder.get_object(el).get_style_context().add_class,"red")
      else:
         GLib.idle_add(builder.get_object(el).get_style_context().remove_class,"red")
def sendcmd(b,t):
    requests.get('http://192.168.0.3/sw/'+str(button[b][0])+'/'+t)
def startvlc(rec):
   global player
   try:
      player = vlcInstance.media_player_new()
      put="/var/www/records/"
      player.set_xwindow(builder.get_object("Камера").get_window().get_xid())   
      if(rec):
         os.system("mkdir -p "+put+datetime.now().strftime("%Y%m/%d"))
         player.set_media(vlcInstance.media_new("rtsp://192.168.0.10/user=admin&password=&channel=1&stream=0", "sout=#duplicate{dst=display,dst=\"transcode{acodec=aac}:std{access=file,mux=ts,dst='"+put+datetime.now().strftime("%Y%m/%d/%H_%M_%S")+".mpg'}\"}"))
      else:
         player.set_media(vlcInstance.media_new("rtsp://192.168.0.10/user=admin&password=&channel=1&stream=0"))
      player.video_set_mouse_input(False)
      player.video_set_key_input(False)
      player.play()
   except Exception:
      print("ошибка vlc") 
def startrecord():
   global player
   try:
      if(not visible["Запись"]):
         player.stop()
      startvlc(True)
      elemvisible("Запись",True)
   except Exception:
      print("ошибка vlc2")  
def stoprecord():
   global player
   try:
      player.stop()
      if(visible["Запись"]):
         startvlc(False)
      elemvisible("Запись",False)
   except Exception:
      print("ошибка vlc3")

def mqtt_message(client, userdata, msg):  
    #try:
       #print("%s: %s" % (msg.topic, msg.payload))
       if(msg.topic=="ESP/dht"):
          GLib.idle_add(builder.get_object("Температура").set_text,(str(msg.payload.decode("utf-8"))).split("|")[1]+"°")
          GLib.idle_add(builder.get_object("Влажность").set_text,(str(msg.payload.decode("utf-8"))).split("|")[0]+"%")
       if(msg.topic=="ESP/S"):#7 9 13 3  0|||0|||0|||1|||0|||0|||0|||0|||1||559682|0|||1||559682|0|||1||559682|0|||1||559682|0|||
          ESPS=str(msg.payload.decode("utf-8"))
          elemclass("Кнопка1",(ESPS.split("|")[7*3]=="0"))
          elemclass("Кнопка2",(ESPS.split("|")[8*3]=="0"))
          elemclass("Кнопка3",(ESPS.split("|")[13*3]=="0"))
          elemclass("Кнопка4",(ESPS.split("|")[3*3]=="0"))
          elemclass("Кнопка5",(ESPS.split("|")[15*3]=="0"))
          for b in range(1,5):
          #   print(not (ESPS.split("|")[button[b][1]*3+2]==''))
             elemvisible("ОсталосьВремени"+str(b),not (ESPS.split("|")[button[b][1]*3+2]==''))
             if(ESPS.split("|")[button[b][1]*3+2]!=''):
                GLib.idle_add(builder.get_object("ОсталосьВремени"+str(b)).set_text,(""+datetime.fromtimestamp(int(ESPS.split("|")[button[b][1]*3+2])/1000-10800).strftime("%H:%M:%S")))
     
    #except Exception:
    #   print("ошибка mqtt") 
class Server8080H(StreamRequestHandler):
    def handle(self):     
        global setting
        self.data = self.request.recv(1024)
        if(setting["ВремяЗаписи"]==0):
                startrecord()
        setting["ВремяЗаписи"]=time.time()+120
        if(str(self.data).find("Stop")>-1):
                setting["ВремяЗаписи"]=time.time()+30
class Server8080(threading.Thread):
    def __init__(self):
       threading.Thread.__init__(self)
    def run(self):
       server = TCPServer(('', 8080), Server8080H)
       print(str(datetime.now())+" starting server")
       server.serve_forever()

class connectsignals:
    def __init__(self):
        pass
    def numberclick(self, Button):
        n=int(builder.get_object("ПроходовПылесоса").get_text())+1
        if(n>3):
           n=1
        GLib.idle_add(builder.get_object("ПроходовПылесоса").set_text,str(n))
    def fanspeed(self, el1, el2):
       try:
          roborock.set_fan_speed(int(builder.get_object("МощностьПылесоса").get_value()))
       except Exception:
          print("ошибка связи")
    def roborockresumeclick(self, Button):
       try:
          roborock.resume_or_start()
       except Exception:
          print("ошибка связи")
    def roborockpauseclick(self, Button):
       try:
          roborock.pause()
       except Exception:
          print("ошибка связи")
    def roborockdokclick(self, Button):
       try:
          roborock.home()
       except Exception:
          print("ошибка связи")
    def roborockclick(self, Button):
       mas=[]
       if(builder.get_object("Комната1").get_state()):#18=зал
          mas+=[18]
       if(builder.get_object("Комната2").get_state()):#16=Спальня
          mas+=[16]
       if(builder.get_object("Комната3").get_state()):#19=кухня
          mas+=[19]
       if(builder.get_object("Комната4").get_state()):#17=Коридор
          mas+=[17]
       if(builder.get_object("Комната5").get_state()):#20=туалет
          mas+=[20]
       try:
          roborock.send("app_segment_clean",[{"segments":mas,"repeat":int(builder.get_object("ПроходовПылесоса").get_text())}])
       except Exception:
          print("ошибка связи")
    def buttonclick(self, Button):
       for b in range(1,5):
          if(Button==builder.get_object("Кнопка"+str(b))):
             if(setting["НажатаКнопка"]==b):
                elemvisible("МенюСвета",False)
                setting["НажатаКнопка"]=0
                setting["ВремяДопМеню"]=0
             else:
                setting["ВремяДопМеню"]=time.time()+60
                setting["НажатаКнопка"]=b
                elemvisible("МенюСвета",True)
       if(Button==builder.get_object("Кнопка5")):
          requests.get('http://192.168.0.3/sw/15/r')
       elif(Button==builder.get_object("Кнопка11")):#Отключить
          sendcmd(setting["НажатаКнопка"],"g")
       elif(Button==builder.get_object("Кнопка12")):#Отключить
          sendcmd(setting["НажатаКнопка"],"r")
       elif(Button==builder.get_object("Кнопка13")):#10минут
         sendcmd(setting["НажатаКнопка"],"y10")
       elif(Button==builder.get_object("Кнопка14")):#1час
             sendcmd(setting["НажатаКнопка"],"y60")
    def onbutton(self, Window, event):
       global player
       if(event.type.value_name=="GDK_BUTTON_PRESS"):
          setting["НажатаМышка"]=True
          setting["Мышка_X"]=event.x
          setting["Мышка_Y"]=event.y
       if(event.type.value_name=="GDK_BUTTON_RELEASE"):
          if((setting["НажатаМышка"]) & (setting["Мышка_X"]-event.x>200)):
             sendcmd(1,"r")
             sendcmd(2,"r")
          #os.system("sudo /sbin/hdparm -y /dev/sda &")
          elif((setting["НажатаМышка"]) & (setting["Мышка_X"]-event.x<-200)):
             sendcmd(1,"y20")
             sendcmd(2,"y20")
          elif((setting["НажатаМышка"]) & (setting["Мышка_Y"]-event.y>200)):
             if(setting["Экран"]==1):
                elemvisible("Часы",False)
                elemvisible("МиниЧасы",True)
                elemvisible("Камера",True)
                if(setting["ВремяЗаписи"]==0):
                   startvlc(False)
                setting["Экран"]=2
             if(setting["Экран"]==0):
                elemvisible("Часы",True)
                elemvisible("МиниЧасы",False)
                elemvisible("Пылесос",False)
                setting["Экран"]=1
          elif((setting["НажатаМышка"]) & (setting["Мышка_Y"]-event.y<-200)):
             if(setting["Экран"]==1):
                elemvisible("Часы",False)
                elemvisible("МиниЧасы",True)
                elemvisible("Пылесос",True)
                setting["Экран"]=0
             if(setting["Экран"]==2):
                #try:
                if(setting["ВремяЗаписи"]==0):
                   player.stop()
                #except Exception:
                #   print("ошибка player")
                elemvisible("Часы",True)
                elemvisible("МиниЧасы",False)
                elemvisible("Камера",False)
                setting["Экран"]=1

          setting["НажатаМышка"]=False;
def OnTimer():
   GLib.idle_add(builder.get_object("Часы").set_text,datetime.strftime(datetime.now(), "%H:%M:%S"))
   GLib.idle_add(builder.get_object("МиниЧасы").set_text,datetime.strftime(datetime.now(), "%H:%M:%S"))
   GLib.idle_add(builder.get_object("Дата").set_text,datetime.strftime(datetime.now(), "%d.%m.%Y"))
   mqtt.loop()
   if((setting["ВремяЗаписи"]!=0)&(time.time()-setting["ВремяЗаписи"]>=0)):
      setting["ВремяЗаписи"]=0
      stoprecord()
   if(setting["ВремяДопМеню"]!=0):
      if(time.time()-setting["ВремяДопМеню"]>=0):
        setting["ВремяДопМеню"]=0
        elemvisible("МенюСвета",False)

def OnTimer2():
   if(visible["Пылесос"]):
      try:
         stat=roborock.status()
         if(stat.state_code in [6,8]):#8: "Charging" 6 возврат на док
            elemvisible("Кнопка21",True)
            elemvisible("Кнопка22",True)
            elemvisible("Кнопка23",False)
            elemvisible("Кнопка24",False)
            elemvisible("Кнопка25",False)
         elif(stat.state_code==10):#10: "Paused"
            elemvisible("Кнопка21",False)
            elemvisible("Кнопка22",False)
            elemvisible("Кнопка23",False)
            elemvisible("Кнопка24",True)
            elemvisible("Кнопка25",True)
         elif(stat.state_code==18):#18: "уборка"
            elemvisible("Кнопка21",False)
            elemvisible("Кнопка22",False)
            elemvisible("Кнопка23",True)
            elemvisible("Кнопка24",False)
            elemvisible("Кнопка25",True)
         else:
            print ("state_code"+stat.state_code+"|"+stat.state)
         
         GLib.idle_add(builder.get_object("СтатусПылесоса").set_text,stat.state)
         GLib.idle_add(builder.get_object("ИнфоПылесоса").set_text,"Уровень заряда="+str(stat.battery)+"%\n"+"Последняя уборка="+str(stat.clean_area)+"м за "+str(stat.clean_time))
         GLib.idle_add(builder.get_object("МощностьПылесоса").set_value,stat.fanspeed)
      except Exception:
         print("ошибка связи")

signal.signal(signal.SIGINT, signal.SIG_DFL)
mqtt = pahomqtt.Client()
mqtt.on_message = mqtt_message

mqtt.connect("192.168.0.1")
mqtt.subscribe("ESP/#")
#mqtt.publish("house/bulbs/bulb1","OFF")
builder = Gtk.Builder()
builder.add_from_file('0.glade')
builder.connect_signals(connectsignals())

window = builder.get_object('window')
window.fullscreen()
screen = Gdk.Screen.get_default()
css_provider = Gtk.CssProvider()
css_provider.load_from_path('1.css')
context = Gtk.StyleContext()
context.add_provider_for_screen(screen, css_provider,
     Gtk.STYLE_PROVIDER_PRIORITY_USER)
vlcInstance = vlc.Instance(['--logfile=/dev/null', '--quiet', '--no-video-on-top'])

S8080 = Server8080()
S8080.start()

timer = PerpetualTimer(0.1, OnTimer)
timer.start()
timer2 = PerpetualTimer(1, OnTimer2)
timer2.start()

vlcInstance = vlc.Instance(['--logfile=/dev/null', '--quiet', '--no-video-on-top','--no-video-title-show','--no-xlib','--no-plugins-cache'])
Gtk.main()
