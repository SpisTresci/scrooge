from django_docopt_command import DocOptCommand


class Command(DocOptCommand):
    docs = '''Usage:
    update_store_products <store_name>...
    update_store_products --all
    '''

    def handle_docopt(self, aruments):
        pass
