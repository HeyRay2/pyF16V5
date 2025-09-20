# Import libraries
from dataclasses import dataclass
from enum import Enum
from typing import List
import requests
import json
import pandas


# Class for Controller Fuse
@dataclass
class ControllerFuse:
    port_id: int
    port: int
    receiver: int
    state: Enum
    icon: Enum

    def __init__(self, port, receiver, state) -> None:
        self.port_id = port
        self.port = port + 1
        self.receiver = receiver
        self.state = ControllerFuseState(state)
        self.icon = ControllerFuseStateIcon(state)

    def to_dict(self):
        return {
            'port': self.port,
            'receiver': self.receiver,
            'state': self.state,
        }


# Class for Fuse States
class ControllerFuseState(Enum):
    UNKNOWN = -1
    GOOD = 0
    OFF = 1
    TRIPPED = 2

    def __str__(self):
        return self.name


# Class for Fuse State Icons
class ControllerFuseStateIcon(Enum):
    U = -1
    O = 0
    _ = 1
    X = 2

    def __str__(self):
        return self.name


# Class for Controller Fuse Block
@dataclass
class ControllerFuseBlock:
    fuses: List[ControllerFuse]

    def __init__(self, fuses, logger) -> None:
        self.logger = logger
        self.fuses = self.__build_fuse_block(fuses)

    def __build_fuse_block(self, fuses):
        self.logger.debug("Fuses Output: {}".format(fuses))
        fuse_list = []

        for fuse in fuses:
            self.logger.debug("Fuse Details: {}".format(fuse))
            fuse_num = fuse.get("p")
            self.logger.debug("Fuse Port #: {}".format(fuse_num))
            fuse_receiver = fuse.get("r")
            self.logger.debug("Fuse Receiver #: {}".format(fuse_receiver))
            fuse_state = fuse.get("f")
            self.logger.debug("Fuse State: {}".format(fuse_state))
            fuse_list.append(ControllerFuse(fuse_num, fuse_receiver, fuse_state))

        return fuse_list

    def get_fuse_block(self):
        fuse_block_table = pandas.DataFrame([fuse.to_dict() for fuse in self.fuses])

        return fuse_block_table

    def find_fuse_in_block(self, port, receiver):
        matching_fuse = None

        self.logger.debug('Searching Fuse Block for Port: {} | Receiver: {}'.format(
            port,
            receiver
        ))

        # Search fuse that has a matching port
        fuses_matching_port = [fuse for fuse in self.fuses if fuse.port == port]

        self.logger.debug("Fuses Matching Port: {}\n{}".format(
            port,
            fuses_matching_port
        ))

        # One or more port matches found
        if len(fuses_matching_port) >= 1:
            # Search the matching ports for a matching receiver
            fuses_matching_receiver = [fuse for fuse in fuses_matching_port if fuse.receiver == receiver]

            self.logger.debug('Receivers matching {} on Port ID: {}'.format(
                receiver,
                port
            ))

            # Matching receiver found
            if len(fuses_matching_receiver) > 0:
                # Return the matching fuse
                matching_fuse = fuses_matching_receiver[0]

        return matching_fuse


