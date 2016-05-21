from spistresci.datasource.generic import XmlDataSource


class Woblink(XmlDataSource):
    depth = 1

    xml_tag_dict = {
        'external_id': ('@id', ''),
        'price': ('@price', 0),
        'url': ('@url', ''),
        'availability': ('@avail', ''),
        'category': ('./cat', ''),
        'title': ('./name', ''),
        'cover': ('./imgs/main/@url', ''),
        'description': ('./desc', ''),
        'isbns': ("./attrs/a[@name='ISBN']", ''),
        'publisher': ("./attrs/a[@name='Wydawnictwo']", ''),
        'formats': ("./attrs/a[@name='Format']", ''),
    }
