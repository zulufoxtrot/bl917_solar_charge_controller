#!/usr/bin/env python3
"""
Solar Charge Controller Websocket Client

This client connects to a solar charge controller via websocket and can run commands (read / write).

Usage:
    python client.py --command get-charge-mode
    python client.py --command set-charge-mode --value 0
"""

import asyncio
import json
import argparse
import sys
import signal
import time
import logging
from typing import Dict, Any, Optional, List, Union

import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SolarControllerClient")

# Constants
DEFAULT_WEBSOCKET_URL = "ws://device.gz529.com/"
CONNECTION_TIMEOUT = 5  # seconds
COMMAND_TIMEOUT = 10  # seconds

PROPERTY_NAME_MAPPING = {
    "solar_model_type": "Device type",
    "dianya": "Battery voltage",
    "cddl": "Charging current",
    "fddl": "Discharge current",
    "temperature": "Temperature",
    "solar_status": "Solar panel status",
    "work_status": "Load status",
    "power_status": "Wind power status",
    "total_power": "Total energy recharged",
    "total_power_num": "Energy reset count",
    "battery_type": "Battery type",
    "timing_hour": "Timer hours",
    "timing_min": "Timer minutes",
    "cm_voltage": "Floating voltage",
    "output_mode": "Mode",
    "jz_voltage": "Cutoff voltage",
    "fz_output": "Output status",
    "voltage_monitor_selected": "Battery voltage detection",
    "hf_out_voltage": "Restore discharge voltage"
}


