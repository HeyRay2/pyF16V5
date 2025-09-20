# pyF16V5
API wrapper for the Falcon F16V5 Pixel Controller

There are plans for making other tweaks and adding features over time, but for now the script will let you do the following for one fuse, a set of fuses, or all fuses:

- Show the status of a fuse
- Turn on / turn off a fuse
- Reset a tripped fuse 

## Installation

- Clone the repository: 
```
git clone https://github.com/HeyRay2/pyF16V5.git
```
- Create a virtual environment in the cloned repository folder (https://www.w3schools.com/python/python_virtualenv.asp):
```
Windows

C:\Users\Your Name> python -m venv my-virt-env

Linux / Mac OS

$ python -m venv my-virt-env 
```
- Activate the virtual environment:
```
Windows

C:\Users\Your Name> my-virt-env\Scripts\activate

Linux / Mac OS

$ source myfirstproject/bin/activate
```
- Install dependency packages:
```
Windows 

(my-virt-env) C:\Users\Your Name> pip install -r requirements.txt

Linux / Mac OS

(my-virt-env) ... $ pip install -r requirements.txt 
```


## Usage 

```
pyf16v5.py [-h] --ip IP --command {on,off,reset,status} [--ports PORTS] [--timeout TIMEOUT] [--log LOG] [--debug [DEBUG]]
```

### Usage Options:

-h, --help            show this help message and exit

--ip IP               The IP address of the controller

--command {on,off,reset,status}  Command to run

--ports PORTS         List of port:receiver values to run command against (example: 0:0,1:1,2:2)

--timeout TIMEOUT     Timeout for command (in seconds)

--log LOG             File path for log file. Defaults to script folder if omitted

--debug [DEBUG]       Verbose mode for debugging
