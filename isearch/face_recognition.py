from isearch.api import (load_image_file,
                         face_locations,
                         face_encodings,
                         compare_faces, )
import PIL
import numpy as np


class FaceRecognition:
    MODEL = "hog"  # Fast but low on accuracy, other can be 'cnn', high accuracy and low speed (on CPU && fast on GPU)
    TOLERANCE = 0.6

    @staticmethod
    def train_known_faces(known_faces):
        """
        Given an image, locate faces and get a 128-dimension face encodings
        :param known_faces: List of images to be processed.
        """
        # List of encodings
        encodings = []

        # We go through the list of known-faces images, then load each image
        # get encodings and append to encodings
        for img in known_faces:
            # Loads an image file (.jpg, .png, etc) into a numpy array
            image = load_image_file(img)

            # returns a list of found faces, for this purpose we take first face only (assuming one face per image)
            encodings.append(face_encodings(image)[0])

        # return list of encodings
        return encodings

    @staticmethod
    def process_unknown_faces(unknown_faces, model):
        """
        Given an image, locate faces and get a 128-dimension face encodings
        :param unknown_faces: List of images to be processed.
        :param model: Which face detection model to use. "hog" is less accurate but faster on CPUs. "cnn" is a more
                      accurate deep-learning model which is GPU/CUDA accelerated (if available). The default is "hog".
        :return: Generator with encodings.
        """

        # List of 128-dimension encodings
        all_encodings = []

        # We go through the list of unknown-faces images, then load each image
        # get encodings, face_locations
        for image in unknown_faces:

            # Loads an image file (.jpg, .png, etc) into a numpy array, then
            np_image = load_image_file(image)

            # Scale down image to gain some speed.
            if max(np_image.shape) > 1600:
                pil_img = PIL.Image.fromarray(np_image)
                pil_img.thumbnail((1600, 1600), PIL.Image.LANCZOS)
                np_image = np.array(pil_img)

            # Locate all faces in image
            locations = face_locations(np_image, model=model)

            # Since we know face locations, we can pass them to face_encodings as second argument
            # Without that it will search for faces once again
            encodings = face_encodings(np_image, locations)

            # If face found yield a tuple with face encodings, original image
            if encodings:
                yield encodings, image

    def find_matches(self, known_faces, unknown_faces):
        """
        Compare a list of face encodings against a candidate encoding to see if they match.
        :param known_faces: List of images of a person
        :param unknown_faces: List of images to compare
        :return: Generator
        """

        # Contains list if a 128-dimension face encodings for all found faces in known_faces.
        known_faces_encodings = self.train_known_faces(known_faces)

        # Compare unknown_faces to the list of known_face encodings to check for a match
        for fc_encodings, original_image in self.process_unknown_faces(unknown_faces, self.MODEL):

            # A list of True/False values indicating which known_face_encodings is a positive match
            for fc_enc in fc_encodings:

                # List of tur false values
                result_array = compare_faces(known_faces_encodings, fc_enc, tolerance=self.TOLERANCE)

                if any(result_array):  # If there is a match, yield

                    yield original_image
