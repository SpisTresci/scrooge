Configuration
=============


Adding new Store
----------------

Before you will be able to add new store, you have to first configure DataSource which will be responsible for providing information how to get data about latest offers from this store.

Defining new DataSource
-----------------------

Right now matadata about products/offers can be imported from XML files. However architecture of SpisTresci supports multiple formats of input data. If you need a support for different format of API, please `create an Issue on our github`_. You can also provide a support for new formats on your own by providing custom classes which will be derived from `DataSourceModel`_ and `DataSourceImpl`_ classes.

.. _create an Issue on our github: https://github.com/SpisTresci/SpisTresci/issues/new 
.. _DataSourceModel: ../../spistresci/datasource/models.py
.. _DataSourceImpl: ../../spistresci/datasource/generic.py

To create DataSource for new Store, go to admin panel and click "+Add" next to DataSource of desired type.

.. image:: images/datasource_add.png

**Properties:**

Name
  Each type of DataSource should have own unique name. All other properties are specific for different types of DataSources. Please read documentation for specific DataSource type for more details.

XMLDataSource
-------------

Offers root xpath
    XPath to element which children are offers elements.

    For document below, that would be ``/root``

    .. code-block:: html    

        <root>
            <book></book>
            <book></book>
        </root>

    and in that case, that would be ``/root/offers``

    .. code-block:: html    

        <root>
            <store>
                <location></location>
            <store>
            <offers>
                <offer></offer>
                <offer></offer>
            </offers>
        </root>

Data Source type
    XMLDataSource is capable of extracting data not only from single XML file, but also from archives which contains multiple XML files. With *Data Source type* you can specify behaviour for file downloaded from specified *url*.
    
    Single XML 
        The most basic case, when *Store* expose all products by single XML file as API

Url
    Address from which data will fetched periodically
    
Custom Class
    Sometimes data provided by Store do not suit very well to assumptions which need to be made during design of database. For example, we assumed that each product has unique integer *id* in *Store* database, or each product has name no longer than 256 characters. For sure there are Stores, which can have products with even longer names, or Stores which have alphanumeric ids.

    In such cases, there is no other choice than write some additional code, which will handle those specific cases in desired way. You can find examples of such classes written in Python in `spistresci/datasource/specific`_ directory. Your new custom class should derived from *DataSourceImpl* (directly or indirectly).
    
.. _spistresci/datasource/specific: ../../spistresci/datasource/specific/

XMLDataFields
-------------

Required XML Data Fields
    .. image:: images/datasource_required_xmldatafields.png

    Right now there are exactly four required *XML Data Fields* - *external_id*, *name*, *price*, *url*. That means that you have to provide information (by xpath), how to extract those product metadata. 
    If *Store* which you want to add do not have any of *Required XML Data Fields*, there is no other way - you have to write your own *Custom Class* to hadle such weird case.

    external_id
        is an *id* of product which *Store* uses in own database to identify specific product (name of product is not the best candidate for being a unique identifier, because there can be multiple products with the same name).
    name
        Because products have to be presented somehow to users, that is why we need something like *name* for each product.
    
    price
        Each product should have own price. If some store distributes also some product for free, you can always set default value for price to `0`.
    
    url
        We assume, that each product has own url, where you can find details about it.


Additional XML Data Fields
    .. image:: images/datasource_additional_xmldatafields.png
    
    The great news is that you can store any data about products in the database! :) The only thing which you have to do to is provide the *name* for the property, information how to extract value of this property from XML document (by *xpath*), and default value for property in case if some products will not have matadata for this specific field.
    
    For example, to store information about *size* of product in your database, just create new field with name *size* (or 'dimensions' if you prefer - name of property do not have to be exactly the same as it is in XML document of specific store). You will be able to fetch all additional data stored in database via API.

    
XMLDataFields - XPath
---------------------

XPath (`XML Path Language`_) is a best way to specify how to exctract data from XML document. Let's take a look on few examples. Having fallowing XML Document:

.. _XML Path Language: https://en.wikipedia.org/wiki/XPath
.. code-block:: html
    
    <document>
      <company>
        <ceo>Elon Musk</ceo>
        <employees>13058</employees>
        <address>
          <city>Palo Alto</city>
          <state>California</state>
          <country>USA</country>
        </address>
      </company>
      <products>
        <product>
          <id>2</id>
          <model>Tesla Model S</model>
          <price>63400.00</price>
          <productUrl>https://www.teslamotors.com/models</productUrl>
          <imageUrl>https://www.teslamotors.com/tesla_theme/assets/img/models/section-initial.jpg</imageUrl>
        </product>
        <product>
          <id>3</id>
          <model>Tesla Model X</model>
          <price>69300.00</price>
          <productUrl>https://www.teslamotors.com/modelx</productUrl>
          <imageUrl>https://www.teslamotors.com/tesla_theme/assets/img/modelx/section-exterior-profile.jpg</imageUrl>
        </product>
        <product>
          <id>4</id>
          <model>Tesla Model 3</model>
          <price>35000.00</price>
          <productUrl>https://www.teslamotors.com/model3</productUrl>
          <imageUrl>https://www.teslamotors.com/sites/default/files/images/model-3/gallery/gallery-1.jpg</imageUrl>
        </product>
      </products>
    </document>

with xpath ``/document/products/product/model`` you will get ``['Tesla Model S', 'Tesla Model X', 'Tesla Model 3']``, and similarly with ``/document/products/product/price`` you will get ``['63400.00', '69300.00', '35000.00']``.

Because of the stracture of typical XML like this, ``/document/products/product/`` is redundant in that case in both xpaths above. Moreover, you **have to** specified this part as *offers xpath root* for XMLDataSource.
Nevertheles, thanks to this for all *XML Data Fields* you can now specify relative (and shorter) xpaths: ``./model``, ``./price``.





