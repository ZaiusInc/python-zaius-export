# -*- coding: utf-8 -*-
"""
Wrapper around the zaius export API
"""

import time
import tempfile
import shutil
import logging
import re
import os
import gzip
import csv
import json

import requests
import zaius.auth as auth
from zaius.s3 import list_objects, par_s3_download

from .parser import QUERY_PARSER


class ExecutionError(Exception):
    """
    Thrown if an export-api request fails to run to completion
    """


class API:
    """
    Wraps the Zaius Export API
    """

    ENDPOINT = "https://api.zaius.com/v3/exports"

    def __init__(self, auth_struct=None, log=logging):
        """
        Args:
            auth_struct (dict): authentication structure produced by pyzaius.auth
            log (logging.Logger): destination for log information
        """
        if auth_struct is None:
            auth_struct = auth.default()

        self.auth = auth_struct
        self.log = log

    def query(self, stmt):
        """
        Execute an SQL like query and return a generator rows (represented as dicts)

        Args:
            stmt (string): sql-like query

        Yields:
            (dict) representing each row of the response
        """
        parsed = QUERY_PARSER.parse(stmt)
        return self.query_raw(parsed)

    def query_raw(self, query_dict):
        """
        Execute a raw query of the form expected by the underlying API. See
        https://developers.zaius.com/v3/reference#export-api-overview for more
        details.

        Args:
            query_dict (dict): query structure as defined by api documentation

        Yields:
            (dict) representing each row of the response
        """

        # we only support csv responses
        query_dict = {**query_dict, "format": "csv"}

        # execute query and await completion
        api_resp = self._api_request(query_dict)
        while api_resp.get("state") in ("pending", "running"):
            time.sleep(1)
            api_resp = self._api_status(api_resp)
        if api_resp.get("state") != "completed":
            raise ExecutionError(
                "query did not complete. response=`{}`".format(api_resp)
            )

        # download the files and yield the rows
        try:
            local = tempfile.mkdtemp()
            for path in self._s3_download(api_resp["path"], local):
                with gzip.open(path, "rt") as csv_file:
                    for row in csv.DictReader(csv_file):
                        yield row

        finally:
            shutil.rmtree(local)

    def _api_request(self, query_dict):
        """
        Issue a raw request to the export API and return the raw response
        """
        self.log.info("query:\n{}".format(json.dumps(query_dict, indent=2)))
        resp = requests.post(
            API.ENDPOINT, json=query_dict, headers=self._headers()
        ).json()
        self.log.info("api_request response:\n{}".format(json.dumps(resp, indent=2)))
        if resp.get("status", 200) != 200:
            raise ExecutionError(resp.get("detail", {}).get("message", "unknown error"))

        return resp

    def _api_status(self, req):
        """
        Request the status for a previous raw request and return the raw response
        """
        resp = requests.get(
            "{}/{}".format(API.ENDPOINT, req["id"]), headers=self._headers()
        ).json()
        self.log.info("api_status response:\n{}".format(json.dumps(resp, indent=2)))
        return resp

    def _headers(self):
        """
        Header structure with authentication key
        """
        return {"x-api-key": self.auth["zaius_secret_key"]}

    def _s3_download(self, s3_url, local_path):
        """
        Download everything at s3_url to a local path. Remove metdata file and
        return set of local paths to downloaded content.
        """
        path_parts = re.match(r"s3:\/\/([^/]+)\/(.*)", s3_url)
        bucket = path_parts.group(1)
        prefix = path_parts.group(2)

        kwargs = {"bucket": bucket, "prefix": prefix}
        keys = []
        while True:
            objs = list_objects(self.auth, **kwargs)
            keys.extend([obj["Key"] for obj in objs["Contents"]])
            if "NextContinuationToken" in objs:
                kwargs["ContinuationToken"] = objs["NextContinuationToken"]
            else:
                break
        par_s3_download(self.auth, bucket, keys, local_path)
        os.remove(os.path.join(local_path, "complete.json"))
        return [os.path.join(local_path, p) for p in sorted(os.listdir(local_path))]
