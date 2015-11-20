# coding: utf-8
from django.test import TestCase
from parkkeeper.base import StoppableMixin


class StoppableMixinTestCase(TestCase):

    def test_stop(self):
        stoppable = StoppableMixin()
        self.assertFalse(stoppable.is_stopped())

        stoppable.stop()
        self.assertTrue(stoppable.is_stopped())