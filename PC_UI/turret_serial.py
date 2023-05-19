class SerialReader(QObject):
    data_ready = pyqtSignal(dict)

    def __init__(self, port, baudrate):
        super().__init__()
        self.serial = serial.Serial(port, baudrate)
        self.buffer_in = bytearray()

    def run(self):
        """ Reads the incomming serial communication. 
        
        If responsible for detecting the packets and managing the buffer storing 
        raw incoming serial communication.
        
        """
        while True:
            if self.serial.inWaiting() > 0:
                # Read the data and append it to the raw_data buffer
                data = bytearray(self.serial.read(self.serial.in_waiting))
                logger.info(f"buffer_in:{self.buffer_in} | data:{data}")
                self.buffer_in.extend(data)
                # Detect all packet present in the buffer
                packet_detected = True
                while packet_detected:
                    # Detect packet
                    self.buffer_in, packet = parse_buffer(self.buffer_in)
                    # Parse packet
                    if len(packet) > 0:
                        packet_detected = True
                        logger.info(f"packet:{packet}")
                        command, payload = parse_packet(packet)
                        dict_dislay = {'command':command, 'payload':payload}
                        self.data_ready.emit(dict_dislay)
                    else:
                        packet_detected = False

    def write_serial(self, message):
        self.serial.write(message.encode())