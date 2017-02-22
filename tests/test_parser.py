import re

import pytest
from django.db.models import Q
# from frog.models import Gallery, Image, Video


def parseUserInput(string):
    string = string.lower()
    # -- Split by and to get buckets
    buckets = string.split(' and ')
    ors = []
    for bucket in buckets:
        ors.append(bucket.replace(' or ', '|'))

    url = '+'.join(ors)

    return url


def dumps(url):
    query = []
    buckets = url.split('+')
    for bucket in buckets:
        query.append(bucket.split('|'))

    return query


# -- Objects
a = ['foo']
b = ['foo', 'bar']
c = ['bar', 'baz']
d = ['baz']
e = ['foo', 'bar', 'baz', 'bit']

USER_INPUT = "Foo and Bar and Baz"
QUERY = [['Foo', 'Bar', 'Baz']]
URL = "Foo+Bar+Baz"

# USER_INPUT > URL > QUERY
#              URL > QUERY


def test_parser():
    userinput = 'Foo and Bar and Baz'
    query = [['foo'], ['bar'], ['baz']]
    url = "foo+bar+baz"
    assert parseUserInput(userinput) == url
    assert dumps(url) == query
    # -- [e]

    # userinput = 'Foo and Bar or Baz'
    # query = [['foo', 'baz'], ['bar', 'baz']]
    # url = "foo+bar|baz"
    # assert parseUserInput(userinput) == url
    # assert dumps(url) == query

    userinput = 'Foo or Bar and Baz'
    query = [['foo', 'bar'], ['baz']]
    url = "foo|bar+baz"
    assert parseUserInput(userinput) == url
    assert dumps(url) == query

    userinput = 'Foo or Bar or Baz'
    query = [['foo', 'bar', 'baz']]
    url = "foo|bar|baz"
    assert parseUserInput(userinput) == url
    assert dumps(url) == query

    userinput = 'Foo or Bar or Baz and Bit'
    query = [['foo', 'bar', 'baz'], ['bit']]
    url = "foo|bar|baz+bit"
    assert parseUserInput(userinput) == url
    assert dumps(url) == query

    userinput = 'Foo'
    query = [['foo']]
    url = "foo"
    assert parseUserInput(userinput) == url
    assert dumps(url) == query


    # query = [['Foo', 'Bar'], ['Baz']]
    # assert parseUserInput('Foo and Bar or Baz') == query
    # assert dumps(query) == "Foo+Bar/Baz"
    # # -- [b, c, d]
    # o = Q(name='foo')
    # o &= Q(name='bar')
    # o |= Q(name='baz')
    #
    # query = [['Foo'], ['Bar'], ['Baz']]
    # assert parseUserInput('Foo or Bar or Baz') == query
    # assert dumps(query) == "Foo/Bar/Baz"
    # # -- [a, b, c, d]
    # o = Q(name='foo')
    # o |= Q(name='bar')
    # o |= Q(name='baz')
    #
    # query = [['Foo'], ['Bar', 'Baz']]
    # assert parseUserInput('Foo or Bar and Baz') == query
    # assert dumps(query) == "Foo/Bar+Baz"
    # # -- [a, b, c] -> [c]
    # o = Q(name='foo')
    # o |= Q(name='bar')
    # o &= Q(name='baz')
    #
    # query = [['Foo', [['Baz'], ['Baz']]]]
    # assert parseUserInput('Foo and (Bar or Baz)') == query
    # assert dumps(query) == "Foo+/Bar/Baz"
    # # -- [a, b, e] -> [b, e]
    # o = Q(name='foo')
    # o &= (Q(name='bar') | Q(name='baz'))
    #
    # query = [['Foo', ['Baz', 'Baz']]]
    # assert parseUserInput('Foo or (Bar and Baz)') == query
    # assert dumps(query) == "Foo/Bar+Baz"
    # # -- [a, b, e, c]
    # o = Q(name='foo')
    # o |= (Q(name='bar') & Q(name='baz'))
    #
    # query = ['Foo', 'Bar', [['Baz'], ['Bit']]]
    # assert parseUserInput('Foo and Bar and (Baz or Bit)') == query
    # assert dumps(query) == "Foo+Bar+/Baz/Bit"
    # # -- [b, e]        -> [e]
    # # -- (foo and bar) -> (baz or bit)
    # o = Q(name='foo')
    # o &= Q(name='bar')
    # o &= (Q(name='baz') | Q(name='bit'))

