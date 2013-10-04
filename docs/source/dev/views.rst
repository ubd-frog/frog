.. _views:

Views
=====


Gallery
-------

Galleries are simply collections of pieces.  They are displayed in order of creation and can share pieces between them.  Galleries can have sub galleries that can old specific sets of images, then can be promoted to the parent Gallery.

Gallery API

::

    GET     /        Lists the galleries currently visible by the current user
    POST    /        Creates a gallery object
    GET     /id      Gallery object if visible by the current user
    PUT     /id      Adds image or video objects to the gallery
    DELETE  /id      Removes image or video objects from the gallery
    GET     /filter  Returns a filtered list of image and video objects


Piece
-----

A piece is either an Image or a Video and is made abstract so you can add more asset types if you'd like.  A piece represents one thumbnail in Frog.

Piece API

::

    GET     /image/id  Returns a rendered page displaying the requested image
    GET     /video/id  Returns a rendered page displaying the requested video
    POST    /image/id  Add tags to an image object
    POST    /video/id  Add tags to an video object
    DELETE  /image/id  Flags the image as deleted in the database
    DELETE  /video/id  Flags the video as deleted in the database


Tag
---

All objects are tagged.  As your data set grows, hierarchial navigation becomes combersome and inefficient.  Users will almost always resort to search of some sort.

Tag API

::

    GET     /        Lists all tags
    POST    /        Creates a Tag object
    PUT     /        Adds tags to guids
    DELETE  /        Removes tags from guids
    GET     /search  Search tag list
    GET     /manage  Renders a form for adding/removing tags
    POST    /manage  Adds and removes tags from guids and commits data


Comment
-------

Frog implements a basic comment system for each Piece.

Comment API

::

    GET     /        Returns a rendered list of comments
    GET     /id      Returns a serialized comment
    POST    /id      Creates a comment for an object
    PUT     /id      Updates the content of the comment