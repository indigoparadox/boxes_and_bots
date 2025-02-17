
CC = msp430-gcc

CFLAGS = -mmcu=msp430g2553 -Wall

BASE_SYSTEM = psubot.o beep.o
INTERACTIVE_SYSTEM = uart.o shell.o

all: test_bluetooth

# test: A general test/debug suite.
test: test.o $(BASE_SYSTEM) $(INTERACTIVE_SYSTEM)
	$(CC) $(CFLAGS) -o $@.out $^

# test_bluetooth: A general test/debug suite designed to operate over the
# 						bluetooth remote serial port.
test_bluetooth: test_bluetooth.o $(BASE_SYSTEM) $(INTERACTIVE_SYSTEM)
	$(CC) $(CFLAGS) -o $@.out $^

# test_eyesense: A simple test that will change the eye color to blue when the
# 					  motor right position sensor is depressed.
test_eyesense: test_eyesense.o $(BASE_SYSTEM)
	$(CC) $(CFLAGS) -o $@.out $^

test_eyemotion: test_eyemotion.o $(BASE_SYSTEM)
	$(CC) $(CFLAGS) -o $@.out $^

test_motors: test_motors.o
	$(CC) $(CFLAGS) -o $@.out $^

# = Generic Utility Definitions =

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

#flash: $(FLASH)
#	mspdebug rf2500 "prog ./$(FLASH).out"

flash:
	mspdebug rf2500 "prog ./test_bluetooth.out"

clean:
	rm *.o
	rm *.out

