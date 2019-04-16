#!/usr/bin/env python3
"""Zaius Export Command Line Interface

Interface to run pre-baked reports from the command line.
"""

import sys
import argparse

import zaius.reports as reports
import zaius.auth as auth
import zaius.export as export


def main():
    """CLI entry point"""

    parser = argparse.ArgumentParser(description="zaius-export command line utility")
    parser.add_argument("--auth", help="file containing zaius credentials")
    parser.add_argument("--output", help="file to write the report into")

    subparsers = parser.add_subparsers(dest="report", help="name of the report")
    subparsers.required = True
    for report in reports.SPECS:
        report.register_args(subparsers)
    args = parser.parse_args()

    if args.auth:
        auth_struct = auth.from_file(args.auth)
    else:
        auth_struct = auth.default()

    if args.output:
        output = open(args.output, "wt")
    else:
        output = sys.stdout

    args.func(export.API(auth_struct), output, args)


if __name__ == "__main__":
    main()
