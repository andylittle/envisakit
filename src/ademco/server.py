from ademco.response import AdemcoResponse
from ademco.connection import AdemcoServerConnection


class AdemcoServer:

    COMMAND_UNKNOWN = 0
    COMMAND_DISARM = 1
    COMMAND_BYPASS = 2
    COMMAND_TOGGLE_CHIME = 3
    COMMAND_TEST = 4
    COMMAND_CODE = 5
    COMMAND_CUSTOM = 6
    COMMAND_ARM_AWAY = 100
    COMMAND_ARM_STAY = 101
    COMMAND_ARM_NIGHT = 102
    COMMAND_ARM_INSTANT = 103
    COMMAND_ARM_MAX = 104

    COMMAND_STATUS = 200
    COMMAND_HELP = 202
    
    # Command ID, CLI command, Keypad command, Requires Parameter, Requires Ready
    ADEMCO_COMMANDS = (
        (COMMAND_DISARM, "disarm", "1", False, False),
        (COMMAND_BYPASS, "bypass", "6", True, True),
        (COMMAND_TOGGLE_CHIME, "togglechime", "9", False, True),
        (COMMAND_TEST, "test", "5", False, True),
        # (COMMAND_CODE, "code", "8", True, True),
        (COMMAND_ARM_AWAY, "arm", "2", False, True),
        (COMMAND_ARM_STAY, "partial", "3", False, True),
        (COMMAND_ARM_NIGHT, "night", "33", False, True),
        (COMMAND_ARM_INSTANT, "instant", "7", False, True),
        (COMMAND_ARM_MAX, "max", "4", False, True),
        (COMMAND_STATUS, "status", None, False, False),
        (COMMAND_HELP, "help", None, False, False),
    )

    def __init__(self):
        self.code = None
        self.config_force = False
        self.config_use_json = False
        self.config_param = ""
        self.responses = {}
        self.clear_responses()

    def clear_responses(self):
        for rtype in AdemcoResponse.RESPONSE_TYPES:
            self.responses[rtype] = []

    def connect(self, host, port, password):
        self.connection = AdemcoServerConnection(host, port, password)
        self.connection.connect()

    def disconnect(self):
        self.connection.disconnect()

    def last_response_of_type(self, response_type):
        rtlist = self.responses[response_type]
        try:
            return rtlist[0]
        except IndexError:
            return None

    def set_code(self, code):
        self.code = code

    def connection_state(self):
        return self.connection.connection_state()

    def issue_command(self, command_id, parameter=""):
        if self.code is None:
            raise Exception("Alarm code not specified")

        commands = dict([(i[0], i[2]) for i in self.ADEMCO_COMMANDS])
        self.connection.add_command(self.code + commands[command_id] + parameter)

    def process_connection(self):
        self.connection.connection_cycle()

    def process_queue(self):
        response_queue = self.connection.pop_responses()
        for response in response_queue:
            self._process_response(response)

    def _process_response(self, response):

        response_obj = AdemcoResponse()
        if not response_obj.parse(response):
            return

        self.responses[response_obj.response_type()].insert(0, response_obj)

    def command_requires_parameter(self, command):
        requires_ready = dict([(i[0], i[3]) for i in self.ADEMCO_COMMANDS])
        return requires_ready[command]

    def is_ready_for_command(self, command):
        requires_ready = dict([(i[0], i[4]) for i in self.ADEMCO_COMMANDS])

        if requires_ready[command] is True:

            last_update = self.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)
            if last_update is None:
                return None

            return last_update.update_is_ready()
        else:
            return True

            








