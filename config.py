
import configparser
import sys


try:
    config = configparser.ConfigParser(interpolation=None)
    config.read("config/credentials.ini")
except (FileNotFoundError, BaseException) as e:
    print("Credentials.ini Not found" if type(e) == BaseException else e)
    sys.exit(1)


def username():
    try:
        user = config["Credentials"]["username"]
        if user == '':
            sys.exit(0)
        return user
    except KeyError:
        sys.exit(0)


def password():
    try:
        passwd = config["Credentials"]["password"]
        if passwd == '':
            sys.exit(0)
        return passwd
    except KeyError:
        sys.exit(0)
