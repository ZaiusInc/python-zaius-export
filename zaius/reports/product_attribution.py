from .spec import ReportSpec

class ProductAttribution(ReportSpec):
    def register_args(self, parser):
        parser = parser.add_parser(
            'product-attribution',
            help='individual purchases attributed to the 3-day last touched campaign',
        )

        parser.add_argument('start_date', help='earlist date. included in the report.')
        parser.add_argument('end_date', help='latest date. not included in the report.')

    def execute(self, api, destination, args):
        pass

ReportSpec.register(ProductAttribution())