# Class for Controller Instance
class Controller:
    # Constructor
    def __init__(self, ip, logger, request_timeout):
        self.ip = ip
        self.name = None
        self.version = None
        self.fuse_block = []
        self.logger = logger
        self.timeout = request_timeout

        # Query the controller for details
        self.__get_controller_details()

        # Query the controller fuse details
        self.__get_controller_fuses()

    def __str__(self):
        return "IP: {} | Name: {} | Version: {}".format(
            self.ip,
            self.name,
            self.version
        )

    def __get_controller_details(self):
        """Returns Controller details from the IP address provided"""

        # API call URL
        url = "http://{}/api".format(
            self.ip)

        self.logger.info("Querying for controller at '{}'".format(self.ip))

        # Payload
        payload = json.dumps({
            "B": 0,
            "E": 0,
            "I": 0,
            "M": "ST",
            "P": {},
            "T": "Q"
        })

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Send the request and record the response
        response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

        # Verify a valid OpenToken was received
        if not response.ok:
            # Error getting Environment ID
            env_error = response.json()

            raise Exception("Error getting controller details at '{}': {} - {}".format(
                self.ip,
                env_error.get("translationKey"),
                env_error.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        # Set controller details
        self.name = response.json().get("P").get("N")
        self.version = response.json().get("P").get("V")
        self.logger.debug("Controller '{}' running version '{}' found at '{}'".format(
            self.name,
            self.version,
            self.ip))

        return

    def __get_controller_fuses(self):
        """Returns Controller fuse details"""

        # API call URL
        url = "http://{}/api".format(
            self.ip)

        self.logger.debug("Querying fuse details for '{}' controller at '{}'".format(
            self.name,
            self.ip))

        # Payload
        payload = json.dumps({
            "B": 0,
            "E": 0,
            "I": 0,
            "M": "CQ",
            "P": {},
            "T": "Q"
        })

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Send the request and record the response
        response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

        # Verify a valid OpenToken was received
        if not response.ok:
            # Error getting Environment ID
            env_error = response.json()

            raise Exception("Error getting controller fuse details at '{}': {} - {}".format(
                self.ip,
                env_error.get("translationKey"),
                env_error.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        # Set controller fuse
        self.logger.debug("Generating Fuse Block Details...")
        self.fuse_block = ControllerFuseBlock(response.json().get("P").get("A"), self.logger)
        self.logger.debug("Controller '{}' fuse details:".format(self.name))
        self.logger.debug('Fuse Block Details:\n{}'.format(
            self.fuse_block.get_fuse_block().to_string(index=False)))

        return

    def turn_off_all_fuses(self):
        """Turns Off All Controller Fuses"""

        # API call URL
        url = "http://{}/api".format(
            self.ip)

        self.logger.info("Turning off all fuses on '{}' controller at '{}'".format(self.name, self.ip))

        # Payload
        payload = json.dumps({
            "B": 0,
            "E": 0,
            "I": 0,
            "M": "FT",
            "P": {"T": 0},
            "T": "S"
        })

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Send the request and record the response
        response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

        # Verify a valid OpenToken was received
        if not response.ok:
            # Error getting Environment ID
            env_error = response.json()

            raise Exception("Error turning off controller fuses at '{}': {} - {}".format(
                self.ip,
                env_error.get("translationKey"),
                env_error.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        return True

    def turn_on_all_fuses(self):
        """Turns On All Controller Fuses"""

        # API call URL
        url = "http://{}/api".format(
            self.ip)

        self.logger.info("Turning on all fuses on '{}' controller at '{}'".format(self.name, self.ip))

        # Payload
        payload = json.dumps({
            "B": 0,
            "E": 0,
            "I": 0,
            "M": "FT",
            "P": {"T": 1},
            "T": "S"
        })

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Send the request and record the response
        response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

        # Verify a valid OpenToken was received
        if not response.ok:
            # Error getting Environment ID
            env_error = response.json()

            raise Exception("Error turning on controller fuses at '{}': {} - {}".format(
                self.ip,
                env_error.get("translationKey"),
                env_error.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        return True

    def reset_all_fuses(self):
        """Resets All Tripped Controller Fuses"""

        # API call URL
        url = "http://{}/api".format(
            self.ip)

        self.logger.info("Resetting all tripped fuses on '{}' controller at '{}'".format(self.name, self.ip))

        # Payload
        payload = json.dumps({
            "B": 0,
            "E": 0,
            "I": 0,
            "M": "FR",
            "P": {},
            "T": "S"
        })

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Send the request and record the response
        response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

        # Verify a valid OpenToken was received
        if not response.ok:
            # Error getting Environment ID
            env_error = response.json()

            raise Exception("Error resetting controller fuses at '{}': {} - {}".format(
                self.ip,
                env_error.get("translationKey"),
                env_error.get("error"))
            )

        # Show response details
        self.logger.debug(json.dumps(response.json()))

        return True

    def turn_on_fuse(self, fuse):
        """Turns On Controller Fuse for a Specific Port"""
        # API call URL
        url = "http://{}/api".format(
            self.ip)

        # Check current fuse state
        if fuse.state is ControllerFuseState.GOOD:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is already on!".format(
                    fuse.port,
                    fuse.receiver
                ))
        elif fuse.state is ControllerFuseState.TRIPPED:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is tripped and must be reset!".format(
                    fuse.port,
                    fuse.receiver
                ))
        elif fuse.state is ControllerFuseState.UNKNOWN:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is in an unknown state!".format(
                    fuse.port,
                    fuse.receiver
                ))
        else:
            self.logger.info(
                "Turning on fuse at Port: {}, Receiver: {})".format(
                    fuse.port,
                    fuse.receiver
                ))

            # Payload
            payload = json.dumps({
                "B": 0,
                "E": 0,
                "I": 0,
                "M": "TF",
                "P": {"P": fuse.port_id, "R": fuse.receiver},
                "T": "S"
            })

            # Headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Send the request and record the response
            response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

            # Verify a valid OpenToken was received
            if not response.ok:
                # Error getting Environment ID
                env_error = response.json()

                raise Exception("Error turning on controller fuse at '{}': {} - {}".format(
                    self.ip,
                    env_error.get("translationKey"),
                    env_error.get("error"))
                )

            # Show response details
            self.logger.debug(json.dumps(response.json()))

            # Update controller fuse status
            fuse.state = ControllerFuseState.GOOD
            fuse.icon = ControllerFuseStateIcon.O

        return True

    def turn_off_fuse(self, fuse):
        """Turns Off Controller Fuse for a Specific Port"""
        # API call URL
        url = "http://{}/api".format(
            self.ip)

        # Check current fuse state
        if fuse.state is ControllerFuseState.OFF:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is already off!".format(
                    fuse.port,
                    fuse.receiver
                ))
        elif fuse.state is ControllerFuseState.TRIPPED:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is tripped and must be reset!".format(
                    fuse.port,
                    fuse.receiver
                ))
        elif fuse.state is ControllerFuseState.UNKNOWN:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is in an unknown state!".format(
                    fuse.port,
                    fuse.receiver
                ))
        else:
            self.logger.info(
                "Turning off fuse at Port: {}, Receiver: {})".format(
                    fuse.port,
                    fuse.receiver
                ))

            # Payload
            payload = json.dumps({
                "B": 0,
                "E": 0,
                "I": 0,
                "M": "TF",
                "P": {"P": fuse.port_id, "R": fuse.receiver},
                "T": "S"
            })

            # Headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Send the request and record the response
            response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

            # Verify a valid OpenToken was received
            if not response.ok:
                # Error getting Environment ID
                env_error = response.json()

                raise Exception("Error turning off controller fuse at '{}': {} - {}".format(
                    self.ip,
                    env_error.get("translationKey"),
                    env_error.get("error"))
                )

            # Show response details
            self.logger.debug(json.dumps(response.json()))

            # Update controller fuse status
            fuse.state = ControllerFuseState.OFF
            fuse.icon = ControllerFuseStateIcon._

        return True

    def reset_fuse(self, fuse):
        """Reset Controller Fuse for a Specific Port"""
        # API call URL
        url = "http://{}/api".format(
            self.ip)

        # Check current fuse state
        if fuse.state in (ControllerFuseState.GOOD, ControllerFuseState.OFF):
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is not tripped!".format(
                    fuse.port,
                    fuse.receiver
                ))
        elif fuse.state is ControllerFuseState.UNKNOWN:
            self.logger.info(
                "Fuse at Port: {}, Receiver: {} is in an unknown state!".format(
                    fuse.port,
                    fuse.receiver
                ))
        else:
            self.logger.info(
                "Resetting fuse at Port: {}, Receiver: {})".format(
                    fuse.port,
                    fuse.receiver
                ))

            # Payload
            payload = json.dumps({
                "B": 0,
                "E": 0,
                "I": 0,
                "M": "FR",
                "P": {"P": fuse.port_id, "R": fuse.receiver},
                "T": "S"
            })

            # Headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            # Send the request and record the response
            response = requests.request("POST", url, headers=headers, data=payload, timeout=self.timeout)

            # Verify a valid OpenToken was received
            if not response.ok:
                # Error getting Environment ID
                env_error = response.json()

                raise Exception("Error resetting controller fuse at '{}': {} - {}".format(
                    self.ip,
                    env_error.get("translationKey"),
                    env_error.get("error"))
                )

            # Show response details
            self.logger.debug(json.dumps(response.json()))

            # Update controller fuse status
            fuse.state = ControllerFuseState.GOOD
            fuse.icon = ControllerFuseStateIcon.O

        return True
