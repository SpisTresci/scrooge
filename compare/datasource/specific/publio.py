from spistresci.datasource.generic import XmlDataSourceImpl


class Publio(XmlDataSourceImpl):
    xml_tag_dict = {
        'external_id': ('./id', ''),
        'title': ('./title', ''),
        'authors': ('./authors', ''),
        'formats': ('./formats', ''),
        'protection': ('./protectionType', ''),
        'price': ('./price', ''),
        'url': ('./productUrl', ''),
        'cover': ('./imageUrl', ''),
        'isbns': ('./isbns', ''),
        'publisher': ('./company', ''),
        'category': ('./categories/category', ''),
    }
