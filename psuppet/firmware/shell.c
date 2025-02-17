
/* TODO: If we support other I/O methods than the UART (like SPI or I2C), how *
 *       should we handle them here? Maybe an if/elif defined preprocessor    *
 *       block to find the correct header?                                    */
#include "uart.h"

#include "shell.h"

#include <stdint.h>

extern shell_command gao_commands[];
extern int gi_commands_count;

char gac_args[SHELL_ARG_COUNT][SHELL_COMMAND_LEN];

void shell_init( void ) {
   /* Enable UART RX interrupt. */
   IE2 |= UCA0RXIE;

   uart_echo( "\n\r" );
   uart_echo( SHELL_STRING_PROMPT );
}

BOOL shell_strcmp( char* pc_string1_in, char* pc_string2_in ) {
   char* pc_iter_1 = pc_string1_in,
      * pc_iter_2 = pc_string2_in;
   
   do {
      if( *pc_iter_1 != *pc_iter_2 ) {
         return FALSE;
      }

      pc_iter_1++;
      pc_iter_2++;
   } while( NULL != *pc_iter_1 && NULL != *pc_iter_2 );

   return TRUE;
}

void shell_command_help( void ) {
   uint8_t i;

   for( i = 0 ; i < gi_commands_count ; i++ ) {
      uart_echo( gao_commands[i].command );
      uart_echo( "\t" );
      uart_echo( gao_commands[i].helptext );
      uart_echo( "\r\n" );
   }
}

#pragma vector=USCIAB0RX_VECTOR
__interrupt void shell_uart0_isr( void ) {
   uint8_t i, j;
   static uint8_t i_command_buffer_pos = 0,
      i_arg_buffer_pos = 0,
      i_arg_buffer_sel = 0;
   static char ac_command_last[SHELL_COMMAND_LEN] = { '\0' };

   if( '\r' == UCA0RXBUF ) {
      /* "Enter" was received, so process the last command. */

      uart_echo( "\n\r" );

      for( i = 0 ; i < SHELL_ARG_COUNT ; i++ ) {
         for( j = 0 ; j < SHELL_COMMAND_LEN ; j++ ) {
            gac_args[i][j] = '\0';
         }
      }

      /* Parse out the arguments from the command line. */
      i_arg_buffer_pos = 0;
      i_arg_buffer_sel = 0;
      i_command_buffer_pos = 0;
      while( NULL != ac_command_last[i_command_buffer_pos] ) {
         if( ' ' == ac_command_last[i_command_buffer_pos] ) {
            /* Move on to the next argument buffer if we can. */
            if( SHELL_ARG_COUNT <= (i_arg_buffer_sel + 1) ) {
               /* TODO: Do we need to handle this situation if it can't occur *
                *       with the selected variable sizing?                    */
               uart_echo( SHELL_STRING_TOOMANYARGS );
               break;
            } else {
               i_arg_buffer_sel++;
               i_arg_buffer_pos = 0;
            }
         } else {
            /* Add the next character to the current argument buffer. */
            /* TODO: Slim down the RAM used for each argument buffer safely. */
            gac_args[i_arg_buffer_sel][i_arg_buffer_pos] =
               ac_command_last[i_command_buffer_pos];
            i_arg_buffer_pos++;
         }

         i_command_buffer_pos++;
      }

      /* Execute the client program's command handler, if there is one. */
      for( i = 0 ; i < gi_commands_count ; i++ ) {
         if( shell_strcmp( gao_commands[i].command, ac_command_last ) ) {
            gao_commands[i].handler();
         }
      }

      for( i = 0 ; i < SHELL_COMMAND_LEN ; i++ ) {
         ac_command_last[i] = '\0';
      }
      i_command_buffer_pos = 0;
      uart_echo( SHELL_STRING_PROMPT );

   } else if( 0x7f == UCA0RXBUF ) {
      /* Delete character. */
      if( 0 < i_command_buffer_pos ) {
         uart_putc( 0x08 ); /* Backspace */
         i_command_buffer_pos--;
      }

   } else if( '\t' == UCA0RXBUF ) {
      /* Tab character. */
      uart_echo( "TAB" );

   } else if( '\r' != UCA0RXBUF ) {
      if( i_command_buffer_pos <= (SHELL_COMMAND_LEN - 1) ) {
         /* Add the character to the current buffer and echo it back. */
         ac_command_last[i_command_buffer_pos] = UCA0RXBUF;
         i_command_buffer_pos++;
         uart_putc( UCA0RXBUF );
      } else {
         /* The command is too long, so reset. */
         i_command_buffer_pos = 0;
         uart_echo( SHELL_STRING_TOOLONG );
      }
   }
}

