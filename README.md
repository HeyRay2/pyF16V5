# pyF16V5
API wrapper for the Falcon F16V5 Pixel Controller

There are plans for making other tweaks and adding features over time, but for now the script will let you do the following for one fuse, a set of fuses, or all fuses:

- Show the status of a fuse
- Turn on / turn off a fuse
- Reset a tripped fuse 


Usage Example: 

pyf16v5.py [-h] --ip IP --command {on,off,reset,status} [--ports PORTS] [--timeout TIMEOUT] [--log LOG] [--debug [DEBUG]]

options:

  -h, --help            show this help message and exit

  --ip IP               The IP address of the controller

 --command {on,off,reset,status}  Command to run

  --ports PORTS         List of port:receiver values to run command against (example: 0:0,1:1,2:2)

  --timeout TIMEOUT     Timeout for command (in seconds)

  --log LOG             File path for log file. Defaults to script folder if omitted

  --debug [DEBUG]       Verbose mode for debugging
