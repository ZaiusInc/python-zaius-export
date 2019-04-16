from .spec import ReportSpec

class Demo(ReportSpec):
    def register_args(self, parser):
        parser = parser.add_parser('demo', help='a demo report that ensures everything is working')
        parser.set_defaults(func=self.execute)

    def execute(self, api, destination, args):
        destination.write("it worked!\n")

ReportSpec.register(Demo())
