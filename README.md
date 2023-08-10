# funhouse_aware

Circuitpython script to gather room sensor data using Adafruit Funhouse and push to MQTT.

## Using

Rename the .dist files, removing the .dist suffix, and enter variables appropriate for your connected sensors/network.

Copy all code to Funhouse with the following adafruit support libraries in lib:

 * adafruit_bitmap_font
 * adafruit_display_text
 * adafruit_minimqtt
 * adafruit_pm25
 * adafruit_scd30.mpy
 * adafruit_sgp30.mpy

## Requirements

 * settings.toml file with values (TBD).
 * BDF font file specified as FONT_BDF in settings.toml.

## Credits

 * Emote balloons by Kenney (https://kenney.nl/assets/emotes-pack).

