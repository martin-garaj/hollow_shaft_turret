#include <stdio.h>
// start & end bytes marking the beginning and end of a packet
#define START_BYTES (int[]){0xAA, 0xBB}
#define END_BYTES  (int[]){0xCC, 0xDD}
// definition of command bytes (in order of expected frequency of execution)
#define CMD_SET_TARGET_FREQ     0x01 // set_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction)
#define CMD_SET_TARGET_DELTA    0x02 // set_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta)
#define CMD_GET_DELTA_STEPS     0x03 // get_delta_steps(uint8_t this_pfm)
#define CMD_GET_IMU_MEASUREMENT 0x04 // imu.get_measurement()
#define CMD_SET_ISR_FREQ        0x05 // set_isr_freq(uint32_t freq)
#define CMD_ENABLE_CNC          0x06 // enable_cnc(void)
#define CMD_DISABLE_CNC         0x07 // disable_cnc(void)
#define CMD_SET_DELTA_STEPS     0x08 // set_delta_steps(uint8_t this_pfm, int32_t delta_steps)
#define CMD_STOP                0x09 // halts execution and resets memory
#define CMD_GET_ISR_FREQ        0x0A // uint32_t get_isr_freq(void)
// definition of response
#define PKT_ACK                 0xAA // acknowledgement sequence
#define PKT_NACK                0xAB // not-acknowledgement sequence