from abc import ABC, abstractmethod
from subprocess import Handle


class OutputFile(ABC):

    @abstractmethod
    def convert(self):
        pass

class DocFile(OutputFile):

    def convert(self):
        # Convert Doc to HTML + Image
        # Convert HTML + Image to Text
        pass

class ImageFile(OutputFile):
    def convert(self):
        # Read text in image
        pass

class OtherFile(OutputFile):

    def convert(self):
        # Read text directly from file
        # Handle unreadable file
        pass

class FileFactory():

    @staticmethod
    def get_output_file(file_type):
        if file_type == 'application/vnd.google-apps.document':
            return DocFile()
        elif file_type.startswith('image/'):
            return ImageFile()
        else:
            return OtherFile()