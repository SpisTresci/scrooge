from spistresci.datasource.generic import DataSource


def get_data_source_classes():
    subclasses = sorted(DataSource.get_all_subclasses().keys())
    assert 'XmlDataSource' in subclasses  # XmlDataSource is default, so we want to make sure it is available
    return zip(subclasses, subclasses)
