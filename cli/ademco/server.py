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
    COMMAND_ARM_INSTANT = 102
    COMMAND_ARM_MAX = 103

    COMMAND_STATUS = 200
    COMMAND_HELP = 201
    
    # Command ID, CLI command, Keypad command, Requires Ready, Help String
    ADEMCO_COMMANDS = (
        (COMMAND_DISARM, "disarm", "1", False),
        # (COMMAND_BYPASS, "bypass", "6", True),
        # (COMMAND_TOGGLE_CHIME, "togglechime", "9", True),
        # (COMMAND_TEST, "test", "5", True),
        # (COMMAND_CODE, "code", "8", True),
        (COMMAND_ARM_AWAY, "arm", "2", True),
        (COMMAND_ARM_STAY, "partial", "3", True),
        (COMMAND_ARM_INSTANT, "instant", "7", True),
        (COMMAND_ARM_MAX, "max", "4", True),
        (COMMAND_STATUS, "status", None, False),
        (COMMAND_HELP, "help", None, False),
    )

    def __init__(self):
        self.code = None
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

    def issue_command(self, command_id):
        if self.code is None:
            raise Exception("Alarm code not specified")

        commands = dict([(i[0], i[2]) for i in self.ADEMCO_COMMANDS])
        self.connection.add_command(self.code + commands[command_id])

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

    def is_ready_for_command(self, command):
        requires_ready = dict([(i[0], i[3]) for i in self.ADEMCO_COMMANDS])

        if requires_ready[command] is True:

            last_update = self.last_response_of_type(AdemcoResponse.RESPONSE_UPDATE)
            if last_update is None:
                return None

            return last_update.update_is_ready()
        else:
            return True

            








