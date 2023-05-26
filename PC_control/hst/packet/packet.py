import logging
logger = logging.getLogger(__name__)

from .pkt_defs import *
""" Definitions

    Buffer: | ... | START_BYTES | PAYLOAD_SIZE | COMMAND | DATA | END_BYTES | ... | START_BYTES | ...|
    Packet:       | START_BYTES | PAYLOAD_SIZE | COMMAND | DATA | END_BYTES |
    Message:                    | PAYLOAD_SIZE | COMMAND | DATA |
    Payload:                                   | COMMAND | DATA |
    Data:                                                | DATA |

    Buffer
        - holds all incoming data (potentially consisting of multiple packets)
    Packet
        - holds structure representing single exchange of data (e.g. reply)
    Message
        - represents stripped-down version of packet without START_BYTES and END_BYTES
        - used only check_packet_complete()
    Payload
        - Message without PAYLOAD_SIZE
        - contains the Command and the Data
    Command
        - when transmitting, the Command is deciphered first, driving the state machine
        - when receiving, the Command is always repeated from the transmitted packet,
          since this is purely Master-Worker relation (Worker never initiates communication) 
    Data
        - Data carried by the packet (e.g. ACK, NACK, IMU data)
        
Public functions:
    parse_message()
    encode_packet()
    parse_buffer()
"""

def parse_message(packet:bytearray) -> tuple(bytearray, bytearray):
    """ Break the packet into Command and Payload

    :param packet: Complete packet, including START_BYTES and END_BYTES
    :type packet: bytearray
    :return: Returns (Command, Payload_content) 
    :rtype: tuple(bytearray, bytearray)
    """
    command = packet[0:COMMAND_BYTE_SIZE]
    data = packet[COMMAND_BYTE_SIZE:]
    return command, data


def encode_packet(payload) -> bytearray:
    """
    Encodes a payload into a packet.

    :param payload: The payload to be encoded into a packet.
    :type payload: bytearray
    :return: The encoded packet.
    :rtype: bytearray
    """
    # Payload size (2 bytes, little-endian)
    payload_size = len(payload)
    size_bytes = payload_size.to_bytes(PAYLOAD_BYTE_SIZE, byteorder=BYTEORDER)
    # Payload
    payload_bytes = bytes(payload)
    # Combine all bytes into a single message
    message = START_BYTES + size_bytes + payload_bytes + END_BYTES
    logger.debug(f"packet.encode_packet(payload={payload}) -> {message}")
    return message


def _find_bytes(byte_array:bytearray, bytes:bytearray) -> list(int):
    """ Locate all indices of bytes-pattern within byte_array.

    :param byte_array: Array of bytes to be searched for a bytes-patter.
    :type byte_array: bytearray
    :param bytes: Patter of bytes to be searched for within byte_array.
    :type bytes: bytearray
    :return: List of indices, if no indices found returns [-1]
    :rtype: list
    """
    indices = []
    for i in range(len(byte_array)-1):
        if byte_array[i:i+len(bytes)] == bytes:
            indices.append(i)
    if len(indices) == 0:
        indices.append(-1)
    return indices


def _bytearray_to_int(bytearray_int:bytearray, byteorder:str=BYTEORDER) -> int:
    """ Decode a bytearray into an integer.

    :param bytearray_int: Array of bytes encoding a single integer.
    :type bytearray_int: bytearray
    :param byteorder: Endianity, defaults to BYTEORDER
    :type byteorder: str, optional
    :return: Integer stored within the bytearray_int.
    :rtype: int
    """
    return int.from_bytes(bytearray_int, byteorder)


def _check_packet_complete(expected_packet:bytearray) -> tuple(bool, bytearray):
    """
    Checks whether a packet is complete according to its payload size.

    :param expected_packet: The packet to be checked.
    :type expected_packet: bytearray
    :return: A tuple containing a boolean indicating whether the packet is complete and the packet's payload.
    :rtype: tuple
    """
    payload_size_bytes = expected_packet[len(START_BYTES):len(START_BYTES)+PAYLOAD_BYTE_SIZE]
    message_size = _bytearray_to_int(bytearray_int=payload_size_bytes) + PAYLOAD_BYTE_SIZE
    if message_size == len(expected_packet)-len(START_BYTES)-len(END_BYTES):
        payload = expected_packet[len(START_BYTES)+PAYLOAD_BYTE_SIZE:len(START_BYTES)+message_size]
        return True, payload
    else:
        # false start and/or end of packet
        return False, bytearray()
        

def parse_buffer(buffer:bytearray) -> tuple(bytearray, bytearray):
    """ Searches for a first complete packet within the buffer.
    
    Function searches the first consistent packet between all valid 
    positions of START_BYTES and END_BYTES found in the buffer.
    Once the first consistent packet is found, updated buffer is returned 
    together with the content of the packet. If no packet is found, 
    an emptyarray representing the packet is returned.  
    
    Since only the first packet is returned, 
    this function can be called continuously.
    
    :param buffer: Array of all received data.
    :type buffer: bytearray
    :return: Returns (updated buffer, packet - empty if no packet is detected)
    :rtype: tuple(bytearray, bytearray)
    """
    # detect all START_BYTES
    packet_start_idxs = _find_bytes(byte_array=buffer, bytes=START_BYTES)
    if packet_start_idxs[0] == -1:
        # no START_BYTES found, dump the buffer
        return bytearray(), bytearray()
    # detect all END_BYTES
    packet_end_idxs = _find_bytes(byte_array=buffer, bytes=END_BYTES)
    # no END_BYTES found, return buffer to append more data
    if packet_end_idxs[0] == -1:
        return buffer, bytearray()
        
    # search for every start of the packet, until a packet of found
    for packet_start_idx in packet_start_idxs:
        for packet_end_idx in packet_end_idxs:
            expected_packet = buffer[packet_start_idx:packet_end_idx+len(END_BYTES)]
            packet_detected, payload = _check_packet_complete(expected_packet)
            if packet_detected:
                # remove the packet from the buffer
                buffer = buffer[packet_end_idx+len(END_BYTES):]
                return buffer, payload
            else:
                # continue the search
                pass
    return buffer, bytearray()