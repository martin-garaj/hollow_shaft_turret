#include "pkt_cmd_defs.h"
#include "pkt_process_cmd.hpp"
// #include "pfm_registers.h"
// arduino headers
#include <Arduino.h>
// Pulse Frequency Modulation
#include <pfm_cnc.hpp>
// Inertial Measurement Unit
#include <pfm_cnc.hpp>


Pkt_pfm::Pkt_pfm(Pfm_cnc *pfm_cnc, Imu *imu){
    // Pfm_cnc *_pfm_cnc = pfm_cnc;
    this->_pfm_cnc = pfm_cnc;
    this->_imu = imu;
    // imu_regs _imu_meas;
};


union Pkt_uint16_t {
    uint16_t val;
    uint8_t arr[2];
};


uint16_t Pkt_pfm::arr_to_uint16_t(uint8_t val_0, uint8_t val_1){
    union Pkt_uint16_t data;
    data.arr[0] = val_0;
    data.arr[1] = val_1;
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
    data.arr[0] = val_0;
    data.arr[1] = val_1;
    data.arr[2] = val_2;
    data.arr[3] = val_3;
    return data.val;
}


void Pkt_pfm::uint16_t_to_arr(uint16_t val, 
                            uint8_t* arr){
    union Pkt_uint16_t data;
    data.val = val;
    for(uint8_t ii=0; ii<2; ii++){
        *(arr+ii) = data.arr[ii];
    }
}


void Pkt_pfm::uint32_t_to_arr(uint32_t val, 
                            uint8_t* arr){
    union Pkt_uint32_t data;
    data.val = val;
    for(uint8_t ii=0; ii<4; ii++){
        *(arr+ii) = data.arr[ii];
    }
}


bool Pkt_pfm::cmd_set_target_freq(uint8_t payload_size, uint8_t* payload){
    if(payload_size == 4){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        // translate array[2] of uint8_t into uint16_t
        // NOTICE: order of bytes in payload is from low to high
        uint16_t pfm_target_freq = arr_to_uint16_t(payload[2], payload[1]);
        // locate value in payload
        bool pfm_direction = payload[3];

        // execute the command (for every targeted pfm)
        // NOTICE: ISR is ignored to assure synchronized execution among PFMs
        _pfm_cnc->block_isr(true);
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                _pfm_cnc->set_target_freq(this_pfm, pfm_target_freq, pfm_direction);
            }
        }
        // retrun true on success
        _pfm_cnc->block_isr(false);
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::cmd_set_target_delta(uint8_t payload_size, uint8_t* payload){
    // check payload is correct size
    if(payload_size == 7){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        // translate array[2] of uint8_t into uint16_t
        // NOTICE: order of bytes in payload is from low to high
        uint16_t pfm_target_freq = arr_to_uint16_t(payload[2], payload[1]);
        // locate value in payload
        // NOTICE: order of bytes in payload is from low to high
        int32_t pfm_target_delta = arr_to_uint32_t(payload[6], payload[5], payload[4], payload[3]);

        // execute the command (for every targeted pfm)
        // NOTICE: ISR is ignored to assure synchronized execution among PFMs
        _pfm_cnc->block_isr(true);
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                _pfm_cnc->set_target_delta(this_pfm, pfm_target_freq, pfm_target_delta);
            }
        }
        _pfm_cnc->block_isr(false);
        // retrun true on success
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::cmd_get_delta_steps(uint8_t payload_size, uint8_t* payload, uint16_t* return_array_size, uint8_t* return_array){
    // check payload is correct size
    if(payload_size == 1){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                uint32_t_to_arr(uint32_t(_pfm_cnc->get_delta_steps(this_pfm)), 
                                return_array);
            }
        }
        // retrun true on success
        *return_array_size = 4;
        return true;
    }else{
        // retrun false when something is wrong
        *return_array_size = 0;
        return false;
    }
}


bool Pkt_pfm::cmd_get_imu_measurement(uint8_t payload_size, uint16_t* return_array_size, uint8_t* return_array){
    // check payload is correct size
    if(payload_size == 0){
        // locate value in payload
        _imu->get_measured_data(&this->_imu_meas);
        // fit measured data into return_array
        uint16_t_to_arr(uint16_t(_imu_meas.ax), return_array+ 0);
        uint16_t_to_arr(uint16_t(_imu_meas.ay), return_array+ 2);
        uint16_t_to_arr(uint16_t(_imu_meas.az), return_array+ 4);
        uint16_t_to_arr(uint16_t(_imu_meas.gx), return_array+ 6);
        uint16_t_to_arr(uint16_t(_imu_meas.gy), return_array+ 8);
        uint16_t_to_arr(uint16_t(_imu_meas.gz), return_array+10);
        uint16_t_to_arr(uint16_t(_imu_meas.mx), return_array+12);
        uint16_t_to_arr(uint16_t(_imu_meas.my), return_array+14);
        uint16_t_to_arr(uint16_t(_imu_meas.mz), return_array+16);
        // retrun true on success
        *return_array_size = 18;
        return true;
    }else{
        // retrun false when something is wrong
        *return_array_size = 0;
        return false;
    }
}


