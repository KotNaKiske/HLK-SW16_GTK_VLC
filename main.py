#!/usr/bin/env python3
import signal,os,gi,threading,socket,time,datetime,vlc,pigpio
from PerpetualTimer import PerpetualTimer
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject
from datetime import datetime
os.system('xinput set-prop 6 "Coordinate Transformation Matrix" -1, 0, 1, 0, -1, 1, 0, 0, 1')
os.system("sudo pigpiod")
#os.system("sudo swapoff -a")

off=[666,0,0,False,666,0]
#время отключения дисплея,позиции мышки,Доп меню света,Запись видео
class structure:
    structure=[[0, False, 'TV', 666, 666, 0], [1, False, '', 666, 666, -1,b"\x00"], [2, False, 'Свалка', 666, 666, -1,b"\x01"], [3, False, '', 666, 666, -1,b"\x02"], [4, False, 'Cпальня', 666, 666, 4,b"\x03"],
[5, False, '', 666, 666, -1,b"\x04"], [6, False, 'Коридор', 666, 666, -1,b"\x05"], [7, False, '', 666, 666, -1,b"\x06"], [8, False, 'кухня', 666, 666, 1,b"\x07"], [9, False, '', 666, 666, -1,b"\x08"],
[10, False, 'Зал', 666, 666, 2,b"\x09"], [11, False, '', 666, 666, -1,b"\x0a"], [12, False, 'Зал2', 666, 666, -1,b"\x0b"], [13, False, '', 666, 666, -1,b"\x0c"], [14, False, 'ванная', 666, 666, 3,b"\x0d"],
[15, False, '', 666, 666, -1,b"\x0e"], [16, False, 'туалет', 666, 666, 5,b"\x0f"]]
    #masbutton=[0,7,9,13,3,1]
    masbutton=[0,8,10,14,4,2]
    def __init__(self):
       threading.Thread.__init__(self)
    def set_value(self,pin,val):
       self.structure[pin][1]=val
    def get_value(self,pin):
       return self.structure[pin][1]
    def get_button(self,pin):
       return self.structure[pin][5]
    def get_ws16(self,pin):
       return self.structure[pin][6]
    def set_timers(self,pin,val):
       self.structure[pin][3]=val
    def get_timers(self,pin):
       return self.structure[pin][3]
    def get_namebutton(self,pin):
       return self.structure[pin][2]
structure=structure()

class GPIO(threading.Thread):
    Gpio = pigpio.pi()
    MasGpio=[2,17,27,22,10,9,11,5,6,13,19,26,18,23,24,25,8,7,12,16,20,21]
    gpiotimer=[0,False]
    def __init__(self):
       threading.Thread.__init__(self)
       for G in self.MasGpio:
          self.Gpio.set_mode(G, pigpio.INPUT)
          self.Gpio.set_pull_up_down(G, pigpio.PUD_UP)
          self.Gpio.callback(G, pigpio.EITHER_EDGE, self.GPIOon)
          self.Gpio.set_glitch_filter(G, 10000)
    def run(self):
       pass
    def GPIOon(self, gpio, level, tick):
       print(time.ctime(time.time()),"!!!GPIO", gpio, level, tick)
       if(gpio==20):#Туалет
          WS16Thread.send(16,True)
          structure.set_timers(16,time.time()+60)
       if((gpio==26)&(level==0)):#Спальня
          WS16Thread.send(4,9)
       if((gpio==19)&(level==0)):#зал
          WS16Thread.send(10,True)
          WS16Thread.send(8,True)
          structure.set_timers(8,time.time()+10*60)
          structure.set_timers(10,time.time()+10*60)
       if((gpio==13)&(level==0)):#Ванная
          self.gpiotimer[1]=structure.get_value(8)
          WS16Thread.send(8,True)
          #set_structure(8,3,time.time()+2.5)
          #set_structure(8,4,time.time()+3)
          self.gpiotimer[0]=time.time()
       if((gpio==13)&(level==1)):#Ванная
          #self.gpiotimer[1]=time.time()
          #set_structure(8,3,666)
          #set_structure(8,4,666)
          if(self.gpiotimer[0]+3<time.time()):
             WS16Thread.send(8,True)
             WS16Thread.send(14,True)
          else:
             if(self.gpiotimer[1]==False):
                WS16Thread.send(8,True)
                WS16Thread.send(14,False)
                structure.set_timers(8,time.time()+10*60)
             else:
                WS16Thread.send(8,False)
                WS16Thread.send(14,True)

