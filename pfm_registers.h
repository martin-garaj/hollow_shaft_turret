#pragma once 
// arduino headers
#include <Arduino.h> 
// PFM configuration
#include "pfm_config.h"

// declare structure representing single PFM
typedef struct {
    // internal - ISR variables
    // interrupt routine counter
    volatile uint16_t _isr_pfm_counter;
    // cnc shield pin for steps
    volatile uint8_t  _cnc_shield_step_pin;
    // cnc shield pin for direction
    volatile uint8_t  _cnc_shield_dir_pin;

    // internal - other
    // binary flag
    volatile uint8_t _bit_flag;

    // input - read/write only
    // true: target delta, false: target frequency
    volatile bool pfm_control_target_delta;
    // frequency of PFM if pfm_control_target_delta[X]=false
    volatile uint16_t pfm_target_freq;
    // target delta if if pfm_control_target_delta[X]=true
    volatile int32_t pfm_target_delta;
    // direction 
    volatile bool pfm_direction;

    // output - read only
    // number of steps from default position
    volatile int32_t pfm_delta_steps;
} pfm_regs;

extern volatile pfm_regs pfm[NUM_PFM];

extern volatile uint8_t _isr_pfm_busy;