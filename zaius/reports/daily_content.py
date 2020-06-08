# -*- coding: utf-8 -*-
"""Daily Marketing Content Report

Aggregates performance of Daily marketing content in the specified campaign_schedule_run_ts period.
"""

import csv
import datetime
import re

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
            "marketing_content_sale_numbers"
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
            and ts >= {start_date_s}
            and campaign_id= '9097'
          )
        order by value
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        current_value = None
        current_marketing_content_category = None
        current_marketing_content_header = None
        current_marketing_content_sale_numbers = None
        current_user_click = None
        last_user_click = None
        count_content = 0
        count_click = 0
            
        for row in rows:
            if re.search("sothebys.com", row["value"]): 
                if current_value == None:
                    current_value = row
                if row["value"] == current_value["value"]:
                    
                    if row["action"] == 'content':
                        current_marketing_content_category = row["marketing_content_category"]
                        current_marketing_content_header = row["marketing_content_header"]
                        current_marketing_content_sale_numbers = row["marketing_content_sale_numbers"]
                        count_content += 1
                    elif row["action"] == 'click':
                        current_user_click = (row['zaius_id'], row['value'])
                        if current_user_click != last_user_click:
                            count_click += 1
                            last_user_click = current_user_click
                
                if row["value"] != current_value["value"]:
                    if count_content != 0:
                        writer.writerow(
                            {
                                "count of assignments": count_content,
                                "content link": current_value["value"],
                                "count of unique clicks": count_click,
                                "click through rate (%)": count_click / count_content * 100,
                                "marketing content category": current_marketing_content_category,
                                "marketing_content_header": current_marketing_content_header,
                                "marketing_content_sale_numbers": current_marketing_content_sale_numbers
                            }
                        )
                    current_value = row
                    count_content = 0 
                    count_click = 0

    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=datetime.timezone.utc
        )


ReportSpec.register(DailyContent())
