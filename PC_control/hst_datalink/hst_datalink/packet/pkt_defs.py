# start & end bytes marking the beginning and end of a packet
START_BYTES = b'\xAA\xBB'
END_BYTES = b'\xCC\xDD'
# definition of command bytes (in order of expected frequency of execution)
CMD_SET_TARGET_FREQ     = bytes.fromhex('01') # set_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction)
CMD_SET_TARGET_DELTA    = bytes.fromhex('02') # set_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta)
CMD_GET_DELTA_STEPS     = bytes.fromhex('03') # get_delta_steps(uint8_t this_pfm)
CMD_GET_IMU_MEASUREMENT = bytes.fromhex('04') # imu.get_measurement()
CMD_SET_ISR_FREQ        = bytes.fromhex('05') # set_isr_freq(uint32_t freq)
CMD_ENABLE_CNC          = bytes.fromhex('06') # enable_cnc(void)
CMD_DISABLE_CNC         = bytes.fromhex('07') # disable_cnc(void)
CMD_SET_DELTA_STEPS     = bytes.fromhex('08') # set_delta_steps(uint8_t this_pfm, int32_t delta_steps)
CMD_STOP                = bytes.fromhex('09') # halts execution and resets memory
CMD_GET_ISR_FREQ        = bytes.fromhex('0A') # uint32_t get_isr_freq(void)
# definition of response
PKT_ACK                 = bytes.fromhex('AA') # acknowledgement sequence
PKT_NACK                = bytes.fromhex('AB') # not-acknowledgement sequence

BYTEORDER = 'little'
PAYLOAD_BYTE_SIZE = 1
COMMAND_BYTE_SIZE = 1