class WS16Thread(threading.Thread):
    t=False
    ws16 = socket.socket()
    sendlast=time.time()
    mas=[]
    def __init__(self):
       threading.Thread.__init__(self)
       self.t = PerpetualTimer(0.03, self.sw16send)
    def run(self):
       self.ws16.connect(('192.168.0.254', 8080))
       self.send(-1,True);
       while True:
          data = self.ws16.recv(1024)
          #print(data)
          if(data[1]==12):
             sendlast=True
             data=data.split(b"\xcc\x0c").pop()
             print(data)
             i=1
             for number in data[0:16]:
                if(number==2):
                   structure.set_value(i,False)
                else:
                   structure.set_value(i,True)
                if(structure.get_button(i)>=0):
                   GLib.idle_add(builder.get_object("i"+str(structure.get_button(i))).set_from_file,"button"+str(int(structure.get_value(i)))+".png")
                   #builder.get_object("i"+str(structure.get_button(i))).set_from_file("button"+str(int(structure.get_value(i)))+".png")
                i=i+1
          time.sleep(0.1)
    def send(self,pin,val):
      if (pin>-1):
         if (val==9):
            self.mas.append([pin,not structure.get_value(pin)])
         else:
            self.mas.append([pin,val])
      else:
         self.mas.append([pin,val])
      self.t.start()

    def sw16send(self):
       pin,val=self.mas.pop(0)
       print('>!sw16',[pin,val])
       if (pin==-1):
          self.ws16.send(b"\xaa\x1e\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xbb")
       else:
          if(structure.get_value(pin)!=bool(val)):
             if(bool(val)==True):
                 self.ws16.send(b"\xaa\x0f"+structure.get_ws16(pin)+b"\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xbb")
             else:
                 self.ws16.send(b"\xaa\x0f"+structure.get_ws16(pin)+b"\x02\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\xbb")
       if(len(self.mas)==0):
          self.t.cancel()


