GAPIC Proto Compiler Plugin
================================

.. image:: https://img.shields.io/travis/googleapis/protoc-java-resource-names-plugin.svg
    :target: https://travis-ci.org/googleapis/protoc-java-resource-names-plugin

The GAPIC Proto Compiler Plugin is used to add functionality to protobuf
generated types. The additional functionality is required by client libraries
generated using the GAPIC code generation tool, which reside in the
`Toolkit`_ repository.

Currently, this means generating resource name types in Java. The new resource
name types will be accessible via getter and setter methods added to the
generated types.

.. _`Toolkit`: https://github.com/googleapis/toolkit/


Python Versions
---------------

GAPIC Proto Compiler Plugin is currently tested with Python 2.7, 3.4, 3.5 and 3.6.


Contributing
------------

Contributions to this library are always welcome and highly encouraged.

See the `CONTRIBUTING`_ documentation for more information on how to get started.

.. _`CONTRIBUTING`: https://github.com/googleapis/proto-compiler-plugin/blob/master/CONTRIBUTING.rst


Versioning
----------

This library follows `Semantic Versioning`_

It is currently in major version zero (``0.y.z``), which means that anything
may change at any time and the public API should not be considered
stable.

.. _`Semantic Versioning`: http://semver.org/


License
-------

BSD - See `LICENSE`_ for more information.

.. _`LICENSE`: https://github.com/googleapis/proto-compiler-plugin/blob/master/LICENSE
