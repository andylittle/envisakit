#!/usr/bin/env python 

from ademco.connection import AdemcoServerConnection
from ademco.response import AdemcoResponse
from ademco.server import AdemcoServer
from ademco.common import RUNLOOP_INTERVAL_RAPID

import time
import sys
import getopt
import json

EXIT_INTERNAL_FAILURE = 254
EXIT_NETWORK_FAILURE = 253
EXIT_SUCCESS = 0
EXIT_BAD_REQUEST = 1
EXIT_KEYBOARD = 2
EXIT_ALARM_NOT_READY = 10

COMMAND_TIMEOUT = 20


def handler_status(server, sec):

    last_update = server.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)
    if last_update is not None:

        if server.config_use_json:
            print json.dumps(last_update.update_dict())
        else:
            print last_update.update_summary()

        return True
    else:
        return None


def handler_ensure_armed(server, sec):

    last_update = server.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)

    if last_update is None:
        return None
    else:
        if last_update.update_is_armed():
            return True
        else:
            if sec < COMMAND_TIMEOUT:
                return None
            else:
                return False


def handler_ensure_disarmed(server, sec):

    last_update = server.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)

    if last_update is None:
        return None
    else:
        if not last_update.update_is_armed():
            return True
        else:
            if sec < COMMAND_TIMEOUT:
                return None
            else:
                return False


def handler_ensure_bypass(server, sec):

    last_update = server.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)
    
    if last_update is None:
        return None
    else:
        if last_update.update_is_bypass():
            return True
        else:
            if sec < COMMAND_TIMEOUT:
                return None
            else:
                return False


def handler_none(server, sec):
    return True


COMMAND_HANDLERS = (
    (AdemcoServer.COMMAND_ARM_AWAY, handler_ensure_armed),
    (AdemcoServer.COMMAND_ARM_STAY, handler_ensure_armed),
    (AdemcoServer.COMMAND_ARM_NIGHT, handler_ensure_armed),
    (AdemcoServer.COMMAND_ARM_INSTANT, handler_ensure_armed),
    (AdemcoServer.COMMAND_ARM_MAX, handler_ensure_armed),
    (AdemcoServer.COMMAND_DISARM, handler_ensure_disarmed),
    (AdemcoServer.COMMAND_BYPASS, handler_ensure_bypass),
    (AdemcoServer.COMMAND_TOGGLE_CHIME, handler_none),
    (AdemcoServer.COMMAND_TEST, handler_none),
)


def main():

    # Create the ademco server object
    conn = AdemcoServer()

    # Process command line arguments
    command = process_cli_arguments(conn)

    if conn.command_requires_parameter(command) and len(conn.config_param) < 1:
        print >> sys.stderr, "Selected command requires parameter (use -x ####)"
        usage(EXIT_BAD_REQUEST)
    
    # Use configuration file to configure connection
    conn.connect(conn.config_host, conn.config_port, conn.config_password)

    # This is a function we call after our initial command processing
    command_callback = None

    iter_count = 0

    while True:
        iter_count += 1
        try:
            # Determine whether we are still connected
            state = conn.connection_state()

            if state == AdemcoServerConnection.STATE_DISCONNECTED:
                print >> sys.stderr, "Connection terminated"
                sys.exit(EXIT_NETWORK_FAILURE)

            elif state == AdemcoServerConnection.STATE_CONNECTED:

                # Send/receive data in queue and process responses
                conn.process_connection()
                conn.process_queue()

                # If we have not issued any commands
                if command_callback is None:

                    ready = conn.is_ready_for_command(command)
                    if ready is True or conn.config_force:
                        # Issue the command and determine the post-command handling
                        command_callback = process_cli_command(conn, command)
                    elif ready is False:
                        print >> sys.stderr, "Error: System not ready for this command."
                        sys.exit(EXIT_ALARM_NOT_READY)

                # If we have already issued a command
                else:
                    # Ask the post-command handler if we are ready to terminate
                    term = command_callback(conn, iter_count * RUNLOOP_INTERVAL_RAPID)
                    if term is True:
                        sys.exit(EXIT_SUCCESS)
                    elif term is False:
                        sys.exit(EXIT_ALARM_NOT_READY)
                    else:
                        # If term is NoneType, then try another runloop
                        pass 

                # Runloop
                time.sleep(RUNLOOP_INTERVAL_RAPID)

            else:
                print >> sys.stderr, "Unexpected error - unexpected state"
                sys.exit(EXIT_INTERNAL_FAILURE)

        except KeyboardInterrupt:
            print >> sys.stderr, "Detected keyboard interrupt - closing connection"
            conn.disconnect()
            sys.exit(EXIT_KEYBOARD)


