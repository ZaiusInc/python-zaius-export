# -*- coding: utf-8 -*-
"""Authentication

This module provides convenience methods for building the authentication
data structure required by other modules in this library.

Example:
    # build the default zaius authentication structure
    default()
    > { "aws_access_key_id": "***", "aws_secret_access_key": "***", "zaius_secret_key": "***" }
"""

from .auth import *
