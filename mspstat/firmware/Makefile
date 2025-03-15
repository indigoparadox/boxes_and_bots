
DEPS=envsensor.o uart.o esp8266.o DHT11_LIB.o

CFLAGS=-mmcu=msp430g2553 -Wall
CC=msp430-gcc

all: envsensor

envsensor: $(DEPS)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

.PHONY: clean flash

flash:
	mspdebug rf2500 "prog envsensor"

clean:
	rm -f *.o ; rm -f dep/*.o ; rm envsensor

