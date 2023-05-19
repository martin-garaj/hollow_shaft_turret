# definition of command bytes (in order of expected frequency of execution)
PKT_ACK     = bytes.fromhex('AA') # set_target_freq(uint8_t this_pfm, uint16_t pfm_target_freq, bool pfm_direction)
PKT_NACK    = bytes.fromhex('AB') # set_target_delta(uint8_t this_pfm, uint16_t pfm_target_freq, int32_t pfm_target_delta)