"""
Instagram Client
"""

import codecs
import concurrent.futures
import json
import os
import sys
import urllib
from functools import wraps

from instagram_private_api import Client as AppClient
from instagram_private_api import ClientCookieExpiredError, ClientLoginRequiredError, ClientError

import config


def catch_exceptions(f):
    """Catch errors.
    """

    @wraps(f)
    def catch(*args, **kwargs):
        try:
            f(*args, **kwargs)

        # OS file not found error
        except FileNotFoundError:
            print("Settings.json don't exist.\n")
            exit()

        # Instagram client error
        except ClientError as e:

            # Print error message
            error = json.loads(e.error_response)
            print(error['message'])

            if 'challenge' in error:  # If instagram redirects to challenge page
                print("Please follow this link to complete the challenge: " + error['challenge']['url'])

            if 'message' in error:
                print(error['message'])

            if 'error_title' in error:
                print(error['error_title'])
            exit(1)

    return catch


class InstagramClient:
    target = ""      # target username
    user = ""        # Target account object
    target_id = ""   # Target account id
    is_private = ""  # Is target account private ?
    following = ""   # Am i following target ?

    BASE_OUTPUT_DIR = ""  # Where can i save photos ?
    OUTPUT_DIR = ""       # Folder will be created for target
    CONFIG_DIR = ""       # Where can i find config files ?
    SETTING = ""          # Where can i (read / write) "settings.json" ?

    def __init__(self, output_dir="output", config_dir="config"):
        """
        :param output_dir: Directory name, where to save photos
        :param config_dir: Directory name, Where to find config files
        """

        # Check for output directory, create it if not exists
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        # Get username, password from credentials.ini
        u = config.username()
        p = config.password()

        # Set class attributes
        self.BASE_OUTPUT_DIR = output_dir
        self.CONFIG_DIR = config_dir
        self.SETTING = self.CONFIG_DIR + '/settings.json'
        self.api = None

        # Authenticate to instagram
        # Note: login will assign to self.api
        self.__login__(u, p)

    def set_target(self, target):
        """
        Fetch and set needed information about target, for later work
        :param target: An instagram username
        """
        # Set class attributes
        self.target = target

        # Create target dir path
        self.OUTPUT_DIR = self.BASE_OUTPUT_DIR + '/' + target

        # Check if exists, then create
        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)

        # Target account
        self.user = self.__target_profile__()

        # Target account id
        self.target_id = self.user['id']

        # Is target account private ?
        self.is_private = self.user['is_private']

        # Am i following target ?
        self.following = self.__ami_following_target__()

    @catch_exceptions
    def __login__(self, u, p):
        """
        Login to instagram using private API.
        :param u: Instagram username
        :param p: Instagram Password
        """
        try:  # To handle client errors, like (ClientCookieExpiredError, ...)

            # Read from settings.json file
            settings_file = self.SETTING

            if not os.path.isfile(settings_file):  # Check if file exists, if not, then we will make a new login

                # Settings file does not exist
                print(f"\n WARNING: settings.json not found! Don't worry i'll create one.")

                # Make new login and save cookies to settings.json
                self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                     on_login=lambda x: self.__onlogin_callback__(x, settings_file))

            else:  # If file exists, then load cookies and login

                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=self.__from_json__)

                # Authenticate with cached settings
                self.api = AppClient(
                    username=u, password=p,
                    settings=cached_settings,
                    on_login=lambda x: self.__onlogin_callback__(x, settings_file))

        # Catch if cookies expired or corrupted, then make new login if so
        except (ClientCookieExpiredError, ClientLoginRequiredError):

            # Login expired
            self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                 on_login=lambda x: self.__onlogin_callback__(x, settings_file))

    @catch_exceptions
    def __onlogin_callback__(self, api, new_settings_file):
        """Save login settings to a json file."""

        # Login settings
        cache_settings = api.settings

        # Open file and dumb json there
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.__to_json__)

    @staticmethod
    def __to_json__(python_object):
        """
        From object to json format.
        :param python_object  Object to be transformed into json
        """

        if isinstance(python_object, bytes):

            return {
                '__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}

        raise TypeError(repr(python_object) + ' is not JSON serializable')

    @staticmethod
    def __from_json__(json_object):
        """
        From json format to object.
        :param json_object  Json to be transformed into object
        """

        if '__class__' in json_object and json_object['__class__'] == 'bytes':

            return codecs.decode(json_object['__value__'].encode(), 'base64')

        return json_object

    @staticmethod
    def __process_to_download__(output_dir, download_url, code):
        """
        Given an image url, handles the downloads process of an image
        :param output_dir:  Place where to save an image
        :param download_url:  Download URL to image
        :param code:  Short_code that represents an instagram post
        """

        # Base url that represents an instagram posts
        base_post_url = "https:##www.instagram.com#p#*#"

        # Since we need to reference the actual IG post later, we format the post url to be
        # acceptable as an image name. image name format: __IG post url.jpeg
        end = f"{output_dir}/__{base_post_url.replace('*', code)}.jpeg"

        # Download image
        urllib.request.urlretrieve(download_url, end)

    def download_target_photo(self, limit=-1):
        """
        Download Target's instagram photos.
        :param limit: Max images to download
        """

        counter = 0

        # Get a list of photos
        # target_photos returns a list of tuples (url, short_code)
        image_urls = self.target_photos()
        image_urls = image_urls[: -1 if limit > len(image_urls) else limit]

        for item in image_urls:
            url, post_code = item[0], item[1]

            # Download the image, using multithreading
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(self.__process_to_download__(self.OUTPUT_DIR, url, post_code))

            # Write progress message to stdout
            sys.stdout.write("\r+ Downloading instagram photo %i/%i" % (counter, len(image_urls)))
            sys.stdout.flush()
            counter += 1

        print(f"\n+ Downloaded {counter} photos. Saved in {self.OUTPUT_DIR}\n")

        return self.OUTPUT_DIR

    def target_photos(self):
        """
        Get a list of all Target's instagram photos.
        :return: List of Urls
        """

        if not self.__ami_allowed__():  # Check if target photos are not private

            # Image data from api
            data = []

            # Get user feed photos and add them to data
            result = self.api.user_feed(str(self.target_id))
            data.extend(result.get('items', []))

            # Pagination
            next_max_id = result.get('next_max_id')

            while next_max_id:  # Get all user feed photos

                results = self.api.user_feed(str(self.target_id), max_id=next_max_id)

                data.extend(results.get('items', []))

                next_max_id = results.get('next_max_id')

            # Extract image urls
            urls = []

            try:  # To handle Attribute, Key errors

                for item in data:

                    if "image_versions2" in item:

                        urls.append((item["image_versions2"]["candidates"][0]["url"], item['code']))

                    else:  # Handle Multiple images in one post (Carousel)

                        carousel = item["carousel_media"]

                        for i in carousel:  # Loop through images

                            urls.append((i["image_versions2"]["candidates"][0]["url"], item['code']))

            except AttributeError:  # Catch and pass (ignore)
                pass

            except KeyError:  # Catch and pass (ignore)
                pass

            return urls
        return

    def __ami_following_target__(self):
        """
        Check if i'm currently following the target.
        :return True OR False
        """
        if str(self.target_id) == self.api.authenticated_user_id:
            return True

        # Retrieve target IG account information, in order to check for following status
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})

        return self.api._call_api(endpoint)['user_detail']['user']['friendship_status']['following']

    def __ami_allowed__(self):
        """
        Check if account is private or not.
        :return True OR False
        """
        return self.is_private and not self.following

    def __target_profile__(self):
        """
        Get target profile information, user_id and is_private account status
        :return: Dict {id! <id>, is_private: <True or False>}
        """

        # Get target username info
        content = self.api.username_info(self.target)
        user = dict()

        # Only extract id & is_private
        user['id'] = content['user']['pk']
        user['is_private'] = content['user']['is_private']

        return user

    def cleanup(self):
        """Cleanup output directory."""
        import shutil
        shutil.rmtree(self.OUTPUT_DIR)
