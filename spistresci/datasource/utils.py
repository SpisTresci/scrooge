from spistresci.datasource.generic import DataSourceImpl


def get_data_source_classes():
    subclasses = sorted(DataSourceImpl.get_all_subclasses().keys())
    assert 'XmlDataSourceImpl' in subclasses  # XmlDataSourceImpl is default, so we want to make sure it is available
    return zip(subclasses, subclasses)