class connectsignals:
    def __init__(self):
        pass
    def buttonclick(self, Button):
       global off
       if ((off[0]==666)):
          os.system("vcgencmd display_power 1 >>/dev/null")
       off[0]=time.time()+60
       if(off[4]==666):
          for b in range(1,5):
             if(Button==builder.get_object("b"+str(b))):
                off[4]=time.time()+60
                off[5]=structure.masbutton[b]
                builder.get_object("МенюСвета").show()
          if(Button==builder.get_object("b0")):
             print("@@@")
       else:
          if(Button==builder.get_object("g0")):#Отключить
             if(structure.get_value(off[5])==True):
                structure.set_timers(off[5],time.time()+5)
          elif(Button==builder.get_object("g1")):#5минут
             WS16Thread.send(off[5],True)
             structure.set_timers(off[5],time.time()+5*60)
          elif(Button==builder.get_object("g2")):#Включить
             WS16Thread.send(off[5],True)
             structure.set_timers(off[5],666)
          elif(Button==builder.get_object("g3")):#20минут
             WS16Thread.send(off[5],True)
             structure.set_timers(off[5],time.time()+20*60)
          else:
             for b in range(1,5):
                if(Button==builder.get_object("b"+str(b))):
                   break
             if(off[5]==structure.masbutton[b]):
                off[4]=666
                builder.get_object("МенюСвета").hide()
             else:
                off[4]=time.time()+60
                off[5]=structure.masbutton[b]

    def onbutton(self, Window, event):
       global off, player
       if (off[0]==666):
          os.system("vcgencmd display_power 1 >>/dev/null")
       off[0]=time.time()+60
       if(event.type.value_name=="GDK_BUTTON_PRESS"):
          off[3]=True
          off[1]=event.x
          off[2]=event.y
       if(event.type.value_name=="GDK_BUTTON_RELEASE"):
          if((off[3]) & (off[1]-event.x>200)):
             if(structure.get_value(8)==True): 
                structure.set_timers(8,time.time()+5)
             if(structure.get_value(10)==True):
                structure.set_timers(10,time.time()+5)
             if(structure.get_value(12)==True):
                structure.set_timers(12,time.time()+5)
          #os.system("sudo /sbin/hdparm -y /dev/sda &")
          elif((off[3]) & (off[1]-event.x<-200)):
             WS16Thread.send(4,True)
             WS16Thread.send(10,True)
             WS16Thread.send(8,True)
             structure.set_timers(8,time.time()+10*60)
             structure.set_timers(10,time.time()+10*60)
          elif((off[3]) & (off[2]-event.y>200)):
             vlcInstance = vlc.Instance(['--logfile=/dev/null', '--quiet', '--no-video-on-top'])
             player = vlcInstance.media_player_new()
             player.set_xwindow(builder.get_object("video").get_window().get_xid())   
             player.set_media(vlcInstance.media_new("rtsp://192.168.0.10/user=admin&password=&channel=1&stream=0"))

             player.video_set_mouse_input(False)
             player.video_set_key_input(False)

             player.play()
             builder.get_object("Обычный").hide()
             builder.get_object("video").show()
          elif((off[3]) & (off[2]-event.y<-200)):
             player.stop()
             builder.get_object("Обычный").show()
             builder.get_object("video").hide()
          off[3]=False;

def OnTimer():
   GLib.idle_add(builder.get_object("clock").set_text,datetime.strftime(datetime.now(), "%H:%M:%S"))
   GLib.idle_add(builder.get_object("date").set_text,datetime.strftime(datetime.now(), "%d.%m.%Y"))

   if((off[0]!=666)&(time.time()-off[0]>=0)):
      off[0]=666
      os.system("vcgencmd display_power 0 >>/dev/null")
   if(off[4]!=666):
      if(time.time()-off[4]>=0):
         off[4]=666
         GLib.idle_add(builder.get_object("МенюСвета").hide)
      if(structure.get_timers(off[5])>time.time()):
         GLib.idle_add(builder.get_object("sl0").set_text,structure.get_namebutton(off[5])+"   "+datetime.strftime(datetime.fromtimestamp(structure.get_timers(off[5])-time.time()), "%M:%S"))
      else:
         GLib.idle_add(builder.get_object("sl0").set_text,structure.get_namebutton(off[5]))

   for s in structure.structure:
      if(s[5]!=-1):
         if(s[3]>time.time()):
            GLib.idle_add(builder.get_object("t"+str(s[5])).set_text,datetime.strftime(datetime.fromtimestamp(s[3]-time.time()), "%M:%S"))
         else:
            GLib.idle_add(builder.get_object("t"+str(s[5])).set_text,"")
      if((s[1]==True)&(s[3]-time.time()<=0) & (s[3]!=666)):
         print(time.ctime(time.time()),"OFF!",s[0],s[3])
         WS16Thread.send(s[0],False)
         s[3]=666


GPIO = GPIO()
GPIO.start()

signal.signal(signal.SIGINT, signal.SIG_DFL)
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
window.show_all()
vlcInstance = vlc.Instance(['--logfile=/dev/null', '--quiet', '--no-video-on-top'])
builder.get_object("video").hide()
builder.get_object("МенюСвета").hide()

WS16Thread = WS16Thread()
WS16Thread.start()
timer = PerpetualTimer(0.1, OnTimer)
timer.start()
Gtk.main()