class SolarControllerClient:
    """Client for interacting with a solar charge controller via websocket."""

    def __init__(self, websocket_url: str = DEFAULT_WEBSOCKET_URL, mac_address: str = None):
        """Initialize the client with the websocket URL and device MAC address."""
        self.websocket_url = websocket_url

        if not mac_address:
            raise ValueError("MAC address is required")

        self.mac_address = mac_address
        self.websocket = None
        self.client_id = None
        self.connected = False
        self.running = False

    async def connect(self, timeout: int = CONNECTION_TIMEOUT, max_attempts: int = 3) -> bool:
        """
        Establish a connection to the websocket server and wait for handshake.
        Makes multiple attempts before giving up.

        Args:
            timeout: Connection timeout in seconds
            max_attempts: Maximum number of connection attempts

        Returns:
            bool: True if connection was successful, False otherwise
        """
        attempt = 1
        while attempt <= max_attempts:
            try:
                logger.info(f"Connection attempt {attempt} of {max_attempts}...")

                # Connect to the websocket server
                self.websocket = await asyncio.wait_for(
                    websockets.connect(self.websocket_url),
                    timeout=timeout
                )
                logger.debug(f"Websocket connection open.")

                # Wait for handshake message
                handshake = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=timeout
                )
                logger.debug(f"Received handshake from server.")


                # Parse handshake message
                handshake_data = json.loads(handshake)
                if handshake_data.get("code") == 200 and "client_id" in handshake_data:
                    self.client_id = handshake_data["client_id"]
                    self.connected = True
                    logger.info(f"Connected successfully. Client ID: {self.client_id}")
                    return True
                else:
                    logger.error(f"Invalid handshake response: {handshake}")

                    # Close the connection before retrying
                    await self.websocket.close()
                    self.websocket = None

            except asyncio.TimeoutError:
                logger.error(f"Connection timed out after {timeout} seconds")
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")

            # Clean up after failed attempt
            if self.websocket:
                try:
                    await self.websocket.close()
                except Exception:
                    pass
                self.websocket = None

            # If this wasn't the last attempt, wait before retrying
            if attempt < max_attempts:
                retry_delay = 2  # seconds
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

            attempt += 1

        # If we get here, all attempts failed
        logger.error(f"Failed to connect after {max_attempts} attempts")
        return False

    async def disconnect(self):
        """Close the websocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug(f"Error while closing websocket: {str(e)}")
            finally:
                self.connected = False
                self.client_id = None
                logger.info("Disconnected from server")

    async def send_command(self, action: str, params: Dict[str, Any] = None) -> Dict:
        """
        Send a command to the server and wait for a response.

        Args:
            action: The action to perform
            params: Additional parameters for the command

        Returns:
            Dict: The server response

        Raises:
            RuntimeError: If not connected or command fails
        """
        if not self.connected or not self.websocket:
            raise RuntimeError("Not connected to server")

        # Prepare command
        command = {"Action": action}
        if params:
            command.update(params)

        # Add MAC address if not present
        if "mac" not in command:
            command["mac"] = self.mac_address

        try:
            # Send command
            command_str = json.dumps(command)
            logger.debug(f"Sending command: {command_str}")
            await self.websocket.send(command_str)

            # Wait for response
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=COMMAND_TIMEOUT
            )

            # Parse response
            response_data = json.loads(response)
            logger.debug(f"Received response: {response}")
            return response_data

        except asyncio.TimeoutError:
            raise RuntimeError(f"Command timed out after {COMMAND_TIMEOUT} seconds")
        except Exception as e:
            raise RuntimeError(f"Command error: {str(e)}")

    async def get_all_machine_info(self) -> List[Dict]:
        """
        Get all machine information by combining getMachinInfoOne and getMachinInfoTwo.

        Returns:
            List[Dict]: Combined machine information
        """
        try:
            # Get info from both endpoints
            info_one = await self.send_command("getMachinInfoOne")
            info_two = await self.send_command("getMachinInfoTwo")

            # Extract data from both responses
            combined_data = []
            if "data" in info_one:
                combined_data.extend(info_one["data"])
            if "data" in info_two:
                combined_data.extend(info_two["data"])

            # Sort by property_id for consistent ordering
            combined_data.sort(key=lambda x: x.get("property_id", 0))

            return combined_data
        except Exception as e:
            logger.error(f"Error getting machine info: {str(e)}")
            return []

    async def get_formatted_info(self) -> None:
        """
        Get all machine information and display it in a nicely formatted table.
        """
        try:
            # Get combined data
            combined_data = await self.get_all_machine_info()

            if not combined_data:
                print("No information available")
                return

            # Calculate column widths
            id_width = 4  # Width for ID column
            key_width = max(20, max(len(item.get("unikey", "")) for item in combined_data))
            name_width = 30  # Width for human-readable name
            value_width = 30  # For formatted value
            raw_width = 10  # For raw value

            # Print table header
            header = (f"{'ID':{id_width}} | {'Property Key':{key_width}} | {'Human Name':{name_width}} | "
                      f"{'Value':{value_width}} | {'Raw Value':{raw_width}}")
            separator = "-" * (id_width + key_width + name_width + value_width + raw_width + 12)  # +12 for separators

            print("\n" + separator)
            print(header)
            print(separator)

            # Process and print each property
            for item in combined_data:
                prop_id = item.get("property_id", "")
                unikey = item.get("unikey", "")
                human_name = PROPERTY_NAME_MAPPING.get(unikey, unikey)  # Use unikey as fallback
                raw_value = item.get("value", "")

                # Parse definition to get friendly value
                friendly_value = self._get_friendly_value(item)

                # Format and print the row
                row = (f"{prop_id:{id_width}} | {unikey:{key_width}} | {human_name:{name_width}} | "
                       f"{friendly_value:{value_width}} | {str(raw_value):{raw_width}}")
                print(row)

            print(separator + "\n")

        except Exception as e:
            logger.error(f"Error formatting machine info: {str(e)}")
            print(f"Error: {str(e)}")

    def _get_friendly_value(self, item: Dict) -> str:
        """
        Extract a user-friendly value from a property item.

        Args:
            item: Property item from machine info

        Returns:
            str: User-friendly value
        """
        try:
            raw_value = item.get("value")
            definition_str = item.get("definition", "")
            unikey = item.get("unikey", "")

            # If no definition, just return the raw value as string
            if not definition_str:
                return str(raw_value)

            # Parse the definition JSON
            try:
                definition = json.loads(definition_str)
            except:
                return str(raw_value)

            # For enum-like definitions (list of options)
            if isinstance(definition, list) and all(isinstance(d, dict) for d in definition):
                # Check if it's a simple on/off or status type
                if len(definition) == 2 and any("0" == str(d.get("value")) for d in definition) and any(
                        "1" == str(d.get("value")) for d in definition):
                    # It's likely a boolean/status field
                    for option in definition:
                        if str(option.get("value")) == str(raw_value):
                            if raw_value == 1 or raw_value == "1":
                                # Status is ON/active
                                status = option.get("en_title") or option.get("title") or "ON"
                                return f"{status} ({raw_value})"
                            else:
                                # Status is OFF/inactive
                                status = option.get("en_title") or option.get("title") or "OFF"
                                return f"{status} ({raw_value})"

                # For other enum types (like battery type, mode, etc.)
                for option in definition:
                    if str(option.get("value")) == str(raw_value):
                        # Prefer English title if available
                        if "en_title" in option:
                            return f"{option['en_title']} ({raw_value})"
                        elif "title" in option:
                            return f"{option['title']} ({raw_value})"

                # If no match found, return raw value
                return str(raw_value)

            # For range-like definitions with units
            unit = ""
            for def_item in definition:
                if isinstance(def_item, dict) and (def_item.get("title") == "单位" or def_item.get("title") == "unit"):
                    unit = def_item.get("value", "")

            if unit:
                # Special case handling
                if unikey == "total_power":
                    return f"{raw_value} {unit}"
                elif unikey in ["dianya", "cm_voltage", "jz_voltage", "hf_out_voltage"]:
                    return f"{raw_value} {unit}"
                elif unikey == "temperature":
                    return f"{raw_value} °C"
                else:
                    return f"{raw_value} {unit}"

            # Default fallback
            return str(raw_value)

        except Exception as e:
            logger.error(f"Error getting friendly value: {str(e)}")
            return str(item.get("value", ""))

    async def set_charge_mode(self, mode: int) -> bool:
        """
        Set the charge mode.

        Args:
            mode: The mode to set (0: manual, 1: auto, 2: timing, 3: straight out)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = await self.send_command(
                "setPropertyData",
                {"id": 35, "value": mode}
            )

            # Check for successful response
            if response.get("code") == 200:
                logger.info(f"Successfully set charge mode to {mode}")
                return True
            else:
                logger.error(f"Failed to set charge mode: {response}")
                return False

        except Exception as e:
            logger.error(f"Error setting charge mode: {str(e)}")
            return False

    async def get_machine_info(self) -> Dict:
        """
        Get machine information.

        Returns:
            Dict: Machine information
        """
        try:
            return await self.send_command("getMachinInfoTwo")
        except Exception as e:
            logger.error(f"Error getting machine info: {str(e)}")
            return {}

    async def get_charge_mode(self) -> Optional[int]:
        """
        Get the current charge mode.

        Returns:
            Optional[int]: The current charge mode or None if retrieval fails
        """
        try:
            response = await self.get_machine_info()

            if "data" in response:
                for item in response["data"]:
                    if item.get("property_id") == 35:
                        mode = item.get("value")
                        mode_names = {0: "manual", 1: "auto", 2: "timing", 3: "straight out"}
                        mode_name = mode_names.get(mode, f"unknown ({mode})")
                        logger.info(f"Current charge mode: {mode_name} ({mode})")
                        return mode

            logger.error("Charge mode not found in response")
            return None

        except Exception as e:
            logger.error(f"Error getting charge mode: {str(e)}")
            return None

    async def get_load_state(self) -> Optional[int]:
        """
        Get the current load state.

        Returns:
            Optional[int]: The current load state or None if retrieval fails
        """
        try:
            response = await self.get_machine_info()

            if "data" in response:
                for item in response["data"]:
                    if item.get("property_id") == 37:
                        state = item.get("value")
                        logger.info(f"Current load state: {state}")
                        return state

            logger.error("Load state not found in response")
            return None

        except Exception as e:
            logger.error(f"Error getting load state: {str(e)}")
            return None

    async def message_listener(self):
        """Listen for incoming messages and handle them."""
        while self.running:
            try:
                if self.connected and self.websocket:
                    message = await self.websocket.recv()
                    data = json.loads(message)
                    logger.debug(f"Received message: {data}")
                    # Handle specific message types here if needed
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error in message listener: {str(e)}")
                    # Reconnect logic could be added here
                break

    def print_help(self):
        """Print available commands for interactive mode."""
        print("\nAvailable commands:")
        print("  get-mode             - Get the current charge mode")
        print("  set-mode <mode>      - Set charge mode (0: manual, 1: auto, 2: timing, 3: straight out)")
        print("  get-load             - Get the current load state")
        print("  info                 - Get all machine information")
        print("  help                 - Show this help message")
        print("  exit                 - Exit the program")
        print()

    async def run(self, command: str, value: Optional[int] = None) -> bool:
        """
        Run command: connect, execute a command, disconnect.

        Args:
            command: The command to execute
            value: Optional value for the command

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to the server
            if not await self.connect():
                return False

            # Execute the command
            result = False
            if command == "set-charge-mode" and value is not None:
                result = await self.set_charge_mode(value)
            elif command == "get-charge-mode":
                mode = await self.get_charge_mode()
                result = mode is not None
            elif command == "get-load-state":
                state = await self.get_load_state()
                result = state is not None
            elif command == "get-info":
                # This will print the formatted info table
                await self.get_formatted_info()
                result = True
            else:
                logger.error(f"Unknown command: {command}")
                result = False

            # Disconnect
            await self.disconnect()
            return result

        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            await self.disconnect()
            return False

async def main():
    """Parse command-line arguments and run the client."""
    parser = argparse.ArgumentParser(description="Solar Charge Controller Client")
    parser.add_argument("--url", default=DEFAULT_WEBSOCKET_URL,
                        help=f"Websocket URL (default: {DEFAULT_WEBSOCKET_URL})")
    parser.add_argument("--mac", required=True,
                        help="Device MAC address (required)")
    parser.add_argument("--command", choices=["get-info", "set-charge-mode", "get-charge-mode", "get-load-state"],
                        help="Command to execute")
    parser.add_argument("--value", type=int,
                        help="Value for the command (if applicable)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create client
    client = SolarControllerClient(args.url, args.mac)

    if not args.command:
        parser.error("--command is required")

    success = await client.run(args.command, args.value)
    return 0 if success else 1



if __name__ == "__main__":
    # Handle keyboard interrupt gracefully
    def signal_handler(sig, frame):
        print("\nExiting...")
        sys.exit(0)


    signal.signal(signal.SIGINT, signal_handler)

    # Run the main function
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)