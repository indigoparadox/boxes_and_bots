
#ifndef PSUBOT_H
#define PSUBOT_H

#include <msp430.h>

/* = Types = */

typedef int BOOL;

/* = Constants = */

#ifndef NULL
#define NULL 0
#endif /* NULL */

#ifndef TRUE
#define TRUE 1
#endif /* TRUE */

#ifndef FALSE
#define FALSE 0
#endif /* FALSE */

/* #define WHEELS_DIRECTION_FORWARD       1
#define WHEELS_DIRECTION_REVERSE       2
#define WHEELS_DIRECTION_RIGHT         3
#define WHEELS_DIRECTION_RIGHT_PIVOT   4
#define WHEELS_DIRECTION_LEFT          5
#define WHEELS_DIRECTION_LEFT_PIVOT    6 */

/* IO Ports: Port 1 */

#define ILED      BIT0

#define EYE_SENSE BIT3

/* Eye directions are from the robot's point of view. */
#define EYE_R     BIT4
#define EYE_L     BIT5

#define WHEEL_R_F BIT7

/* IO Ports: Port 2 */

#define LED_RED   BIT0
#define LED_GREEN BIT1
#define LED_BLUE  BIT2

#define WHEEL_R_R BIT5
#define WHEEL_L_R BIT4
#define WHEEL_L_F BIT3

typedef enum {
   DRIVING_STOPPED,
   DRIVING_FORWARD,
   DRIVING_REVERSE,
   DRIVING_RIGHT,
   DRIVING_LEFT,
   DRIVING_RIGHT_PIVOT,
   DRIVING_LEFT_PIVOT
} DRIVING_DIR;

typedef enum {
   EYE_RIGHT,
   EYE_LEFT,
   EYE_STOPPED
} EYE_DIR;

/* Configuration */

#define EYE_MAX_CYCLES_L 10500
#define EYE_MAX_LOOPS_R 40000

/* = Function Prototypes = */

void psubot_init( void );
void psubot_button_enable( void );
void psubot_eye_enable( void );
void psubot_wheels_enable( void );
void psubot_eye_pos( int );
void psubot_eye_move( EYE_DIR );
void psubot_wheel_drive( DRIVING_DIR );
void psubot_wait( void );
void psubot_halt( void );

#endif /* PSUBOT_H */

