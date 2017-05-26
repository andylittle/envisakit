# EnvisaKit

EnvisaKit is a command-line interface for the [Eyez-On Envisalink](http://www.eyezon.com) module with Honeywell Vista panels. It allows you to arm and disarm the alarm system, as well as custom commands.

**Note**: This project _is not_ compatible with DSC security panels.

# Installation

```

# Clone the repository
$ git clone 'https://github.com/andylittle/envisakit.git'
$ cd envisakit

# Create virtual env and install packages
$ apt install virtualenv
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt

# Configure EnvisaKit (see Configuration section)
$ cp envisakit-config.json.sample envisakit-config.json
$ vi envisakit-config.json

```

# Usage

```

# Arming the system with code 1234
$ ./envisakit-cli arm -p 1234
Sending command: 12342

# Disarming the system with code 1234
$ ./envisakit-cli disarm -p 1234
Sending command: 12341

# Getting the status of the system
$ ./envisakit-cli status
Ready
AC Present

# Output JSON
$ ./envisakit-cli status -j
{"alarm_in_memory": false, "faulted": false, "in_alarm": false, "fire": false, "low-battery": false, "arm-mode": "disarmed", "ac-present": true, "bypassed": false, "system-trouble": false, "ready": true, "chime": false, "armed": false}

```


# Configuration

EnvisaKit works through the Ademco Third-Party Interface (TPI) running on the Envisalink module.

Configuration sample:

```

{
	"host": "envisalink",
	"port": 4025,
	"password": "1234"
}

```

* "host": Hostname or IP of the Envisalink module (required, default: "envisalink")
* "port": Port for the Envisalink TPI (required, default: 4025)
* "password": Password for the Envisalink TPI (required, default: "user")




