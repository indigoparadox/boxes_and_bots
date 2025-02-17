
#ifndef BEEP_H
#define BEEP_H

/* = Constants = */

#define SPEAKER   BIT6

typedef enum {
   BEEP_NULL = 0,
   BEEP_C = 76,
   BEEP_D = 67,
   BEEP_E = 60,
   BEEP_F = 56,
   BEEP_G = 50,
   BEEP_A = 44,
   BEEP_B = 32
} BEEP_NOTE;

/* = Function Prototypes = */

void beep_init( void );
void beep( int, int );

#endif /* BEEP_H */

