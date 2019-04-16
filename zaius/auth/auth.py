# -*- coding: utf-8 -*-
"""
Produce auth structures that other parts of the API consume.
"""

import configparser
import os


def default():
    """
    Load authentication information from $HOME/.zaius_api
    """
    return from_file(os.path.join(os.environ["HOME"], ".zaius_api"))


def from_file(path):
    """
    Load authentication information

    Args:
        path (str): Filename to load

    Returns:
        dict: The authorization structure
    """
    if not os.path.exists(path):
        raise ValueError("{} does not exist".format(path))

    config = configparser.ConfigParser()
    config.read(path)
    auth = config["auth"]
    return {
        "aws_access_key_id": auth["aws_access_key_id"],
        "aws_secret_access_key": auth["aws_secret_access_key"],
        "zaius_secret_key": auth["zaius_secret_key"],
    }
