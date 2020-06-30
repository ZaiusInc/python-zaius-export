# -*- coding: utf-8 -*-
"""Daily Marketing Content Report

Aggregates performance of Daily marketing content in the specified campaign_schedule_run_ts period.
"""

import csv
import datetime
import re
import urllib.parse as parse
from .spec import ReportSpec


class DailyContent(ReportSpec):
    """Daily Marketing Content Report"""

    def register_args(self, parser):
        parser = parser.add_parser(
            "daily-content"
            # help="individual purchases attributed to the 3-day last touched campaign"
        )
        # parser.add_argument("campaign_id",
        #                     help="the ID of the campaign to get metrics for",
        #                     default='9097')
        parser.add_argument("start_date", help="earlist date, YYYY-MM-DD, inclusive")
        parser.add_argument("end_date", help="latest date, YYYY-MM-DD, exclusive")
        parser.set_defaults(func=self.execute)

    # pylint: disable=R0914
    def execute(self, api, destination, args):
        columns = [
            "count of assignments",
            "content link",
            "count of unique clicks",
            "click through rate (%)",
            "marketing content category",
            "marketing_content_header",
            "marketing_content_sale_numbers",
        ]
        writer = csv.DictWriter(destination, columns)
        writer.writeheader()

        start_date = self._parse_date(args.start_date)
        end_date = self._parse_date(args.end_date)

        # build our query
        params = {
            "start_date_s": int(start_date.timestamp()),
            "end_date_s": int(end_date.timestamp()),
        }
        stmt = """
        select
            zaius_id,
            action,
            event_type,
            value,
            campaign_schedule_run_ts,
            campaign_id,
            marketing_content_category,
            marketing_content_header,
            campaign,
            marketing_content_sale_numbers

        from events
        where
          (
            event_type = 'marketing_email'
            and action = 'content'
            and campaign_schedule_run_ts >= {start_date_s}
            and campaign_schedule_run_ts < {end_date_s}
          )
          or (
            event_type = 'email'
            and action = 'click'
            and ts >= {start_date_s}
            and campaign_schedule_run_ts >= {start_date_s}
            and campaign_schedule_run_ts < {end_date_s}
            and campaign_id= '9097'
          )
        order by value, zaius_id, action
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        def output_key(row):
            """generates an equality comparable value that uniquely identifies if an output
            row depends on this input row"""
            url = parse.urlparse(row["value"])
            qparams = parse.parse_qs(url.query)
            return (qparams.get('utm_content', 'empty'),)

        def element_key(row):
            """generates an equality comparable value that uniquely identifies if a user's stats
            within this output_key depend on this input row"""
            return (output_key(row), row["zaius_id"])

        def update_meta(meta, row):
            if meta is None and row["action"] == "content":
                # capture the metadata
                return {
                    "content link": row["value"],
                    "marketing content category": row["marketing_content_category"],
                    "marketing_content_header": row["marketing_content_header"],
                    "marketing_content_sale_numbers": row[
                        "marketing_content_sale_numbers"
                    ],
                }
            else:
                # no change
                return meta

        def merge_element(current_output, current_element):
            """mutates output to contain the contribution from the user represented in the
            current element"""
            for key, value in current_element.items():
                current_output[key] = current_output.get(key, 0) + value

        def write_result(writer, current_output, current_output_meta):
            if current_output is None or current_output_meta is None:
                # we can't output if we're missing a row requirement. This typically happens
                # when we observe a click against a campaign that we've never seen a send
                # for.
                return

            if "count of assignments" in current_output:
                ctr = (
                    float(current_output.get("count of unique clicks", 0) * 100)
                    / current_output["count of assignments"]
                )
            else:
                ctr = 0
            writer.writerow({
                **current_output_meta,
                **current_output,
                "click through rate (%)": ctr,
            })

        last_output_key = None
        last_element_key = None
        current_element = {}
        current_output = None
        current_output_meta = None

        for row in rows:
            if not re.search("sothebys.com", row["value"]):
                continue
            this_output_key = output_key(row)
            this_element_key = element_key(row)

            if this_element_key != last_element_key:
                # update the current output with this element
                merge_element(current_output, current_element)

                # reset the current element
                current_element = {}

            if this_output_key != last_output_key:
                # emit our current output
                write_result(writer, current_output, current_output_meta)
                current_output = {}
                current_output_meta = None

            # update the current element with this row
            if row["action"] == "content":
                current_element["count of assignments"] = 1
            if row["action"] == "click":
                current_element["count of unique clicks"] = 1

            current_output_meta = update_meta(current_output_meta, row)
            last_output_key = this_output_key
            last_element_key = this_element_key

        # flush the final row
        merge_element(current_output, current_element)
        write_result(writer, current_output, current_output_meta)

    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(DailyContent())
