from django_docopt_command import DocOptCommand


class Command(DocOptCommand):
    docs = '''Usage:
    fetch_store_products <store_name>...
    fetch_store_products --all
    '''

    def handle_docopt(self, aruments):
        pass
