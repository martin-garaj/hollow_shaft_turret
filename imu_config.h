// size of window over which the samples are averaged
// NOTICE: value 0 results in WINDOW_SIZE = 1, 
//         value 1 results in WINDOW_SIZE = 2, 
//         value 2 results in WINDOW_SIZE = 4, 
//         value 3 results in WINDOW_SIZE = 8, 
//          ...
#define LOG2_WINDOW_SIZE         5
#define WINDOW_SIZE             (0x1 << LOG2_WINDOW_SIZE)
