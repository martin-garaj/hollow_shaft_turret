#pragma once 
// import IMU configuration
#include "imu_config.h"
// import MPU6050 object and I2CDev
#include "I2Cdev.h"
#include "MPU9250.h"
// arduino header for Arduino related datatypes
#include <Arduino.h>

// structure blueprint for holding measurements
typedef struct {
    int16_t ax, ay, az;
    int16_t gx, gy, gz;
    int16_t mx, my, mz;
} imu_regs;

// structure holding intermediate values
typedef struct {
    int32_t ax, ay, az;
    int32_t gx, gy, gz;
    int32_t mx, my, mz;
} imu_div_mem;


class Imu
{

private:
    uint8_t _address;
    void * _wire_obj;
    MPU9250 _imu_obj;
    imu_regs _imu_mem[WINDOW_SIZE];
    uint8_t _mem_ptr;

public:
    Imu(uint8_t address);
    bool    initialize(void);
    bool    working_status(void);
    void    perform_measurement(void);
    void    get_measured_data(imu_regs* _imu_regs);

};