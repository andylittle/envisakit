#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import sys
import getopt
import json

#
# Recognized Command IDs
#

COMMAND_UNKNOWN = 0
COMMAND_DISARM = 1
COMMAND_BYPASS = 2
COMMAND_TOGGLE_CHIME = 3
COMMAND_TEST = 4
COMMAND_CODE = 5
COMMAND_CUSTOM = 6
COMMAND_ARM_AWAY = 100
COMMAND_ARM_STAY = 101
COMMAND_ARM_INSTANT = 102
COMMAND_ARM_MAX = 103

COMMAND_BUILTINS = 500
COMMAND_GETSTATUS = 501
COMMAND_HELP = 502

#
# EZMOBILE commands to ignore
#

EZMOBILE_COMMANDS_IGNORE = [
    "cancel"
]

#
# Supported EZMOBILE commands
#
# Format: (EZMobile Name, Command ID, CLI Command, CLI Help String)
#

EZMOBILE_COMMANDS = (
    ("away arm", COMMAND_ARM_AWAY, "arm", "Arms the entire partition"),
    ("stay arm", COMMAND_ARM_STAY, "partial", "Arms the perimeter of the partition"),
    ("instant arm", COMMAND_ARM_INSTANT, "instantarm", "Unknown"),
    ("max", COMMAND_ARM_MAX, "maxarm", "Unknown"),
    ("off", COMMAND_DISARM, "disarm", "Disarms the entire partition"),
    ("bypass", COMMAND_BYPASS, "bypass", "Bypasses a zone"),
    ("toggle chime", COMMAND_TOGGLE_CHIME, "togglechime", "Unknown"),
    ("test", COMMAND_TEST, "test", "Tests the partition"),
    ("code", COMMAND_CODE, "code", "Configure a code"),
    ("custom", COMMAND_CUSTOM, "sequence", "Enter a custom sequence"),
)

#
# Commands supported by the script
#
# Format: (CLI Command, Command ID, CLI Help String)
#

BUILTIN_COMMANDS = (
    ("status", COMMAND_GETSTATUS, "Gets the status of the partition"),
    ("help", COMMAND_HELP, "Lists all possible commands"),
)


