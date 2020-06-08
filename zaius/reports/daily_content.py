# -*- coding: utf-8 -*-
"""Daily Marketing Content Report

Aggregates performance of Daily marketing content in the specified campaign_schedule_run_ts period.
"""

import csv
import datetime
from collections import Counter

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
            "marketing content category"
        ]
        writer = csv.DictWriter(destination, columns)
        writer.writeheader()

        start_date = self._parse_date(args.start_date)
        end_date = self._parse_date(args.end_date)

        # build our query
        params = {
            "start_date_s": int(start_date.timestamp()),
            "end_date_s": int(end_date.timestamp())
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
            and campaign_schedule_run_ts >= {start_date_s}
            and campaign_schedule_run_ts < {end_date_s}
            and campaign_id= '9097'
          )
        order by value
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        current_value = None
        current_action = None
        current_row = None

        count_content = 0
        count_click = 0

        # def write_to_csv():
        #     writer.writerow(
        #         {
        #             "count of assignments": count_content,
        #             "content link": current_value,
        #             "count of unique clicks": count_click
        #         }
        #     )
            
        for row in rows:
            if current_value == None:
                current_value = row["value"]
            while row["value"] == current_value:
                if row["action"] == 'content':
                    count_content += 1
                elif row["action"] == 'click':
                    count_click += 1



            # if row["value"] == current_value:
            #     if row["action"] == 'content':
            #         count_content += 1
            #     elif row["action"] == 'click':
            #         count_click += 1
            if row["value"] != current_value:
                writer.writerow(
                    {
                        "count of assignments": count_content,
                        "content link": current_value,
                        "count of unique clicks": count_click
                    }
                )
                current_value == row["value"]
                count_content = 0 
                count_click = 0

    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(DailyContent())
