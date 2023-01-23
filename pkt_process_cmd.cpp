#include "pkt_cmd_defs.h"
#include "pkt_process_cmd.hpp"
// #include "pfm_registers.h"
// arduino headers
#include <Arduino.h>
// arduino headers
#include <pfm_cnc.hpp>

Pkt_pfm::Pkt_pfm(Pfm_cnc *pfm_cnc){
    // Pfm_cnc *_pfm_cnc = pfm_cnc;
    this->_pfm_cnc = pfm_cnc;
};


union Pkt_uint16_t {
    uint16_t val;
    uint8_t arr[2];
};


uint16_t Pkt_pfm::arr_to_uint16_t(uint8_t val_0, uint8_t val_1){
    union Pkt_uint16_t data;
    data.arr[1] = val_0;
    data.arr[0] = val_1;
    return data.val;
}


union Pkt_uint32_t {
    uint32_t val;
    uint8_t arr[4];
};


uint32_t Pkt_pfm::arr_to_uint32_t(uint8_t val_0, 
                                uint8_t val_1, 
                                uint8_t val_2, 
                                uint8_t val_3){
    union Pkt_uint32_t data;
    data.arr[3] = val_0;
    data.arr[2] = val_1;
    data.arr[1] = val_2;
    data.arr[0] = val_3;
    return data.val;
}


bool Pkt_pfm::cmd_set_target_freq(uint8_t payload_size, uint8_t* payload){
    if(payload_size == 4){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        // translate array[2] of uint8_t into uint16_t
        uint16_t pfm_target_freq = arr_to_uint16_t(payload[1], payload[2]);
        // locate value in payload
        bool pfm_direction = payload[3];

        // execute the command (for every targeted pfm)
        // NOTICE: ISR is ignored to assure synchronized execution among PFMs
        _pfm_cnc->ignore_isr(true);
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                _pfm_cnc->set_target_freq(this_pfm, pfm_target_freq, pfm_direction);
            }
        }
        // retrun true on success
        _pfm_cnc->ignore_isr(false);
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::set_target_delta(uint8_t payload_size, uint8_t* payload){
    // check payload is correct size
    if(payload_size == 7){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        // translate array[2] of uint8_t into uint16_t
        uint16_t pfm_target_freq = arr_to_uint16_t(payload[1], payload[2]);
        // locate value in payload
        int32_t pfm_target_delta = arr_to_uint32_t(payload[3], payload[4], payload[5], payload[6]);

        // execute the command (for every targeted pfm)
        // NOTICE: ISR is ignored to assure synchronized execution among PFMs
        _pfm_cnc->ignore_isr(true);
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                _pfm_cnc->set_target_delta(this_pfm, pfm_target_freq, pfm_target_delta);
            }
        }
        _pfm_cnc->ignore_isr(false);
        // retrun true on success
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::process_command(uint8_t command, uint8_t payload_size, uint8_t* payload){
    switch (command)
    {
        case CMD_SET_TARGET_FREQ:
            // command action here
            return cmd_set_target_freq(payload_size, payload);
            break;
        case CMD_SET_TARGET_DELTA:
            // command action here
            return set_target_delta(payload_size, payload);
            break;
        case CMD_GET_DELTA_STEPS:
            // command action here
            return false;
            break;
        case CMD_SET_ISR_FREQ:
            // command action here
            return false;
            break;
        case CMD_ENABLE_CNC:
            // command action here
            return false;
            break;
        case CMD_DISABLE_CNC:
            // command action here
            return false;
            break;
        case CMD_SET_DELTA_STEPS:
            // command action here
            return false;
            break;
        case CMD_STOP:
            // command action here
            return false;
            break;

        default:
            return false;
    }
}