class MobileAlarm:

    def __init__(self, url, mid, did, partition):
        self.url = url
        self.mobileIdentifier = mid
        self.deviceIdentifier = did
        self.partition = partition

        self.discoveredCommands = []
        self.commandActions = {}
        self.commandMethods = {}
        self.commandFormData = {}
        self.commandFormSlots = {}
        self.ignoreCommands = list(EZMOBILE_COMMANDS_IGNORE)

    @classmethod
    def _fetch_page_dom(self, url):
        '''

        Fetches the specified URL (HTTP GET) and returns the response
        in a BeautifulSoup HTML DOM object.

        '''
        response = urllib2.urlopen(url)
        html = response.read()
        dom = BeautifulSoup(html)
        return dom

    @classmethod
    def _post_page(self, url, method, data):
        '''

        Fetches the specified URL (HTTP GET) and returns the response
        in a urllib2 response object.

        '''
        data = urllib.urlencode(data)
        headers = {}
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        return response

    def _fetch_command_page(self):
        '''

        Fetches the EZMOBILE command page and returns the response
        in a BeautifulSoup HTML DOM object.

        '''
        url = '%(url)s?mid=%(mid)s&did=%(did)s&part=%(partition)s&action=partcommands' % {
            'url': self.url,
            'mid': self.mobileIdentifier,
            'did': self.deviceIdentifier,
            'partition': self.partition, 
        }
        return MobileAlarm._fetch_page_dom(url=url)

    def _fetch_arm_page(self):
        '''

        Fetches the EZMOBILE arm command page and returns the response
        in a BeautifulSoup HTML DOM object.

        '''
        url = '%(url)s?mid=%(mid)s&did=%(did)s&part=%(partition)s&action=armconfirm' % {
            'url': self.url,
            'mid': self.mobileIdentifier,
            'did': self.deviceIdentifier,
            'partition': self.partition,
        }
        return MobileAlarm._fetch_page_dom(url=url)

    def _discover_command_form(self, url, command_id):
        '''

        Fetches the command form at the specified URL and associates
        the form at the URL with the specified command_id.

        Populates the command action, method, and inputs for the command.

        '''

        # Get the DOM of the link href
        command_dom = self._fetch_page_dom(url=url)

        # Look into form
        form = command_dom.find('form')

        # Get form action & method
        self.commandActions[command_id] = form.get('action')
        self.commandMethods[command_id] = form.get('method')

        # Add this command to our discovered commands
        self.discoveredCommands += [command_id]

        # Get all hidden inputs and non-hidden inputs
        inputs = form.findAll('input')

        # Look at the inputs
        hidden_inputs = []
        slots = []
        for input_field in inputs:
            if "hidden".lower() in input_field.get('type').lower():
                hidden_input = (input_field.get('name'), input_field.get('value'))
                hidden_inputs += [hidden_input]
            else:
                slots += [input_field.get('name')]

        self.commandFormData[command_id] = hidden_inputs
        self.commandFormSlots[command_id] = slots

    def _discover_commands_in_dom(self, dom):
        '''

        Fetches the EZMOBILE command page and discovers actions available.

        '''
        links = dom.findAll('a')

        # Link strings that we should be matching against
        match_strings = [i[0].lower() for i in EZMOBILE_COMMANDS]

        # Map from link names to command IDs
        command_ids = dict([(i[0], i[1]) for i in EZMOBILE_COMMANDS])

        for link in links:
            link_string = link.string.lower()

            if link_string in self.ignoreCommands:
                continue

            if link_string in match_strings:
                command_id = command_ids[link_string]
                self._discover_command_form(url=link.get('href'), command_id=command_id)
            else:
                print "[Warning] Discovered unknown command = " + link.string.lower()

    def discover_arm_commands(self):
        '''

        Discovers all ARM commands from the EZMOBILE portal.
        You must run this method before attempting to execute an ARM command.

        '''

        dom = self._fetch_arm_page()
        self._discover_commands_in_dom(dom)

    def discover_commands(self):
        '''

        Discovers all standard commands from the EZMOBILE portal.
        You must run this method before attempting to execute a standard command.

        '''

        dom = self._fetch_command_page()
        self._discover_commands_in_dom(dom)

    def determine_command(self, command_argument):
        '''

        Provides a command ID for the specified CLI command argument.

        '''
        commands = dict([(i[2], i[1]) for i in EZMOBILE_COMMANDS])
        builtins = dict([(i[0], i[1]) for i in BUILTIN_COMMANDS])

        try:
            return commands[command_argument]
        except KeyError:
            try:
                return builtins[command_argument]
            except KeyError:
                return COMMAND_UNKNOWN

    def discovered_command_help_and_labels(self):
        '''

        Provides a list of all discovered CLI commands and a help string (list of tuples).

        '''
        script_commands = dict([(i[1], i[2]) for i in EZMOBILE_COMMANDS])
        script_command_help = dict([(i[1], i[3]) for i in EZMOBILE_COMMANDS])
        items = [(i[0], i[2]) for i in BUILTIN_COMMANDS]
        items += [(script_commands[i], script_command_help[i]) for i in self.discoveredCommands]
        return items

    def _issue_builtin(self, command_id, **kwargs):
        if command_id == COMMAND_HELP:
            help(self)
            exit(0)
        else:
            print "not implemented"

    def issue(self, command_id, **kwargs):
        '''

        Issues the specified alarm command. 
        Specify additional form fields through kwargs.

        '''

        # Do not process the command if it is unknown
        if command_id == COMMAND_UNKNOWN:
            print "[Error] Cannot issue unknown command"
            return None

        if command_id > COMMAND_BUILTINS:
            return self._issue_builtin(command_id, **kwargs)

        # Get the request method and action from the discovery cache
        command_url = self.commandActions[command_id]
        command_method = self.commandMethods[command_id]

        # Our form data
        command_form = {}

        # List of all of the required form fields for the selected action
        required_slots = self.commandFormSlots[command_id]

        # Include all hidden fields from the discovery cache into our new form data
        for hidden_field in self.commandFormData[command_id]:
            command_form[hidden_field[0]] = hidden_field[1]

        # Add any custom arguments which are required for the form
        for (key, value) in kwargs.iteritems():
            if key in required_slots:
                command_form[key] = value

        # List of all form fields which have been met with the information we have
        filled_slots = command_form.keys()

        # If we're missing any form fields, we cannot continue
        for required_slot in required_slots:
            if required_slot not in filled_slots:
                print "[Error] Missing required field: " + required_slot
                return None

        # Issue the command request
        print "Issuing command..."
        MobileAlarm._post_page(command_url, command_method, command_form)


