

#include "imu.hpp"


Imu::Imu(uint8_t address=MPU9250_DEFAULT_ADDRESS){
    // keep wire object
    this->_address = address;
    this->_imu_obj = MPU9250(address);
    this->_mem_ptr = 0;
    // this->_imu_mem = imu_regs[WINDOW_SIZE];
};

bool Imu::initialize(void){
    this->_imu_obj.initialize();
    return true;
}


bool Imu::working_status(void){
    return this->_imu_obj.testConnection();
}

void Imu::perform_measurement(void){
    // increment rotary counter
    this->_mem_ptr++;
    // rotate counter
    if(this->_mem_ptr >= WINDOW_SIZE){
        this->_mem_ptr = 0;
    };
    // get new data
    this->_imu_obj.getMotion9(
            &this->_imu_mem[this->_mem_ptr].ax, &this->_imu_mem[this->_mem_ptr].ay, &this->_imu_mem[this->_mem_ptr].az, 
            &this->_imu_mem[this->_mem_ptr].gx, &this->_imu_mem[this->_mem_ptr].gy, &this->_imu_mem[this->_mem_ptr].gz, 
            &this->_imu_mem[this->_mem_ptr].mx, &this->_imu_mem[this->_mem_ptr].my, &this->_imu_mem[this->_mem_ptr].mz);
}


void Imu::get_measured_data(imu_regs* _imu_result){

    // init intermediate structure
    imu_div_mem _inter_mem;  
    _inter_mem.ax = 0;
    _inter_mem.ay = 0;
    _inter_mem.az = 0;
    _inter_mem.gx = 0;
    _inter_mem.gy = 0;
    _inter_mem.gz = 0;
    _inter_mem.mx = 0;
    _inter_mem.my = 0;
    _inter_mem.mz = 0;

    // accumulate measurements
    for(uint8_t ii=0; ii<WINDOW_SIZE; ii++){
        _inter_mem.ax += this->_imu_mem[ii].ax;
        _inter_mem.ay += this->_imu_mem[ii].ay;
        _inter_mem.az += this->_imu_mem[ii].az;
        _inter_mem.gx += this->_imu_mem[ii].gx;
        _inter_mem.gy += this->_imu_mem[ii].gy;
        _inter_mem.gz += this->_imu_mem[ii].gz;
        _inter_mem.mx += this->_imu_mem[ii].mx;
        _inter_mem.my += this->_imu_mem[ii].my;
        _inter_mem.mz += this->_imu_mem[ii].mz;
    };

    // division by shifting
    _imu_result->ax = int16_t(_inter_mem.ax >> LOG2_WINDOW_SIZE);
    _imu_result->ay = int16_t(_inter_mem.ay >> LOG2_WINDOW_SIZE);
    _imu_result->az = int16_t(_inter_mem.az >> LOG2_WINDOW_SIZE);
    _imu_result->gx = int16_t(_inter_mem.gx >> LOG2_WINDOW_SIZE);
    _imu_result->gy = int16_t(_inter_mem.gy >> LOG2_WINDOW_SIZE);
    _imu_result->gz = int16_t(_inter_mem.gz >> LOG2_WINDOW_SIZE);
    _imu_result->mx = int16_t(_inter_mem.mx >> LOG2_WINDOW_SIZE);
    _imu_result->my = int16_t(_inter_mem.my >> LOG2_WINDOW_SIZE);
    _imu_result->mz = int16_t(_inter_mem.mz >> LOG2_WINDOW_SIZE);
}
