#!/usr/bin/python
from Tkinter import *
import serial, time

sPSUBot = serial.Serial( '/dev/rfcomm0', 9600, timeout=1 );

def send_command( wnd_app_in, command_in ):
   sPSUBot.write( command_in + "\r" )

# Create the window...
wnd_info = Tk()
wnd_info.config( padx=10, pady=10, bg="black" )

# Create the window controls...

wnd_info.frm_buttons_led = Frame( wnd_info )
wnd_info.frm_buttons_led.btn_led_red = Button(
   wnd_info.frm_buttons_led,
   text="LED: Red",
   command=lambda: send_command( wnd_info, 'LED RED' )
)
wnd_info.frm_buttons_led.btn_led_green = Button(
   wnd_info.frm_buttons_led,
   text="LED: Green",
   command=lambda: send_command( wnd_info, 'LED GREEN' )
)
wnd_info.frm_buttons_led.btn_led_blue = Button(
   wnd_info.frm_buttons_led,
   text="LED: Blue",
   command=lambda: send_command( wnd_info, 'LED BLUE' )
)

wnd_info.frm_buttons_eye = Frame( wnd_info )
wnd_info.frm_buttons_eye.btn_eye_left = Button(
   wnd_info.frm_buttons_eye,
   text="Eye: Left",
   command=lambda: send_command( wnd_info, 'EYE L 10' )
)
wnd_info.frm_buttons_eye.btn_eye_right = Button(
   wnd_info.frm_buttons_eye,
   text="Eye: Right",
   command=lambda: send_command( wnd_info, 'EYE R 10' )
)

wnd_info.frm_buttons_beep = Frame( wnd_info )
wnd_info.frm_buttons_beep.btn_beep = Button(
   wnd_info.frm_buttons_beep,
   text="Beep",
   command=lambda: send_command( 
      wnd_info,
      'BEEP ' + wnd_info.frm_buttons_beep.spn_beep_freq.get() + ' ' +
         wnd_info.frm_buttons_beep.spn_beep_time.get()
   )
)
wnd_info.frm_buttons_beep.lbl_beep_freq = Label(
   wnd_info.frm_buttons_beep,
   text="Frequency:"
)
wnd_info.frm_buttons_beep.spn_beep_freq = Spinbox(
   wnd_info.frm_buttons_beep,
   from_=0,
   to=10000
)
wnd_info.frm_buttons_beep.lbl_beep_time = Label(
   wnd_info.frm_buttons_beep,
   text="Time:"
)
wnd_info.frm_buttons_beep.spn_beep_time = Spinbox(
   wnd_info.frm_buttons_beep,
   from_=0,
   to=10000
)

wnd_info.frm_buttons_wheels = Frame( wnd_info )
wnd_info.frm_buttons_wheels.btn_lp = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Left (Hard)",
   command=lambda: send_command( wnd_info, 'DRIVE PL 10000' )
)
wnd_info.frm_buttons_wheels.btn_l = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Left",
   command=lambda: send_command( wnd_info, 'DRIVE L 10000' )
)
wnd_info.frm_buttons_wheels.btn_b = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Backwards",
   command=lambda: send_command( wnd_info, 'DRIVE B 10000' )
)
wnd_info.frm_buttons_wheels.btn_f = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Forwards",
   command=lambda: send_command( wnd_info, 'DRIVE F 10000' )
)
wnd_info.frm_buttons_wheels.btn_r = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Right",
   command=lambda: send_command( wnd_info, 'DRIVE R 10000' )
)
wnd_info.frm_buttons_wheels.btn_rp = Button(
   wnd_info.frm_buttons_wheels,
   text="Drive Right (Hard)",
   command=lambda: send_command( wnd_info, 'DRIVE PR 10000' )
)

wnd_info.frm_buttons = Frame( wnd_info )
wnd_info.frm_buttons.btnClose = Button( 
   wnd_info.frm_buttons, text="Close", command=lambda: wnd_info.quit()
)

# Pack the window controls...
wnd_info.frm_buttons_led.pack( side=TOP )
wnd_info.frm_buttons_eye.pack( side=TOP )
wnd_info.frm_buttons_beep.pack( side=TOP )
wnd_info.frm_buttons_wheels.pack( side=TOP )
wnd_info.frm_buttons.pack( side=TOP )
wnd_info.frm_buttons_led.btn_led_red.pack( side=LEFT )
wnd_info.frm_buttons_led.btn_led_green.pack( side=LEFT )
wnd_info.frm_buttons_led.btn_led_blue.pack( side=LEFT )
wnd_info.frm_buttons_eye.btn_eye_left.pack( side=LEFT )
wnd_info.frm_buttons_eye.btn_eye_right.pack( side=LEFT )
wnd_info.frm_buttons_beep.btn_beep.pack( side=LEFT )
wnd_info.frm_buttons_beep.lbl_beep_freq.pack( side=LEFT )
wnd_info.frm_buttons_beep.spn_beep_freq.pack( side=LEFT )
wnd_info.frm_buttons_beep.lbl_beep_time.pack( side=LEFT )
wnd_info.frm_buttons_beep.spn_beep_time.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_lp.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_l.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_b.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_f.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_r.pack( side=LEFT )
wnd_info.frm_buttons_wheels.btn_rp.pack( side=LEFT )
wnd_info.frm_buttons.btnClose.pack( side=RIGHT )

# Wait for user input...
wnd_info.mainloop()

try:
    wnd_info.destroy()
except:
    pass

