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

# Configure EnvisaKit (see Configuration section)
$ cp cli/envisalink-config.json.sample cli/envisalink-config.json
$ nano envisalink-config.json

```


# Configuration

Configuration sample:

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
