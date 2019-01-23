import maya.cmds as cmds
from cmt.test import TestCase


class HelloWorldCase(TestCase):
    def test_hello_world(self):
        self.assertTrue(True)
