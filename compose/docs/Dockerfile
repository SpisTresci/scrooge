FROM httpd:2.4

RUN apt-get update && apt-get install -y python-sphinx make

ADD ./docs/  /docs/
WORKDIR /docs/
RUN make html
RUN rm -rf /usr/local/apache2/htdocs/
RUN ln -s /docs/_build/html /usr/local/apache2/htdocs
