__author__ = "Artur Fejklowicz"
__copyright__ = "Copyright 2023, The AF Finanzen Project"
__credits__ = ["Artur Fejklowicz"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__maintainer__ = "Artur Fejklowicz"
__status__ = "Production"


import logging

class FileContent:
    content = None
    def __init__(self, raw_content):
        self.raw_content = raw_content

    def get_content(self):
        return self.content

    def transform(self, first_line):


    def transform(self, end_of_file):

