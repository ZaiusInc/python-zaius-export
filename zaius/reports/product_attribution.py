# -*- coding: utf-8 -*-
"""Product Purchase Attribution Report

Attribute product purchases to the last email engagement (open or click)
that happened within a 3-day window of the purchase.
"""

import csv
import sys
import datetime

from .spec import ReportSpec


class ProductAttribution(ReportSpec):
    """Product Attribution Report"""

    def register_args(self, parser):
        parser = parser.add_parser(
            "product-attribution",
            help="individual purchases attributed to the 3-day last touched campaign",
        )

        parser.add_argument("start_date", help="earlist date, YYYY-MM-DD, inclusive")
        parser.add_argument("end_date", help="latest date, YYYY-MM-DD, exclusive")
        parser.set_defaults(func=self.execute)

    # pylint: disable=R0914
    def execute(self, api, destination, args):
        writer = csv.DictWriter(
            destination,
            ["campaign", "product_id", "order_id", "email", "quantity", "subtotal"],
        )
        writer.writeheader()

        start_date = self._parse_date(args.start_date)
        end_date = self._parse_date(args.end_date)

        # build our query
        params = {
            "start_date_s": start_date.strftime("%s"),
            "end_date_s": end_date.strftime("%s"),
        }
        stmt = """
        select
            ts,
            user_id,
            product_id,
            order_id,
            customer.email,
            action,
            order_item_quantity,
            campaign,
            order_item_subtotal
        from events
        where 
            ts >= {start_date_s}
            and ts < {end_date_s}
            and (
              (
                event_type = 'email'
                and (
                  action = 'open'
                  or action = 'click'
                )
              )
              or (
                event_type = 'order'
                and action = 'purchase'
                and order.status = 'purchased'
              )
            )
        order by user_id, ts
        """.format(
            **params
        )

        # issue the query
        rows = api.query(stmt)

        # our result comes back ordered by user_id, ts so we can know
        # that we'll see all of one user before we see then next
        current_user = None
        last_engagement = None

        def is_attributed(conv):
            if last_engagement is None:
                return False

            dt_s = int(conv["ts"]) - int(last_engagement["ts"])

            after_engagement = dt_s > 0
            within_window = dt_s < (3 * 24 * 3600)
            return after_engagement and within_window

        idx = 0
        for idx, row in enumerate(rows):
            if idx % 100000 == 0:
                sys.stderr.write("Read {} rows\n".format(idx))

            if row["user_id"] != current_user:
                current_user = row["user_id"]
                last_engagement = None
            if row["action"] in ("open", "click"):
                last_engagement = row
            elif row["action"] == "purchase" and is_attributed(row):
                writer.writerow(
                    {
                        "campaign": last_engagement["campaign"],
                        "product_id": row["product_id"],
                        "order_id": row["order_id"],
                        "email": row["customer.email"],
                        "quantity": row["order_item_quantity"],
                        "subtotal": row["order_item_subtotal"],
                    }
                )
        sys.stderr.write("Read {} rows\n".format(idx))

    # pylint: disable=R0201
    def _parse_date(self, date_str):
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


ReportSpec.register(ProductAttribution())
