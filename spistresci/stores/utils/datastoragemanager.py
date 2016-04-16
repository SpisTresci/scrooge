import os
from contextlib import contextmanager
from datetime import datetime
from git import Repo

from django.conf import settings


class DataStorageManager:

    def __init__(self, store_name):
        self.store_name = store_name
        self.store_storage_dir = os.path.join(settings.ST_STORES_DATA_DIR, store_name)

        os.makedirs(self.store_storage_dir, exist_ok=True)

        if not os.path.exists(os.path.join(self.store_storage_dir, '.git/')):
            self.repo = Repo.init(self.store_storage_dir)
        else:
            self.repo = Repo(self.store_storage_dir)
            self.__asert_is_clean()

    @contextmanager
    def save(self, filename):
        self.__asert_is_clean()
        filepath = os.path.join(self.store_storage_dir, filename)

        file = open(filepath, 'wb')
        yield file

        file.close()
        self.repo.index.add([filepath])

        commit_date = datetime.now()
        commit_datetime_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = "Store: {}\nDate: {}".format(self.store_name, commit_datetime_str)

        self.repo.index.commit(commit_msg)

    def get(self, filename):
        self.__asert_is_clean()

        filepath = os.path.join(self.store_storage_dir, filename)
        with open(filepath) as f:
            return f.read()

    def __asert_is_clean(self):
        assert not self.repo.is_dirty(), "Repository '{}' is dirty. " \
            "Has to be cleaned up before further work.".format(self.store_storage_dir)
