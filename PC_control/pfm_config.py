# There are 3 axis: X, Y, Z
NUM_PFM                 = (3).to_bytes(length=1, byteorder='big')
PFM_X                   = (0).to_bytes(length=1, byteorder='big')
PFM_X_FLAG              = bytes.fromhex('01')
PFM_Y                   = (1).to_bytes(length=1, byteorder='big')
PFM_Y_FLAG              = bytes.fromhex('02')
PFM_Z                   = (2).to_bytes(length=1, byteorder='big')
PFM_Z_FLAG              = bytes.fromhex('04')
# frequency value considered as STOP
INACTIVE_FREQ           = (65535).to_bytes(length=4, byteorder='big')
# default PFM frequency (can be changed in software)
DEFAULT_PFM_FREQ        = (6400).to_bytes(length=4, byteorder='big')
# derive balue of interrupt counter with prescaler 1:1
#INTERRUPT_COUNTER       = hex(F_CPU/2/DEFAULT_PFM_FREQ)
