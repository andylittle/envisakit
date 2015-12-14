#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import sys
import getopt
import json

#
# Command IDs
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

            if link_string in EZMOBILE_COMMANDS_IGNORE:
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
        try:
            return commands[command_argument]
        except KeyError:
            return COMMAND_UNKNOWN

    def discovered_command_help_and_labels(self):
        '''

        Provides a list of all discovered CLI commands and a help string (list of tuples).

        '''
        script_commands = dict([(i[1], i[2]) for i in EZMOBILE_COMMANDS])
        script_command_help = dict([(i[1], i[3]) for i in EZMOBILE_COMMANDS])
        return [(script_commands[i], script_command_help[i]) for i in self.discoveredCommands]

    def issue(self, command_id, **kwargs):
        '''

        Issues the specified alarm command. 
        Specify additional form fields through kwargs.

        '''

        # Do not process the command if it is unknown
        if command_id == COMMAND_UNKNOWN:
            print "[Error] Cannot issue unknown command"
            return None

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
    print "Usage: %(script)s: command code [-c/--config config_file]" % {'script': sys.argv[0]}

    if ma is None:
        return

    print "--"
    print "Detected commands: "
    print "***"
    for (action, label) in ma.discovered_command_help_and_labels():
        print "%(action)s - %(help)s" % {'action': action, 'help': label}


def main():
    '''

    Reads configuration and attempts to issue the alarm command requested on the CLI.

    '''

    # Get any options on the command line
    try:
        opts, args = getopt.getopt(sys.argv[3:], "c:", ["config"])
    except getopt.GetoptError as err:
        print str(err)
        help(None)
        sys.exit(2)

    # Default configuration file name
    config_file_name = "envisalink-config.json"

    # Change configuration file name if specified
    for option, value in opts:
        if option == "-c":
            config_file_name = value
        else:
            assert False, "unknown option"

    # Open configuration file
    try:
        config = json.load(open(config_file_name))
    except IOError:
        print "Error: Failed to open %s - use -c to specify a custom config file."
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

    # Discover alarm commands
    print "Detecting alarm commands..."
    ma.discover_commands()
    ma.discover_arm_commands()

    # If we're not asked for a command, print usage
    if len(sys.argv) < 2:
        help(ma)
        exit(1)

    # Determine requested command
    command_id = ma.determine_command(sys.argv[1])
    code = sys.argv[2]

    if len(code) != 4:
        print "Error: Specify a valid code"
        help(ma)
        exit(1)

    # If unknown command, print usage
    if command_id == COMMAND_UNKNOWN:
        help(ma)
        exit(1)

    # Issue the command!
    ma.issue(command_id, pin=code)
    exit(0)


if __name__ == "__main__":
    main()

