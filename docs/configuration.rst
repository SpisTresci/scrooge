Configuration
=============


Adding new Store
----------------

Before you will be able to add new store, you have to first configure DataSource which will be responsible for providing information how to get data about latest offers from this store.

Defining new DataSource
-----------------------

Right now matadata about products/offers can be imported from XML files. However architecture of SpisTresci supports multiple formats of input data. If you need a support for different format of API, please `create an Issue on our github`_. You can also provide a support for new formats on your own by providing custom classes which will be derived from `DataSourceModel`_ and `DataSourceImpl`_ classes.

.. _create an Issue on our github: https://github.com/SpisTresci/SpisTresci/issues/new 
.. _DataSourceModel: ../spistresci/datasource/models.py
.. _DataSourceImpl: ../spistresci/datasource/generic.py

To create DataSource for new Store, go to admin panel and click `+Add` next to DataSource of desired type.

.. image:: images/datasource_add.png


XMLDataSource
-------------

XMLDataField
------------
