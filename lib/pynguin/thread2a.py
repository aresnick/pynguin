# Copyright 2012 Lee Harr
#
# This file is part of pynguin.
# http://pynguin.googlecode.com/
#
# Pynguin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pynguin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pynguin.  If not, see <http://www.gnu.org/licenses/>.


from . import thread2

class Thread(thread2.Thread):
    def _get_my_tid(self):
        if not self.isAlive():
            return -1
        else:
            return thread2.Thread._get_my_tid(self)

    def raise_exc(self, exctype):
        tid = self._get_my_tid()
        if tid != -1:
            thread2._async_raise(tid, exctype)
