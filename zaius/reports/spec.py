class ReportSpec:
    specs = []

    def register_args(self, parser):
        raise ValueError('not implemented')

    def execute(self, api, destination, args):
        raise ValueError('not implemented')

    @classmethod
    def register(kls, report_spec):
        kls.specs.append(report_spec)
