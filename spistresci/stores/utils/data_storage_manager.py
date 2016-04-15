import os
from datetime import datetime
from git import Repo

from django.conf import settings


class data_storage_manager:

    def __init__(self, store_name, filename):
        self.store_name = store_name
        store_storage_dir = os.path.join(settings.ST_STORES_DATA_DIR, store_name)

        os.makedirs(store_storage_dir, exist_ok=True)

        if not os.path.exists(os.path.join(store_storage_dir, '.git/')):
            self.repo = Repo.init(store_storage_dir)
        else:
            self.repo = Repo(store_storage_dir)

        self.filepath = os.path.join(store_storage_dir, filename)

    def __enter__(self):
        self.file = open(self.filepath, 'wb')
        return self.file

    def __exit__(self, type, value, traceback):
        self.file.close()

        self.repo.index.add([self.filepath])

        commit_date = datetime.now()
        commit_datetime_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = "Store: {}\nDate: {}".format(self.store_name, commit_datetime_str)

        self.repo.index.commit(commit_msg)
        self.repo.create_tag(commit_date.strftime('%Y-%m-%d'))
