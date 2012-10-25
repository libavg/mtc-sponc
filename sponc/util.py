# Copyright (C) 2007
#    Martin Heistermann, <mh at lulzmeister dot de>
#    Tim Grocki, <drogenkonsument at gmail dot com>
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



def in_between(val,b1,b2):
    """return True if val is between b1 and b2"""
    return((b1>=val and val>=b2) or (b1<=val and val<=b2))

def boundary(val,min,max):
    """return the value between min and max which is closest to val"""
    if val<min:
        return min
    if val>max:
        return max
    return val

