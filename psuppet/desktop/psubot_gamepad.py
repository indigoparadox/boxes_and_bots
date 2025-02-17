#!/usr/bin/python

import pygame, bluetooth

psubot_address = '00:18:a1:12:0f:f9'

pygame.init()

gamepad_buttons = {}
gamepad_axes = {}

gamepad = None
for i in range( 0, pygame.joystick.get_count() ):
   j = pygame.joystick.Joystick( i )
   if 'USB Gamepad' == j.get_name().strip():
      print "Found " + j.get_name() + "."
      gamepad = j
      gamepad.init()

      gamepad_buttons = {
         0: {
            'down': lambda: psubot_command( 'LED RED' ),
            'up': lambda: do_nothing(),
         },
         1: { 
            'down': lambda: psubot_command( 'LED GREEN' ),
            'up': lambda: do_nothing(),
         },
         2: {
            'down': lambda: psubot_command( 'LED BLUE' ),
            'up': lambda: do_nothing(),
         },
         3: {
            'down': lambda: psubot_command( 'BEEP 100 100' ),
            'up': lambda: do_nothing(),
         },
         4: {
            'down': lambda: psubot_command( 'EYE L' ),
            'up': lambda: psubot_command( 'EYE S' ),
         },
         5: {
            'down': lambda: psubot_command( 'EYE R' ),
            'up': lambda: psubot_command( 'EYE S' ),
         },
         6: {
            'down': lambda: psubot_command( 'DRIVE PL' ),
            'up': lambda: psubot_command( 'DRIVE S' ),
         },
         7: {
            'down': lambda: psubot_command( 'DRIVE PR' ),
            'up': lambda: psubot_command( 'DRIVE S' ),
         }
      }

      gamepad_axes = {
         0: {
            -1.0: lambda: do_nothing(),
         },
         1: {
            0.0: lambda: do_nothing(),
         },
         2: {
            0.0: lambda: do_nothing(),
         },
         3: { 
            -1.0: lambda: psubot_command( 'DRIVE L' ),
            1.0: lambda: psubot_command( 'DRIVE R' ),
            0.0: lambda: psubot_command( 'DRIVE S' ),
         },
         4: {
            -1.0: lambda: psubot_command( 'DRIVE F' ),
            1.0: lambda: psubot_command( 'DRIVE B' ),
            0.0: lambda: psubot_command( 'DRIVE S' ),
         },
         5: {
            -1.0: lambda: do_nothing(),
         },
      }


if None == gamepad:
   print "Joystick not found!"
   die()

#try:
btsocket = bluetooth.BluetoothSocket( bluetooth.RFCOMM )
btsocket.connect( (psubot_address, 1) ) 
#except bluetooth.btcommon.BluetoothError:
#   print "Unable to establish connection!"
#   exit( 1 )

print "Connection established. Please press the reset button on the PSUBot."

print btsocket.recv( 1024 )

# TODO: Wait for READY prompt.

print "Ready! Press CTRL-C to exit."

def psubot_command( command_in ):
   global btsocket
   btsocket.send( command_in + "\r" )

def do_nothing():
   pass

try:
   while True:
      event = pygame.event.poll()

      if event.type == pygame.JOYBUTTONDOWN:
         action = None
         try:
            action = gamepad_buttons.get( event.button )['down']
         except KeyError:
            print event.button
         if None != action:
            action()
         else:
            print event.button
      if event.type == pygame.JOYBUTTONUP:
         action = None
         try:
            action = gamepad_buttons.get( event.button )['up']
         except KeyError:
            print event.button
         if None != action:
            action()
         else:
            print event.button
      elif event.type == pygame.JOYAXISMOTION:
         action = gamepad_axes.get( event.axis )
         if None != action:
            action = action.get( event.value )
         if None != action:
            action()
         else:
            print event.value
            print event.axis

except KeyboardInterrupt:
   btsocket.close()
   gamepad.quit()

