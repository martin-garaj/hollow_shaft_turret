/* Pulse-Frequency-Modulation Iterrupt Service Routine
 * 
 * This file defines the operation of PFM for controling 3-axis CNC Shield.
 * 
 * Functions defined in this file include:
 *      void    init_pfm_vars(int32_t pfm_delta_steps_x, int32_t pfm_delta_steps_y, int32_t pfm_delta_steps_z)
 *      void    set_pfm_delta_steps(uint8_t this_pfm, int32_t pfm_delta_steps_x)
 *      int32_t get_pfm_delta_steps(uint8_t this_pfm)
 *      void    init_pfm_isr(void)
 *      void    set_pfm_freq(uint32_t freq)
 *              ISR(TIMER1_COMPA_vect)
 *      void    init_cnc_pins(void)
 *      void    set_cnc_enable(void)
 *      void    set_cnc_disable(void)
 *      void    setup_pfm(int32_t pfm_delta_steps_x, int32_t pfm_delta_steps_y, int32_t pfm_delta_steps_z)
 *      void    setup_pfm(void)
 *      void    control_pfm_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction)
 *      void    control_pfm_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta)
 * 
 * Variables defined in this file:
 *      static pfm_vars pfm[NUM_PFM]
 *      static volatile uint8_t _isr_pfm_busy
 * 
*/

// #pragma once
// ensure this library description is only included once
// #ifndef cnc_pfm_isr
// #define cnc_pfm_isr

// import Arduino headers
#include <Arduino.h>
// import constants regardin CNC Shield
#include "cnc_shield.h"
// import constants regardin CNC Shield
#include "pfm_config.h"
// import structure with pfm registers
#include "pfm_registers.h"

volatile pfm_regs pfm[NUM_PFM];

volatile uint8_t _isr_pfm_busy = false;


// Pulse-Frequency-Modulation Interrupt Service Routine (PFM ISR)
ISR(TIMER1_COMPA_vect)
{
    /*
    * Function: ISR
    * ----------------------------
    *   Interrupt-Service-Routine of Pulse-Frequency-Modulation
    */
    if (_isr_pfm_busy) { return; } // The busy-flag is used to avoid reentering this interrupt
    _isr_pfm_busy = true;

    // digitalWrite(LED_PIN, ~digitalRead(LED_PIN));

    for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
    {
        // default state
        if(pfm[this_pfm]._isr_pfm_counter==0 || pfm[this_pfm]._isr_pfm_counter==INACTIVE_FREQ)
        {
            // reset counter
            pfm[this_pfm]._isr_pfm_counter=0;
            // reset/default step signal
            digitalWrite(pfm[this_pfm]._cnc_shield_step_pin, LOW);
            // change direction when the step pin is reset
            digitalWrite(pfm[this_pfm]._cnc_shield_dir_pin, pfm[this_pfm].pfm_direction);

            // debug only
            digitalWrite(LED_PIN, LOW);
        }

        // increment counter 
        pfm[this_pfm]._isr_pfm_counter++;

        // produce signal
        if(pfm[this_pfm]._isr_pfm_counter>pfm[this_pfm].pfm_target_freq)
        {
            // reset counter
            pfm[this_pfm]._isr_pfm_counter=0;
            // assert signal
            digitalWrite(pfm[this_pfm]._cnc_shield_step_pin, HIGH);
            // update step counter (add/subtract bool)
            if(pfm[this_pfm].pfm_direction)
            {
                pfm[this_pfm].pfm_delta_steps++;
            }
            else
            {
                pfm[this_pfm].pfm_delta_steps--;
            }

            // debug only
            digitalWrite(LED_PIN, HIGH);            
        }

        // run until delta steps reached
        if(pfm[this_pfm].pfm_control_target_delta)
        {
            //if target delta steps are reached
            if(pfm[this_pfm].pfm_delta_steps==pfm[this_pfm].pfm_target_delta)
            {
                // set speed to 0
                pfm[this_pfm].pfm_target_freq = INACTIVE_FREQ;
                // control back to default
                pfm[this_pfm].pfm_control_target_delta = false;
            }
        }
    }

    // reset busy flag
    _isr_pfm_busy = false;

}


// #endif
