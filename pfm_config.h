// There are 3 axis: X, Y, Z
#define NUM_PFM                 3
#define PFM_X                   0
#define PFM_X_FLAG              0x01
#define PFM_Y                   1
#define PFM_Y_FLAG              0x02
#define PFM_Z                   2
#define PFM_Z_FLAG              0x04
// frequency value considered as STOP
#define INACTIVE_FREQ           65535
// default PFM frequency (can be changed in software)
#define DEFAULT_PFM_FREQ        6400
// derive balue of interrupt counter with prescaler 1:1
#define INTERRUPT_COUNTER       F_CPU/2/DEFAULT_PFM_FREQ