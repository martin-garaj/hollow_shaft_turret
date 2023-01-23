#include <Arduino.h>
#include "pkt_cmd_defs.h"
#include "pfm_cnc.hpp"

class Pkt_pfm
{

private:
    Pfm_cnc *_pfm_cnc;
    bool        cmd_set_target_freq(uint8_t payload_size, uint8_t* payload);
    bool        set_target_delta(uint8_t payload_size, uint8_t* payload);
    uint16_t    arr_to_uint16_t(uint8_t val_0, uint8_t val_1);
    uint32_t    arr_to_uint32_t(uint8_t val_0, uint8_t val_1, 
                                uint8_t val_2, uint8_t val_3);

public:
    Pkt_pfm(Pfm_cnc *pfm_cnc);
    bool        process_command(uint8_t command, uint8_t payload_size, uint8_t* payload);
};