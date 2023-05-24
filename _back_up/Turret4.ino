// Continue writing the Command functions (translating packets into commands)
// Then implement SerialTransfer and pySerialTransfer (already tested)
// Lastly, work on the main loop, integrate sensors, 
// serial communication and control into several high level commands.


// Below code is tested and works, try to connect motors next time.
#include "pfm_cnc.hpp"
#include "pfm_isr.h"
#include "imu.hpp"
#include "pkt_cmd_defs.h"
#include "pkt_process_cmd.hpp"
// Arduino Wire library is required if I2Cdev I2CDEV_ARDUINO_WIRE implementation
// is used in I2Cdev.h
#include "Wire.h"
// I2Cdev and MPU6050 must be installed as libraries, or else the .cpp/.h files
// for both classes must be in the include path of your project
#include "I2Cdev.h"
#include "MPU6050.h"

Imu imu(MPU9250_DEFAULT_ADDRESS);
Pfm_cnc Pfm;
Pkt_pfm Pkt(&Pfm, &imu);

//############################################################################//
//                                 CONSTANTS                                  //
//############################################################################//
// Define the maximum size of the serial input buffer
#define SERIAL_BUFFER_SIZE 128

//############################################################################//
//                                 FUNCTIONS                                  //
//############################################################################//
/**
 * The encode_message function prepares a message by adding start bytes, payload size, payload data, and end bytes to a message array.
 *
 * @param payload: This is a pointer to an array of 8-bit unsigned integers (bytes). This array holds the actual data that needs to be sent.
 * @param payload_size: This is an 8-bit unsigned integer representing the size of the payload data. It specifies how many bytes are in the payload.
 * @param message: This is a pointer to an array of 8-bit unsigned integers. This array will hold the final encoded message, including start bytes, payload size, payload data, and end bytes.
 * 
 * The function starts by setting the first two bytes of the message array to the start bytes (START_BYTES). The third byte is set to the size of the payload.
 * The function then copies the payload data into the message array, starting at the fourth byte. 
 * After the payload, the function sets two end bytes (END_BYTES).
 * 
 * @return: The function returns a 16-bit unsigned integer representing the total size of the message (start bytes + payload size byte + payload data + end bytes).
 */
uint16_t encode_message(uint8_t *payload, uint8_t payload_size, uint8_t *message) {
    // Start bytes
    message[0] = START_BYTES[0];
    message[1] = START_BYTES[1];
    // Payload size (1 byte)
    message[2] = payload_size;
    // Payload
    memcpy(&message[3], payload, payload_size);
    // Ending bytes
    message[3+payload_size] = END_BYTES[0];
    message[4+payload_size] = END_BYTES[1];
    // return 
    return payload_size+5;
}

/**
 * The decode_message function decodes a message by finding the start bytes, reading the payload size, extracting the payload data, and checking for the correct end bytes.
 *
 * @param data: This is a pointer to an array of 8-bit unsigned integers (bytes). This array holds the data that needs to be decoded.
 * @param data_length: This is a 16-bit unsigned integer representing the size of the data array. It specifies how many bytes are in the data array.
 * @param payload: This is a pointer to an array of 8-bit unsigned integers. This array will hold the payload data extracted from the data array.
 * 
 * The function starts by finding the start bytes (START_BYTES) in the data array. If the start bytes are not found, the function returns 0 (invalid message).
 * After finding the start bytes, the function finds the end bytes (END_BYTES). If the end bytes are not found, the function returns 0 (invalid message).
 * The function then reads the payload size (1 byte) and checks if it matches the actual payload size. If it doesn't, the function returns 0 (invalid message).
 * If the payload size is greater than 0, the function copies the payload data into the payload array.
 * 
 * @return: The function returns a 16-bit unsigned integer representing the total size of the message (start bytes + payload size byte + payload data + end bytes). If the message is invalid, the function returns 0.
 */