bool Pkt_pfm::cmd_set_isr_freq(uint8_t payload_size, uint8_t* payload){
    // check payload is correct size
    if(payload_size == 2){
        // locate value in payload 
        // NOTICE: order of bytes in payload is from low to high
        uint16_t frequency = arr_to_uint16_t(payload[1], 
                                            payload[0]);

        // frequency = uint16_t(0x0C80);
        _pfm_cnc->set_isr_freq(frequency);
        // retrun true on success
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::cmd_get_isr_freq(uint8_t payload_size, uint16_t* return_array_size, uint8_t* return_array){
    // check payload is correct size
    if(payload_size == 0){
        //  
        return_array[3] = 0x00;
        return_array[2] = 0x00;
        uint16_t_to_arr(uint16_t(_pfm_cnc->get_isr_freq()), 
                                        return_array);
        // retrun true on success
        *return_array_size = 4;
        return true;
    }else{
        // retrun false when something is wrong
        *return_array_size = 0;
        return false;
    }
}


bool Pkt_pfm::cmd_enable_cnc(uint8_t payload_size){
    // check payload is correct size
    if(payload_size == 0){
        // locate value in payload
        _pfm_cnc->enable_cnc();
        _pfm_cnc->block_isr(false);
        // retrun true on success
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::cmd_disable_cnc(uint8_t payload_size){
    // check payload is correct size
    if(payload_size == 0){
        // locate value in payload
        _pfm_cnc->block_isr(true);
        _pfm_cnc->disable_cnc();
        // retrun true on success
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::cmd_set_delta_steps(uint8_t payload_size, uint8_t* payload){
    if(payload_size == 5){
        // locate value in payload
        uint8_t bit_flags_target_pfm = payload[0];
        // translate array[2] of uint8_t into uint16_t
        uint32_t pfm_delta_steps = arr_to_uint32_t(payload[3], 
                                                    payload[2], 
                                                    payload[1], 
                                                    payload[0]);

        // execute the command (for every targeted pfm)
        // NOTICE: ISR is ignored to assure synchronized execution among PFMs
        _pfm_cnc->block_isr(true);
        for(uint8_t this_pfm=0; this_pfm<NUM_PFM; this_pfm++)
        {
            // if flag==true, then execute command for this_pmf
            if( (bit_flags_target_pfm & _pfm_cnc->get_bit_flag(this_pfm))){
                _pfm_cnc->set_delta_steps(this_pfm, pfm_delta_steps);
            }
        }
        // retrun true on success
        _pfm_cnc->block_isr(false);
        return true;
    }else{
        // retrun false when something is wrong
        return false;
    }
}


bool Pkt_pfm::process_command(uint8_t command, uint8_t payload_size, uint8_t* payload, uint16_t* return_array_size, uint8_t* return_array){
    switch (command)
    {
        case CMD_SET_TARGET_FREQ:
            *return_array_size = 0;
            return cmd_set_target_freq(payload_size, payload);
            break;
        case CMD_SET_TARGET_DELTA:
            *return_array_size = 0;
            return cmd_set_target_delta(payload_size, payload);
            break;
        case CMD_GET_DELTA_STEPS:
            return cmd_get_delta_steps(payload_size, payload, return_array_size, return_array);
            break;
        case CMD_GET_IMU_MEASUREMENT:
            return cmd_get_imu_measurement(payload_size, return_array_size, return_array);
            break;
        case CMD_SET_ISR_FREQ:
            *return_array_size = 0;
            return cmd_set_isr_freq(payload_size, payload);
            break;
        case CMD_ENABLE_CNC:
            *return_array_size = 0;
            return cmd_enable_cnc(payload_size);
            break;
        case CMD_DISABLE_CNC:
            *return_array_size = 0;
            return cmd_disable_cnc(payload_size);
            break;
        case CMD_SET_DELTA_STEPS:
            *return_array_size = 0;
            return cmd_set_delta_steps(payload_size, payload);
            break;
        case CMD_GET_ISR_FREQ:
            return cmd_get_isr_freq(payload_size, return_array_size, return_array);
            break;
        // case CMD_STOP:
        //     // command action here
        //     return false;
        //     break;

        default:
            return false;
    }
}