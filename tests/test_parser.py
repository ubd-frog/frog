

import pytest
from django.db.models import Q

def parse(string):
    return []

# -- Objects
a = ['foo']
b = ['foo', 'bar']
c = ['bar', 'baz']
d = ['baz']
e = ['foo', 'bar', 'baz', 'bit']




def test_parser():
    assert parse('Foo and Bar and Baz') == [['Foo', 'Bar', 'Baz']]
    # -- []
    o = Q(name='foo')
    o &= Q(name='bar')
    o &= Q(name='baz')

    assert parse('Foo and Bar or Baz') == [['Foo', 'Bar'], ['Baz']]
    # -- [b, c, d]
    o = Q(name='foo')
    o &= Q(name='bar')
    o |= Q(name='baz')

    assert parse('Foo or Bar or Baz') == [['Foo'], ['Bar'], ['Baz']]
    # -- [a, b, c, d]
    o = Q(name='foo')
    o |= Q(name='bar')
    o |= Q(name='baz')

    assert parse('Foo or Bar and Baz') == [['Foo'], ['Bar', 'Baz']]
    # -- [a, b, c] -> [c]
    o = Q(name='foo')
    o |= Q(name='bar')
    o &= Q(name='baz')

    assert parse('Foo and (Bar or Baz)') == [['Foo', 'Bar', 'Baz']]
    # -- [b, c, d] -> [b]
    o = Q(name='foo')
    o &= (Q(name='bar') | Q(name='baz'))

    assert parse('Foo and Bar and (Baz or Bit)')
    # -- [b, e]        -> [e]           -> [e]
    # -- (foo and bar) -> (bar and baz) -> (baz or bit)
    o = Q(name='foo')
    o &= Q(name='bar')
    o &= (Q(name='baz') | Q(name='bit'))

