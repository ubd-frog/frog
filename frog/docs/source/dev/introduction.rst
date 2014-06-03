.. _introduction:

Introduction
============

Frog is a simple server/client setup and most of the work is done on the client.  The server is simply a `REST API <http://en.wikipedia.org/wiki/Representational_state_transfer>`_ for the client(s) to work with.  There are only a couple URLs which will render HTML, the rest will return a standardized `JSON <http://www.json.org/>`_ serialized response object.


Response
--------

::

    {
        "isSuccess": true,    // Did the request succeed
        "isError": false,     // Did the request fail
        "message": "",        // A string relevent to the request result
        "values": [],         // A list of objects.  This will always contain the object in "value"
        "value": {}           // An object.  If the request was for a list, this will be the first
                                 member of the list
    }
