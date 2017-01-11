import re

import pytest
from django.db.models import Q


def parse(string):
    return []


def toURL(query):
    return ''


# -- Objects
a = ['foo']
b = ['foo', 'bar']
c = ['bar', 'baz']
d = ['baz']
e = ['foo', 'bar', 'baz', 'bit']

"""
Proposed Changes:

* buckets are ORed together
* bucket members are ANDed together
* A trailing "+" will signal a perenthesis AND
  * This is on the client side
* Support parenthetical queries
  * ["foo", ["bar", "baz"]] AND
  * ["foo", [["bar"], ["baz"]] OR
"""


def test_parser():
    assert parse('Foo and Bar and Baz') == [['Foo', 'Bar', 'Baz']]
    assert toURL([['Foo', 'Bar', 'Baz']]) == "Foo+Bar+Baz"
    # -- []
    o = Q(name='foo')
    o &= Q(name='bar')
    o &= Q(name='baz')

    assert parse('Foo and Bar or Baz') == [['Foo', 'Bar'], ['Baz']]
    assert toURL([['Foo', 'Bar'], ['Baz']]) == "Foo+Bar/Baz"
    # -- [b, c, d]
    o = Q(name='foo')
    o &= Q(name='bar')
    o |= Q(name='baz')

    assert parse('Foo or Bar or Baz') == [['Foo'], ['Bar'], ['Baz']]
    assert toURL([['Foo'], ['Bar'], ['Baz']]) == "Foo/Bar/Baz"
    # -- [a, b, c, d]
    o = Q(name='foo')
    o |= Q(name='bar')
    o |= Q(name='baz')

    assert parse('Foo or Bar and Baz') == [['Foo'], ['Bar', 'Baz']]
    assert toURL([['Foo'], ['Bar', 'Baz']]) == "Foo/Bar+Baz"
    # -- [a, b, c] -> [c]
    o = Q(name='foo')
    o |= Q(name='bar')
    o &= Q(name='baz')

    assert parse('Foo and (Bar or Baz)') == [['Foo', [['Baz'], ['Baz']]]]
    assert toURL([['Foo', [['Baz'], ['Baz']]]]) == "Foo+/Bar/Baz"
    # -- [a, b, e] -> [b, e]
    o = Q(name='foo')
    o &= (Q(name='bar') | Q(name='baz'))

    assert parse('Foo or (Bar and Baz)') == [['Foo', ['Baz', 'Baz']]]
    assert toURL([['Foo', [['Baz'], ['Baz']]]]) == "Foo/Bar+Baz"
    # -- [a, b, e, c]
    o = Q(name='foo')
    o |= (Q(name='bar') & Q(name='baz'))

    assert parse('Foo and Bar and (Baz or Bit)') == ['Foo', 'Bar', [['Baz'], ['Bit']]]
    assert toURL(['Foo', 'Bar', [['Baz'], ['Bit']]]) == "Foo+Bar+/Baz/Bit"
    # -- [b, e]        -> [e]
    # -- (foo and bar) -> (baz or bit)
    o = Q(name='foo')
    o &= Q(name='bar')
    o &= (Q(name='baz') | Q(name='bit'))

