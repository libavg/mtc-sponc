#!/usr/bin/env python


import unittest
from Geometry import Line
from libavg import Point2D

def floatEqual (a,b):
    print a,b
    return abs(a-b) < 1e-6


class TestLine(unittest.TestCase):
    def setUp(self):
        pass

    def test_getLength(self):
        a = Line(Point2D(1,2),Point2D(4,2))
        self.assertEqual(a.getLength(), 3.0)

        a = Line((1,2),(1,5))
        self.assertEqual(a.getLength(), 3.0)

        a = Line((0,0),(3,4))
        self.assertEqual(a.getLength(), 5.0)

        a = Line((0,0),(0,0))
        self.assertEqual(a.getLength(), 0.0)

    def test_getAngle(self):
        a = Line((0,0),(3,4))
        self.assert_(floatEqual(a.getAngle(), 0.9272952180016123))

        a = Line((5,0),(3,3))
        self.assert_(floatEqual(a.getAngle(), 2.158798930342464))

        a = Line((4,3),(0,0))
        self.assert_(floatEqual(a.getAngle(), 3.7850937623830774))

        a = Line((3,3),(5,5))
        self.assert_(floatEqual(a.getAngle(), 0.78539816339744817))

        try:
            Line((1,2),(1,2)).getAngle()
        except:
            self.fail("zero length Line.getAngle() threw an exception")

if __name__ == '__main__':
    unittest.main()
