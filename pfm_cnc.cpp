/* Pulse-Frequency-Modulation for CNC Shield
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

// header 
#include "pfm_cnc.hpp"
// arduino headers
#include <Arduino.h>
#include <avr/io.h>
// CNC shield constants
#include "cnc_shield.h"
// PFM configuration
#include "pfm_config.h"
// internal registers
#include "pfm_registers.h"


Pfm_cnc::Pfm_cnc(void){};

void Pfm_cnc::init_memory(int32_t delta_steps_x, int32_t delta_steps_y, int32_t delta_steps_z){
    for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
    {
        // for all axis
        pfm[this_pfm]._isr_pfm_counter = 0;
        pfm[this_pfm].pfm_control_target_delta = false;
        pfm[this_pfm].pfm_target_freq = INACTIVE_FREQ;
        pfm[this_pfm].pfm_target_delta = 0;
        pfm[this_pfm].pfm_direction = true;

        // X axis
        if(this_pfm==PFM_X)
        {
            pfm[this_pfm]._cnc_shield_step_pin = X_STP_PIN;
            pfm[this_pfm]._cnc_shield_dir_pin = X_DIR_PIN;
            pfm[this_pfm].pfm_delta_steps = delta_steps_x;
            pfm[this_pfm]._bit_flag = PFM_X_FLAG;
        }
        // Y axis
        if(this_pfm==PFM_Y)
        {
            pfm[this_pfm]._cnc_shield_step_pin = Y_STP_PIN;
            pfm[this_pfm]._cnc_shield_dir_pin = Y_DIR_PIN;
            pfm[this_pfm].pfm_delta_steps = delta_steps_y;
            pfm[this_pfm]._bit_flag = PFM_Y_FLAG;
        }
        // Z axis
        if(this_pfm==PFM_Z)
        {
            pfm[this_pfm]._cnc_shield_step_pin = Z_STP_PIN;
            pfm[this_pfm]._cnc_shield_dir_pin = Z_DIR_PIN;
            pfm[this_pfm].pfm_delta_steps = delta_steps_z;
            pfm[this_pfm]._bit_flag = PFM_Z_FLAG;
        }
    }
}

void Pfm_cnc::init_memory(void)
{
    init_memory(0, 0, 0);
}

void Pfm_cnc::init_isr(void)
{
    // _isr_pfm_busy = true;
    noInterrupts();
    TCCR1A = 0;
    TCCR1B = 0; 
    OCR1A = INTERRUPT_COUNTER;
    TCCR1B = (1<<WGM12) | (1<<CS10); // 1<<CS10 -> prescaler 1:1
    TIMSK1 = (1<<OCIE1A); 
    // _isr_pfm_busy = false;
    interrupts(); 
}

void Pfm_cnc::enable_cnc(void)
{
    digitalWrite(SHIELD_EN_PIN, LOW);
}

void Pfm_cnc::disable_cnc(void)
{
    digitalWrite(SHIELD_EN_PIN, HIGH);
}

void Pfm_cnc::init_pins(void)
{
    // set pin directions
    pinMode(SHIELD_EN_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    // disable cnc shield
    disable_cnc();
    // set pins to 
    for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
    {
        pinMode(pfm[this_pfm]._cnc_shield_step_pin, OUTPUT);
        digitalWrite(pfm[this_pfm]._cnc_shield_step_pin, LOW);
        pinMode(pfm[this_pfm]._cnc_shield_dir_pin, OUTPUT);
        digitalWrite(pfm[this_pfm]._cnc_shield_dir_pin, LOW);
    }
}

void Pfm_cnc::set_delta_steps(uint8_t this_pfm, int32_t delta_steps)
{
    // _isr_pfm_busy = true;
    pfm[this_pfm].pfm_delta_steps = delta_steps;
    // _isr_pfm_busy = false;
}

int32_t Pfm_cnc::get_delta_steps(uint8_t this_pfm)
{
    return pfm[this_pfm].pfm_delta_steps;
}

void Pfm_cnc::set_isr_freq(uint16_t freq)
{
    OCR1A = F_CPU/2/freq;
}

uint16_t Pfm_cnc::get_isr_freq(void)
{
    return F_CPU/2/OCR1A;
}

void Pfm_cnc::init(int32_t delta_steps_x, int32_t delta_steps_y, int32_t delta_steps_z)
{
    // set registers
    init_memory(delta_steps_x, delta_steps_y, delta_steps_z);
    // set pins (read from registers)
    init_pins();
    // star interrupt routine
    init_isr();
}

void Pfm_cnc::init(void)
{
    init(0, 0, 0);
}

void Pfm_cnc::set_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction)
{
    // _isr_pfm_busy = true;
    // give control to freq
    pfm[this_pfm].pfm_control_target_delta = false;
    // set frequency and direction
    pfm[this_pfm].pfm_target_freq = pfm_target_freq;
    pfm[this_pfm].pfm_direction = pfm_direction;
    // assure the change takes immediate effect
    // pfm[this_pfm]._isr_pfm_counter=0;
    // _isr_pfm_busy = false;

}

void Pfm_cnc::set_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta)
{

    // _isr_pfm_busy = true;
    // the current pfm_delta_steps is exactly at pfm_target_delta
    if(pfm[this_pfm].pfm_delta_steps == pfm_target_delta) 
    {
        // prevent any movement
        pfm[this_pfm].pfm_target_freq = INACTIVE_FREQ;
        // control back to default
        pfm[this_pfm].pfm_control_target_delta = false;
    }
    // discrepancy 
    else
    {
        // give control to delta 
        pfm[this_pfm].pfm_control_target_delta = true;
        pfm[this_pfm].pfm_target_delta = pfm_target_delta;
        pfm[this_pfm].pfm_target_freq = pfm_target_freq;
        // decide shortest direction
        if(pfm[this_pfm].pfm_delta_steps < pfm_target_delta)
        {
            // set delta and direction
            pfm[this_pfm].pfm_direction = true;
        } 
        if(pfm[this_pfm].pfm_delta_steps > pfm_target_delta)
        {
            // set delta and direction
            pfm[this_pfm].pfm_direction = false;
        } 

        // assure the change takes immediate effect
        pfm[this_pfm]._isr_pfm_counter=0;
    }
    // _isr_pfm_busy = false;
}

bool Pfm_cnc::get_control(uint8_t this_pfm)
{
    return pfm[this_pfm].pfm_control_target_delta;
}

void Pfm_cnc::block_isr(bool ignore)
{
    _isr_pfm_busy = ignore;
}

uint8_t Pfm_cnc::get_bit_flag(uint8_t this_pfm)
{
    return pfm[this_pfm]._bit_flag;
}

uint8_t Pfm_cnc::get_num_pfms(void)
{
    return NUM_PFM;
}