
import random

import pytest

from frog.models import cropBox, squareCropDimensions, FROG_THUMB_SIZE


@pytest.mark.django_db
def test_cropBox():
    for i in range(10000):
        width = random.randrange(FROG_THUMB_SIZE, 2048)
        height = random.randrange(FROG_THUMB_SIZE, 2048)
        box = cropBox(width, height)

        assert box[2] - box[0] == FROG_THUMB_SIZE
        assert box[3] - box[1] == FROG_THUMB_SIZE
        assert box[2] - box[0] == box[3] - box[1]

@pytest.mark.django_db
def test_inverseDimensions():
    for i in range(10000):
        width = random.randrange(FROG_THUMB_SIZE, 2048)
        height = random.randrange(FROG_THUMB_SIZE, 2048)
        w, h = squareCropDimensions(width, height)

        assert w == FROG_THUMB_SIZE or h == FROG_THUMB_SIZE
