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

Depth
    Depth describe on which level offers are located.

    Example of XML with depth 0:
    
    .. code-block:: html
    
        <root>
            <product></product>
            <product></product>
        </root>


    Example of XML with depth 1:
    
    .. code-block:: html
    
        <root>
          <group>
            <product></product>
            <product></product>
          </group>
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

XML Data Fields
    Required XML Data Fields
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
        Descr    
    
XMLDataField
------------
