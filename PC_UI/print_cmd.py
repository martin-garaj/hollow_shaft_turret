""" This file documents the command structure by parsing the commands in their
byt format into a structured and human-readable format.

The command functions in their original form can be found in pkt_process_cmd.cpp
and the command constants are defined in pkt_cmd_defs.h

"""

from pkt_cmd_defs import *

def encode_pfm_flag(PFM_X_FLAG:bool=False, PFM_Y_FLAG:bool=False, PFM_Z_FLAG:bool=False, PFM_Q_FLAG:bool=False):
    pmf_flag = 0b000
    if PFM_X_FLAG:
        pmf_flag = pmf_flag | 0b0001
    if PFM_Y_FLAG:
        pmf_flag = pmf_flag | 0b0010
    if PFM_Z_FLAG:
        pmf_flag = pmf_flag | 0b0100
    if PFM_Q_FLAG:
        pmf_flag = pmf_flag | 0b1000
    return pmf_flag


def decode_pfm_flag(pmf_flag):
    return {'PFM_X':bool(pmf_flag&0b0001),
            'PFM_Y':bool(pmf_flag&0b0010),
            'PFM_Z':bool(pmf_flag&0b0100),
            'PFM_Q':bool(pmf_flag&0b1000)}
    

def packet_outgoing_to_dict(command, payload):
    info = dict()
    # command_int = int.from_bytes(command, byteorder=BYTEORDER)
    if command == int.from_bytes(CMD_SET_TARGET_FREQ, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_TARGET_FREQ'
        info.update(decode_pfm_flag(payload[0]))
        info['FREQ'] = int.from_bytes(payload[1:3], byteorder=BYTEORDER)
        info['DIR'] = bool(payload[3])
    elif command == int.from_bytes(CMD_SET_TARGET_DELTA, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_TARGET_DELTA'
        info.update(decode_pfm_flag(payload[0]))
        info['FREQ'] = int.from_bytes(payload[1:3], byteorder=BYTEORDER)
        info['DELTA'] = int.from_bytes(payload[3:7], byteorder=BYTEORDER)
    elif command == int.from_bytes(CMD_GET_DELTA_STEPS, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        info.update(decode_pfm_flag(payload[0]))
    elif command == int.from_bytes(CMD_GET_IMU_MEASUREMENT, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_GET_IMU_MEASUREMENT'
    elif command == int.from_bytes(CMD_SET_ISR_FREQ, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_ISR_FREQ'
        info['ISR_FREQ'] = int.from_bytes(payload[0:2], byteorder=BYTEORDER)
    elif command == int.from_bytes(CMD_ENABLE_CNC, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_ENABLE_CNC'
    elif command == int.from_bytes(CMD_DISABLE_CNC, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_DISABLE_CNC'
    elif command == int.from_bytes(CMD_SET_DELTA_STEPS, byteorder=BYTEORDER):
        info['CMD'] = 'CMD_SET_DELTA_STEPS'
        info.update(decode_pfm_flag(payload[0]))
        info['DELTA'] = int.from_bytes(payload[1:5], byteorder=BYTEORDER)
    else:
        raise ValueError(f"command={command}, invalid value.")
    return info
    
    
def packet_incoming_to_dict(command, payload):
    info = dict()
    if command == CMD_SET_TARGET_FREQ:
        info['CMD'] = 'CMD_SET_TARGET_FREQ'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_SET_TARGET_DELTA:
        info['CMD'] = 'CMD_SET_TARGET_DELTA'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_GET_DELTA_STEPS:
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        if len(payload) > 1:
            info['DELTA'] = int.from_bytes(payload[0:4], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_GET_IMU_MEASUREMENT:
        info['CMD'] = 'CMD_GET_DELTA_STEPS'
        if len(payload) > 1:
            for idx, value_type in enumerate(['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']):
                val_start = idx*2
                val_end = val_start+2
                info[value_type] = int.from_bytes(payload[val_start:val_end], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_SET_ISR_FREQ:
        info['CMD'] = 'CMD_SET_ISR_FREQ'
        if len(payload) > 1:
            info['ISR_FREQ'] = int.from_bytes(payload[0:2], byteorder=BYTEORDER)
        else:
            info['ACK'] = False if int(payload[0])==int.from_bytes(PKT_NACK, byteorder=BYTEORDER) else 'ERROR'
    elif command == CMD_ENABLE_CNC:
        info['CMD'] = 'CMD_ENABLE_CNC'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_DISABLE_CNC:
        info['CMD'] = 'CMD_DISABLE_CNC'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    elif command == CMD_SET_DELTA_STEPS:
        info['CMD'] = 'CMD_SET_DELTA_STEPS'
        info['ACK'] = True if int(payload[0])==int.from_bytes(PKT_ACK, byteorder=BYTEORDER) else False
    else:
        raise ValueError(f"command={command}, invalid value.")
    return info
    
    
def cmd_dict_to_str(cmd_dict:dict):
    no_name_keys = ['CMD']
    pmf_flag_keys = ['PFM_X', 'PFM_Y', 'PFM_Z', 'PFM_Q']
    int_keys = ['FREQ', 'DELTA', 'ISR_FREQ']
    other_keys = ['DIR', 'ACK']
    imu_keys = ['AX', 'AY', 'AZ', 'GX', 'GY', 'GZ', 'MX', 'MY', 'MZ']
    
    string = ""
    for key, value in cmd_dict.items():
        if key in no_name_keys:
            string += f"{str(value)[4:].ljust(21)}: "
        if key in pmf_flag_keys:
            string += f"|{int(value)}"
        if key in int_keys:
            string += f" - {key}={str(value).ljust(6)}"
        if key in other_keys:
            string += f" - {key}={value}"
        if key in imu_keys:
            floating_point = (value-65535)/32767
            string += f"|{key}={floating_point:.2f}"
    return string
    

if __name__ == '__main__':
    
    BYTEORDER = 'little'

    payload = bytearray([
                1, # payload: which pfm
                11, # payload: freq
                0, # payload: freq
                1, # payload: pfm direction
                ],
            )
    command = CMD_SET_TARGET_FREQ

    print(packet_outgoing_to_dict(command, payload))
    print(cmd_dict_to_str(packet_outgoing_to_dict(command, payload)))
    
    payload = bytearray([
                1, 0,# AX
                2, 0,# AY
                3, 0,# AZ
                4, 0,# GX
                5, 0,# GY
                6, 0,# GZ
                7, 0,# MX
                8, 0,# MY
                9, 0,# MZ
                ],
            )
    command = CMD_GET_IMU_MEASUREMENT
    
    print(packet_incoming_to_dict(command, payload))
    print(cmd_dict_to_str(packet_incoming_to_dict(command, payload)))