uint16_t decode_message(uint8_t *data, uint16_t data_length, uint8_t *payload) {

    uint16_t start_index = 0;
    while (start_index < data_length-1) {
        // Find the start bytes
        if (data[start_index] == START_BYTES[0] && data[start_index+1] == START_BYTES[1]) {
            break;
        }
        start_index++;
    }
    if (start_index >= data_length-1) {
        // Start bytes not found, invalid message
        return 0;
    }
    uint16_t end_index = start_index+2;
    while (end_index < data_length-1) {
        // Find the ending bytes
        if (data[end_index] == END_BYTES[0] && data[end_index+1] == END_BYTES[1]) {
            break;
        }
        end_index++;
    }
    if (end_index >= data_length-1) {
        // Ending bytes not found, invalid message
        return 0;
    }
    // Extract the payload size (1 byte)
    uint8_t payload_size = data[start_index+2];
    if (end_index-start_index-3 != payload_size) {
        // Payload size does not match actual payload size, invalid message
        return 0;
    }
    if (payload_size > 0) {
        memcpy(payload, data+start_index+3, payload_size);
    }
    // Return the total length of the message, including start and ending bytes
    return end_index-start_index+2;
}

//############################################################################//
//                              GLOBAL VARIABLES                              //
//############################################################################//
bool imu_wokring;
// keeps raw incomming serial trafic
uint8_t serial_buffer[SERIAL_BUFFER_SIZE];
uint16_t serial_buffer_length = 0;
// buffer of a message to be sent
uint8_t message[SERIAL_BUFFER_SIZE];
// received packet
uint8_t packet_in[SERIAL_BUFFER_SIZE];
uint16_t packet_in_size = 0;
uint16_t command_payload_size = 0;
// State machine related
bool packet_end_detected;
bool command_success;
// Messaging variables
uint8_t command_type;
uint8_t* command_payload;
uint16_t packet_out_size;
uint16_t output_size;
uint8_t output[SERIAL_BUFFER_SIZE];
uint8_t packet_out[SERIAL_BUFFER_SIZE];

//############################################################################//
//                                    SETUP                                   //
//############################################################################//
void setup()
{
  // Connect to PC
  Serial.begin(115200);
  while (!Serial) 
  { 
    ; // Wait for serial to connect 
  }

  // Connect to IMU
  Wire.begin();
  imu.initialize();
  // check if IMU is connected
  imu_wokring = imu.working_status();

  // Initialize PFMs
  Pfm.init();
  Pfm.disable_cnc();
}

//############################################################################//
//                                    MAIN                                    //
//############################################################################//
void loop() {

  // get new IMU measurement
  if (imu_wokring) {
    imu.perform_measurement();
  }else{
    imu_wokring = imu.working_status();
  }

  // Check if there is any data available on the serial port
  if (Serial.available() > 0) {
    serial_buffer[serial_buffer_length] = Serial.read();
    if (serial_buffer_length < SERIAL_BUFFER_SIZE) {
      serial_buffer_length++;
    }else{
      // when overflow, reset pointer to buffer
      serial_buffer_length=0;
    }
    
    // look for the end of a packet
    packet_end_detected = serial_buffer[serial_buffer_length-2] == END_BYTES[0] && serial_buffer[serial_buffer_length-1] == END_BYTES[1];
    if (packet_end_detected) {
      // detect packat_in and its size
      packet_in_size = decode_message(serial_buffer, serial_buffer_length, &packet_in[0]);

      if (packet_in_size > 0) {
        
        // separate command
        command_type = packet_in[0];
        // separate command payload
        command_payload = &packet_in[1];
        command_payload_size = packet_in_size-6;
        // process command
        command_success = Pkt.process_command(command_type, command_payload_size, command_payload, &output_size, &output[1]);
        
        if (command_success) {
          if (output_size > 0){
            // response is returned
            output[0] = command_type;
            packet_out_size = encode_message(output, output_size+1, packet_out);
          }else{
            // ACK is returned
            output[0] = command_type;
            output[1] = PKT_ACK;
            packet_out_size = encode_message(output, 2, packet_out);          
          }
        }else{
          // NACK is returned
          output[0] = command_type;
          output[1] = PKT_NACK; 
          packet_out_size = encode_message(output, 2, packet_out);
        }

        Serial.write(packet_out, packet_out_size);
        // Serial.println();

        // when command processed, reset pointer to buffer (write over previous values)
        serial_buffer_length=0;
      } // if (packet_in_size > 0)
        // Execution gets here only if FALSE packet end was detected.
        // This is not dangerous and the program should continue 
        // execution as usual.
    } // if (packet_end_detected)
  }

}