def help(ma=None):
    '''

    Displays usage information.
    If a MobileAlarm object is specified, it will also display the discovered commands.

    '''
    print ""
    print "Usage: %(script)s COMMAND [-p PIN] [-c config_file] [-f key=value]" % {'script': sys.argv[0]}
    print ""
    # print "-p PIN: Specify the 4-digit PIN used to issue the command (if required for the command)"
    # print "-c config_file: Specify a configuration file (see envisalink-config.json.sample for more details)"
    # print "-f key=value: Specify additional fields that may be required for the command, e.g., -f sequence=12345"
    # print ""

    if ma is None:
        return

    print "Detected commands: "
    print ""
    for (action, label) in ma.discovered_command_help_and_labels():
        print "* %(action)s - %(help)s" % {'action': action, 'help': label}

    if len(ma.ignoreCommands) > len(EZMOBILE_COMMANDS_IGNORE):
        print ""
        print "Note: Some commands have been hidden by your config file."
        print ""


def main():
    '''

    Reads configuration and attempts to issue the alarm command requested on the CLI.

    '''

    # Get any options on the command line
    try:
        opts, args = getopt.getopt(sys.argv[2:], "hp:c:f:", ["pin", "config", "field"])
    except getopt.GetoptError as err:
        print str(err)
        help(None)
        sys.exit(2)

    # Default configuration file name
    config_file_name = "envisalink-config.json"

    # Extra fields
    extra_fields = {}

    # Change configuration file name if specified
    for option, value in opts:

        if option == "-p":
            if len(value) != 4:
                assert False, "PIN must be 4 digits"
            extra_fields["pin"] = value

        elif option == "-c":
            config_file_name = value

        elif option == "-f":
            keyvalue = value.split('=')

            if len(keyvalue) != 2:
                assert False, "fields must be in key=value format"

            extra_fields[keyvalue[0]] = keyvalue[1]
        else:
            assert False, "unknown option"

    # Open configuration file
    try:
        config = json.load(open(config_file_name))
    except IOError:
        print "Error: Failed to open %s - use -c to specify a custom config file." % config_file_name
        help(None)
        exit(1)

    # Load configuration
    try:
        CONFIG_URL = config["mobile-url"]
        CONFIG_MID = config["mid"]
        CONFIG_DID = config["did"]
        CONFIG_PARTITION = config["partition"]
    except KeyError:
        print "Error: Missing required key. Ensure you have specified: mobile-url, mid, did, partition"
        help(None)
        exit(1)

    # Initialize mobile alarm object
    ma = MobileAlarm(CONFIG_URL, CONFIG_MID, CONFIG_DID, CONFIG_PARTITION)

    # Load optional configurations
    try:
        ignore_cli_commands = config["ignore"]
        cli_commands = dict([(i[2], i[0]) for i in EZMOBILE_COMMANDS])
        ignore_commands = [cli_commands[i] for i in ignore_cli_commands]
        ma.ignoreCommands += ignore_commands
    except:
        pass

    # If we're not asked for a command, print usage
    if len(sys.argv) < 2:
        help(ma)
        exit(1)

    # Determine requested command
    command_id = ma.determine_command(sys.argv[1])

    # If we don't recognize the command (i.e., not a builtin command), detect possible commands
    if command_id == COMMAND_UNKNOWN or command_id == COMMAND_HELP:

        # Discover alarm commands
        print "Detecting commands..."
        ma.discover_commands()

        # Discover arming commands
        print "Detecting arm types..."
        ma.discover_arm_commands()

        # Re-determine requested command, now that we have the full set
        command_id = ma.determine_command(sys.argv[1])

    # If unknown command, print usage
    if command_id == COMMAND_UNKNOWN:
        help(ma)
        exit(1)

    # Issue the command!
    ma.issue(command_id, **extra_fields)
    exit(0)


if __name__ == "__main__":
    main()