def usage(exit_code):
    '''

    Displays usage information and quits with exit_code.

    '''
    print >> sys.stderr, ""
    print >> sys.stderr, "Usage: %(script)s COMMAND [-p PIN] [-c config_file] [-f] [-x extra-parameter] [-j]" % {'script': sys.argv[0]}
    print >> sys.stderr, ""
    print >> sys.stderr, "Available commands: " + ", ".join([i[1] for i in AdemcoServer.ADEMCO_COMMANDS])
    print >> sys.stderr, ""
    print >> sys.stderr, "* [-p PIN]: Provide your 4-digit security PIN (required for most commands)"
    print >> sys.stderr, "* [-c config_file]: Specify a configuration file"
    print >> sys.stderr, "* [-f]: Force command to be sent without first checking for READY"
    print >> sys.stderr, "* [-x extra_parameter]: Provide a parameter for the command (e.g., bypass zone #)"
    print >> sys.stderr, "* [-j]: Output JSON (used for status only)"
    sys.exit(exit_code)


def process_cli_arguments(ademcoServer):

    # Get any options on the command line
    try:
        opts, args = getopt.getopt(sys.argv[2:], "jfp:c:x:", ["pin", "config"])
    except getopt.GetoptError as err:
        print >> sys.stderr, str(err)
        usage(EXIT_BAD_REQUEST)

    # Default configuration file name
    config_file_name = "envisakit-config.json"

    # Change configuration file name if specified
    for option, value in opts:

        if option == "-p":
            if len(value) != 4:
                assert False, "PIN must be 4 digits"
            ademcoServer.code = value

        elif option == "-x":
            assert len(value) >= 1, "Parameter must be provided"

            ademcoServer.config_param = value

        elif option == "-f":
            ademcoServer.config_force = True

        elif option == "-j":
            ademcoServer.config_use_json = True

        elif option == "-c":
            config_file_name = value

        else:
            assert False, "unknown option"

    # Open configuration file
    try:
        config = json.load(open(config_file_name))
    except IOError:
        print >> sys.stderr, "Error: Failed to open %s - use -c to specify a custom config file." % config_file_name
        usage(EXIT_BAD_REQUEST)

    # Load configuration
    try:
        ademcoServer.config_host = config["host"]
        ademcoServer.config_port = config["port"]
        ademcoServer.config_password = config["password"]
    except KeyError:
        print >> sys.stderr, "Error: Missing required key. Ensure you have specified: host, port, password"
        usage(EXIT_BAD_REQUEST)

    # Validate commands
    if len(sys.argv) < 2:
        usage(EXIT_BAD_REQUEST)
    if sys.argv[1].startswith('-'):
        usage(EXIT_BAD_REQUEST)

    possible_commands = dict([(i[1], i[0]) for i in AdemcoServer.ADEMCO_COMMANDS])

    try:
        selected_command = possible_commands[sys.argv[1]]
    except KeyError:
        print >> sys.stderr, "Unexpected command: " + str(sys.argv[1])
        usage(EXIT_BAD_REQUEST)

    return selected_command


def process_cli_command(ademcoServer, command_id):

    handlers = dict(COMMAND_HANDLERS)

    if command_id == AdemcoServer.COMMAND_HELP:
        usage(EXIT_BAD_REQUEST)

    elif command_id == AdemcoServer.COMMAND_STATUS:
        return handler_status

    try:
        handler = handlers[command_id]
        ademcoServer.issue_command(command_id, ademcoServer.config_param)
        ademcoServer.clear_responses()
        return handler
    except IndexError:
        raise Exception("Command not implemented")
  

if __name__ == "__main__":
    main()
