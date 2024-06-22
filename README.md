Introduction
------------

A vector clock is a data structure used for determining the partial
ordering of events in a distributed system and detecting causality
violations.

See https://en.wikipedia.org/wiki/Vector_clock.

This implements a vector where each process has its own clock.

A typical description will have the counter start from 1 and increment by
1 every time there is a change.

However, this implementation allows the counter increase by whatever the
client asks for.  Our processes can set the counter to their own clock,
hence allow us to resolve conflicts (unordered changes) by leaning towards
later (more recent) object versions.

Testing
-------

```
python -m unittest discover -s tests
```

Building
--------

```
python -m pip install --upgrade build
python -m build
```

See also https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives.

Uploading to pypi
-----------------

```
python -m pip install twine
twine check dist/*
```
