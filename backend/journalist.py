import json
import logging


class Journalist:
    def __init__(self, journal_path):
        self.journal_path = journal_path  # path to direcotry containing journal files
