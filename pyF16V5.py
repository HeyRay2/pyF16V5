# Import libraries
from controller_classes import Controller
import pandas
import asyncio  # async io
import platform  # platform
import argparse  # argument parsing
import re  # regex
import logging  # Logging
from pathlib import Path  # Path functions

# Set platform policy
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Set a default command response timeout (in seconds)
command_timeout_default = 3

# List of valid device command options
command_options = ['on', 'off', 'reset', 'status']

# CMD Line Parser
parser = argparse.ArgumentParser(description='Control a Falcon F16V5 Pixel Controller.')
parser.add_argument('--ip', help='The IP address of the controller', required=True)
parser.add_argument('--command', help='Command to run', choices=command_options, required=True)
parser.add_argument('--ports', help='List of port:receiver values to run command against (example: 0:0,1:1,2:2)',
                    default="all")
parser.add_argument('--timeout', type=int,
                    help='Timeout for command (in seconds)', default=command_timeout_default)
parser.add_argument('--log', help='File path for log file. Defaults to script folder if omitted')
parser.add_argument('--debug', type=bool, help='Verbose mode for debugging', nargs='?', const=True)

# Get CMD Args
args = parser.parse_args()
logLevel = logging.DEBUG if args.debug else logging.INFO

# Initialize logger (so functions can utilize it)
loggerName = "myLogger"
logPath = args.log if args.log else "."
logger = logging.getLogger(loggerName)


# Functions
def run_command(controller_ip, command, port_receiver_list_string, command_timeout):
    # Access the controller
    controller = Controller(controller_ip, logger, command_timeout)

    # Show controller details
    logger.info('Controller Details: {}'.format(controller))

    # Get list of ports / receivers to run command against
    port_receiver_list = []
    fuse_list = []

    # Parse the list of ports provided
    if port_receiver_list_string != "all":
        port_receiver_list = port_receiver_list_string.split(',')

        for port_receiver in port_receiver_list:
            current_port_receiver = port_receiver.split(':')
            current_port = int(current_port_receiver[0])
            current_receiver = int(current_port_receiver[1])

            try:
                # Look for a valid fuse with the give Port and Receiver values
                fuse = controller.fuse_block.find_fuse_in_block(current_port, current_receiver)

                if fuse:
                    # Valid fuse. Added to command action list
                    logger.debug('Added - Port ID: {} | Port: {} | Receiver: {}'.format(
                        fuse.port_id,
                        fuse.port,
                        fuse.receiver))

                    fuse_list.append(fuse)
                else:
                    logger.error("No fuse found at Port: {} | Receiver {}. Skipping...".format(
                        current_port,
                        current_receiver))
            except Exception as e:
                logger.error('Could not query for use at Port: {} | Receiver: {} -- {}'.format(
                    current_port,
                    current_receiver,
                    e
                ))
    else:
        # Add full set of fuses to command action list
        logger.debug("All ports will be used!")

        fuse_list = controller.fuse_block.fuses

    # Show port list
    logger.debug('Port List: \n{}'.format(
        pandas.DataFrame([fuse.to_dict() for fuse in fuse_list]).to_string(index=False)
    ))

    # Run command on target device(s)
    logger.info('Command: {}'.format(command))

    # Keep a running list of updated ports
    updated_ports = []

    # Loop through the fuses in the command action list
    for fuse in fuse_list:
        logger.debug('Performing "{}" action for Port: {} | Receiver: {}'.format(
            command,
            fuse.port,
            fuse.receiver))

        # Perform command action
        if command == "on":
            controller.turn_on_fuse(fuse)
            updated_ports.append(fuse)
        elif command == "off":
            controller.turn_off_fuse(fuse)
            updated_ports.append(fuse)
        elif command == "reset":
            controller.reset_fuse(fuse)
            updated_ports.append(fuse)
        elif command == "status":
            updated_ports.append(fuse)
        else:
            logger.critical('Unknown or unsupported command: {}'.format(command))

    # Show status of selected fuses
    updated_ports_sorted = sorted(updated_ports, key=lambda x: x.port_id)  # sort the fuse list
    fuse_df = pandas.DataFrame([fuse.to_dict() for fuse in updated_ports_sorted])  # create a data frame
    logger.info('Updated Fuse Status:\n{}'.format(fuse_df.to_string(index=False)))  # print the data frame


def print_debug(message, debug_mode):
    # Print message only if debug mode is enabled
    if debug_mode:
        print('|| -- DEBUG -- || {}'.format(message)) if (len(message) > 0) else print('')


def config_logger(log_name_prefix, log_level, log_path):
    # Log path existence / creation
    Path(log_path).mkdir(parents=True, exist_ok=True)

    # Log filename
    logFileName = '{}/{}.log'.format(log_path, log_name_prefix)

    # Get logger
    myLogger = logging.getLogger(loggerName)

    # Set lowest allowed logger severity
    logger.setLevel(logging.DEBUG)

    # Console output handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

    # Log file output handler
    file_handler = logging.FileHandler(logFileName)
    file_handler.setLevel(log_level)
    file_handler.encoding = 'utf-8'
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)d: %(message)s'))
    logger.addHandler(file_handler)

    # Return configured logger
    return myLogger


# Main function
async def main():
    # Configure logging
    logger = config_logger(Path(parser.prog).stem, logLevel, logPath)

    # Get command timeout
    command_timeout = args.timeout

    # Check for valid IP address
    if re.match(
            r"(?:\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b)\Z",
            args.ip):

        # Successful match at the start of the string
        device_ip = args.ip
    else:
        # IP match attempt failed
        logger.critical('Invalid IP Address: {}'.format(args.ip))
        exit()

    # Check if port list is valid
    if re.match(r"^all|([1-9]|[12][0-9]|[3][0-2]):[0-9]([,]([1-9]|[12][0-9]|[3][0-2]):[0-9])*$", args.ports):
        port_list = args.ports
    else:
        # Port list parsing failure
        logger.critical('Invalid Port List: {}'.format(args.ports))
        exit()

    #  Get command from CMD args
    command = args.command

    # Check for valid command
    if command in command_options:
        # Try to run command
        try:
            run_command(device_ip, command, port_list, command_timeout)
        except Exception as e:
            logger.critical('Error: {}'.format(e))
    else:
        logger.critical('Invalid command: {}'.format(command))
        exit()


# Initiate main
if __name__ == "__main__":
    asyncio.run(main())
else:
    help()
