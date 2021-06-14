from isearch import InstagramClient, FaceRecognition
import os
import click


# Config paths
BASE_DIR = os.getcwd()
CONFIG_DIR = BASE_DIR + '/config'


def load_files(dir_path):
    """Load files form a dir path."""
    assert os.path.exists(dir_path)
    return [f"{dir_path}/{file}" for file in os.listdir(dir_path)]


def build_image_url(image_name):
    """Build url from image name."""
    return image_name.split('__')[-1][:-5].replace('#', '/')


@click.command()
@click.argument('known_people_folder')
@click.argument('target_username')
@click.option('--limit', default=-1, help='Number of photos to Download and process from target_profile')
def main(known_people_folder, target_username, limit):

    target_face, ig_profile = known_people_folder, target_username

    # Authenticate to instagram
    client = InstagramClient(config_dir=CONFIG_DIR)

    # Set target to ig_profile
    client.set_target(ig_profile)

    print()  # for better stdout display

    # returns path to the downloaded photos
    output = client.download_target_photo(limit=limit)

    recon = FaceRecognition()

    # generator yield match if found.
    for match in recon.find_matches(load_files(target_face), load_files(output)):
        click.echo(" Possible match [{}]".format(build_image_url(match)))

    client.cleanup()  # Delete downloaded photos


if __name__ == '__main__':
    main()
