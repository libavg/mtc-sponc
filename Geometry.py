# Copyright (C) 2007
#    Martin Heistermann, <mh at lulzmeister dot de>
#
# This file is part of sponc.
#
# sponc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# sponc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sponc.  If not, see <http://www.gnu.org/licenses/>.


import math
from util import in_between, boundary
from libavg import Point2D

class Box:
    def __init__(self,x,y,width,height):
        self.x=x
        self.y=y
        self.width=width
        self.height=height
    def inbound(self,p):
        """find closest position inside of cage for point p"""
        newx=boundary(p.x,self.x, self.x+self.width)
        newy=boundary(p.y,self.y, self.y+self.height)
        return Point2D(newx,newy)
    def contains(self,p):
        """find out if a point is inside the cage"""
        return (in_between(p.x,self.x,self.x+self.width)
                and in_between(p.y,self.y,self.y+self.height))

class Line:
    def __init__(self,p1,p2):
        self.ends=(p1,p2)
    def __str__(self):
        return "%s-%s" % self.ends
    def getAngle(self):
        hyp=self.getLength()
        if(hyp==0):
            return 0 # avoid division by zero -> value doesnt matter cause there
                     # is no real line
        kath=self.ends[1].y-self.ends[0].y
        x=math.asin(kath/hyp)
        if (self.ends[0].x>self.ends[1].x):
            x=math.pi-x
        return x
    def getNormal(self):
        return self.getAngle()+math.pi/2
    def collide(self,other):
        """
        compare 2 lines - when they cut, return cut point, else
        return False
        """

        """
        vector math lulz:

                (a)    (c)
        self: p=(b)+r* (d)

        other:p=(e)+s* (g)
                (f)    (h)

        (a)+r(c) = (e)+s(g)
        (b)  (d)   (f)  (h)
        """
        a=self.ends[0].x
        b=self.ends[0].y
        c=self.ends[1].x-self.ends[0].x
        d=self.ends[1].y-self.ends[0].y
        e=other.ends[0].x
        f=other.ends[0].y
        g=other.ends[1].x-other.ends[0].x
        h=other.ends[1].y-other.ends[0].y

        dem=g*d-c*h
        if dem==0: # parallel 
            return False

        s=(a*d+f*c-b*c-e*d)/dem
        x=e+s*g
        y=f+s*h
        return Point2D(x,y)

    def clash(self,other):
        """compare 2 lines segments, return cutpoint if they cut"""
        ka=self.ends[0]
        kb=self.ends[1]
        la=other.ends[0]
        lb=other.ends[1]

        p=self.collide(other)
        if(not p):
            return False

        if(in_between(p.x,ka.x,kb.x) # do line segments match?
                and in_between(p.x,la.x,lb.x)
                and in_between(p.y,ka.y,kb.y)
                and in_between(p.y,la.y,lb.y)):
            return p

        return False
        
    def getLength(self):
        p1 = self.ends[0]
        p2 = self.ends[1]
        a=p1.x
        return math.sqrt((p2.x-p1.x)**2+(p2.y-p1.y)**2)

    def isHard(self):
        """will things bounce or not?
        to be overwritten by child classes"""
        return True

    def onClash(self,object,position):
        if self.isHard():
            object.dobounce(self)
        return False


class Triangle:
    def __init__(self,a,b,c):
        self.ends=(a,b,c)
    def inBox(self,p):
        (a,b,c)=self.ends
        x=min(a.x,min(b.x,c.x))
        y=min(a.y,min(b.y,c.y))
        width=max(a.x,max(b.x,c.x))-x
        height=max(a.y,max(b.y,c.y))-y
        self.box=Box(x,y,width,height)
        return self.box.inbound(p)
        


    def contains(self,p):
        """ check if point is in triangle"""
        # algo from:
        # http://nuttybar.drama.uga.edu/pipermail/dirgames-l/2003-December/027342.html
        (a,b,c)=self.ends
        b0 = ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y))
        if(b0==0): # all points in one line
            return False
        
        b1 = (((b.x - p.x) * (c.y - p.y) - (c.x - p.x) * (b.y - p.y)) / (b0*1.0))
        b2 = (((c.x - p.x) * (a.y - p.y) - (a.x - p.x) * (c.y - p.y)) / (b0*1.0))
        b3 = 1 - b1 - b2

        return (b1 > 0 and b2 > 0 and b3 > 0)

    def __str__(self):
        return "%s-%s-%s" % self.ends



