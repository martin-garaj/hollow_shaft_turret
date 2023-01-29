
#pragma once
#include <Arduino.h>
#include "pfm_config.h"
class Pfm_cnc
{

private:
    void        init_memory(int32_t delta_steps_x, int32_t delta_steps_y, int32_t delta_steps_z);
    void        init_memory(void);
    void        init_isr(void);
    void        init_pins(void);

public:
    Pfm_cnc(void);
    // void    init_memory(int32_t delta_steps_x, int32_t delta_steps_y, int32_t delta_steps_z);
    // void    init_memory(void);
    // void    init_isr(void);
    void        enable_cnc(void);
    void        disable_cnc(void);
    // void    init_pins(void);
    void        set_delta_steps(uint8_t this_pfm, int32_t delta_steps);
    int32_t     get_delta_steps(uint8_t this_pfm);
    void        set_isr_freq(uint16_t freq);
    uint16_t    get_isr_freq(void);
    void        init(int32_t pfm_delta_steps_x, int32_t pfm_delta_steps_y, int32_t pfm_delta_steps_z);
    void        init(void);
    void        set_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction);
    void        set_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta);
    bool        get_control(uint8_t this_pfm);
    void        block_isr(bool ignore);
    uint8_t     get_bit_flag(uint8_t this_pfm);
    uint8_t     get_num_pfms(void);
};