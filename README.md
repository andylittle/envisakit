# EnvisaKit

EnvisaKit is a command-line interface for the [Eyez-On Envisalink](http://www.eyezon.com) module. It allows you to arm and disarm the alarm system, as well as custom commands.

# HomeKit and Siri

Connect EnvisaKit to HomeKit in order to control your alarm panel through Siri.

1. Install EnvisaKit (see below)
2. Install [HomeBridge](https://github.com/nfarina/homebridge)
3. Install the [homebridge-envisakit plugin](https://github.com/mklips0/homebridge-envisakit)

# Installation

```

# Clone the repository
$ git clone 'https://github.com/mklips0/envisakit.git'

# Create virtual env
$ cd envisakit
$ virtualenv venv

# Activate virtual env
$ source venv/bin/activate

# Install python packages
$ pip install -r requirements.txt

# EITHER
# (1) Configure EnvisaKit for EZMOBILE (see Configuration section)
$ cp cli/envisalink-config.json.sample cli/envisalink-config.json
$ nano envisalink-config.json

# OR
# (2) Configure EnvisaKit for Ademco (see Configuration section)
$ cp cli/envisalink-ademco-config.json.sample cli/envisalink-ademco-config.json
$ nano envisalink-ademco-config.json

```

# Usage

```

# Arming the system with code 1234
$ ./envisakit-cli arm -p 1234
Detecting commands...
Detecting arm types...
Issuing command...

# Disarming the system with code 1234
$ ./envisakit-cli disarm -p 1234
Detecting commands...
Detecting arm types...
Issuing command...

# Getting the status of the system
$ ./envisakit-cli status
ready

```


# Configuration

EnvisaKit works through either the Ademco TPI (preferred) or the EZMOBILE interface.

Configuration sample for Ademco TPI (envisalink-ademco-config.json):

```

{
	"host": "envisalink",
	"port": 4025,
	"password": "1234"
}

```

* "host": Hostname or IP of the Envisalink module
* "port": Port for the Envisalink TPI (default: 4025)
* "password": Password for the Envisalink TPI (default: "user")


Configuration sample for EZMOBILE (envisalink-config.json):

```

{
	"mobile-url": "https://www.eyez-on.com/EZMOBILE/index.php",
	"mid": "abcdefghijklmnopqrstuvwxyz01234567890000",
	"did": "000000000000",
	"partition": "1",
	"ignore": ["instantarm", "maxarm", "bypass", "togglechime", "test", "code"],
	"only": ["arm", "disarm"]
}

```

Fields: 

* "mobile-url": The base URL of your Envisalink mobile portal. This can be generated on your [account page](https://www.eyez-on.com/EZMAIN/accountdetails.php?action=genmobilebrowselink)
* "mid": 40-character security code. Found in the mobile URL after "&mid=".
* "did": 12-character Envisalink MAC address.
* "partition": Partition number.
* "ignore": Blacklist specified commands from Envisakit. Excluding commands which are never used will speed up the execution of commands. Do not use with "only".
* "only": Whitelist specified commands from Envisakit. Whitelisting needed commands will speed up the execution of commands. Do not use with "ignore".
