.. _views:

Views
=====


Gallery
-------

Galleries are simply collections of pieces.  They are displayed in order of creation and can share pieces between them.  Galleries can have sub galleries that can old specific sets of images, then can be promoted to the parent Gallery.

.. automodule:: frog.views.gallery
    :members:


Piece
-----

A piece is either an Image or a Video and is made abstract so you can add more asset types if you'd like.  A piece represents one thumbnail in Frog.

.. automodule:: frog.views.piece
    :members:


Tag
---

All objects are tagged.  As your data set grows, hierarchial navigation becomes combersome and inefficient.  Users will almost always resort to search of some sort.

.. automodule:: frog.views.tag
    :members:


Comment
-------

Frog implements a basic comment system for each Piece.

.. automodule:: frog.views.comment
    :members: