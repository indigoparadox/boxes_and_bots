
#ifndef SHELL_H
#define SHELL_H

/* = Includes = */

#include <msp430.h>

/* = Constants = */

#define SHELL_COMMAND_LEN 20
#define SHELL_ARG_COUNT 5

#define SHELL_STRING_PROMPT "READY\n\r"
#define SHELL_STRING_TOOLONG "TOO LONG\n\r"
#define SHELL_STRING_TOOMANYARGS "TOO MANY ARGS\n\r" 

/* = Structures = */

typedef struct {
   char* command;
   char* helptext;
   void (*handler)( void );
} shell_command;

/* = Macros = */

#define SHELL_COMMANDS_BLOCK_ITEM( command, help, handler ) \
   { command, help, handler }

/* "count" should have the number of system-defined commands added to it in-  *
 * macro.                                                                     */
#define SHELL_COMMANDS_BLOCK_START( count ) \
   int gi_commands_count = (count + 1); \
   shell_command gao_commands[count + 1] = { \
   { "HELP", "DISPLAY THIS LIST.", shell_command_help },

#define SHELL_COMMANDS_BLOCK_END() };

#define SHELL_ENABLE() extern char gac_args[SHELL_ARG_COUNT][SHELL_COMMAND_LEN];

/* = Function Prototypes = */

void shell_init( void );
BOOL shell_strcmp( char*, char* );
void shell_command_help( void );

#endif /* SHELL_H */

