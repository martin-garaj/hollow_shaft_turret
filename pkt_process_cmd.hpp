#include <Arduino.h>
#include "pkt_cmd_defs.h"
#include "pfm_cnc.hpp"
#include "imu.hpp"
class Pkt_pfm
{

private:
    Pfm_cnc*    _pfm_cnc;
    Imu*        _imu;
    imu_regs    _imu_meas;
    bool        cmd_set_target_freq(    uint8_t payload_size,   uint8_t* payload                            );
    bool        cmd_set_target_delta(   uint8_t payload_size,   uint8_t* payload                            );
    bool        cmd_get_delta_steps(    uint8_t payload_size,   uint8_t* payload,   uint16_t* return_array_size,    uint8_t* return_array   );
    bool        cmd_set_isr_freq(       uint8_t payload_size,   uint8_t* payload                            );
    bool        cmd_get_imu_measurement(uint8_t payload_size,                       uint16_t* return_array_size,    uint8_t* return_array   );
    bool        cmd_get_isr_freq(       uint8_t payload_size,                       uint16_t* return_array_size,    uint8_t* return_array   );
    bool        cmd_enable_cnc(         uint8_t payload_size                                                );
    bool        cmd_disable_cnc(        uint8_t payload_size                                                );
    bool        cmd_set_delta_steps(    uint8_t payload_size,   uint8_t* payload                            );
    uint16_t    arr_to_uint16_t(        uint8_t val_0, uint8_t val_1    );
    uint32_t    arr_to_uint32_t(        uint8_t val_0, uint8_t val_1, 
                                        uint8_t val_2, uint8_t val_3    );
    void        uint16_t_to_arr(        uint16_t val, uint8_t* arr      );
    void        uint32_t_to_arr(        uint32_t val, uint8_t* arr      );
public:
    Pkt_pfm(Pfm_cnc* pfm_cnc, Imu* imu);
    bool        process_command(uint8_t command, uint8_t payload_size, uint8_t* payload, uint16_t* return_array_size, uint8_t* return_array);
};