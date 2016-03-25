
#ifndef UART_H
#define UART_H

#include <msp430g2553.h>
#include <string.h>

#ifdef UART_LED
#define LED BIT0
#endif /* UART_LED */

#define RXD BIT1
#define TXD BIT2

void uart_init( void );
unsigned char uart_getc( void );
void uart_gets( char* buffer, int length );
void uart_putc( const unsigned char c );
void uart_puts( const char *str );

#endif /* UART_H */

