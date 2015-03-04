# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import os
import socket

import errorhandling


class FileLock(object):

    SUFFIX = '.lock'

    def __init__(self, path):
        self.path = path
        self.locker = self._get_locker()
        self._data = list()
        self._host = socket.gethostname()
        self._pid = os.getpid()

    def _get_locker(self):
        return self.path + self.SUFFIX

    def _parse(self):
        self._data = list()
        if os.path.isfile(self.locker):
            with open(self.locker) as f:
                for l in f:
                    host, pid = l.split()
                    self._data.append((host, int(pid)))

    @errorhandling.SuppressError
    def _dump(self):
        if os.path.isfile(self.locker):
            os.remove(self.locker)
        if self._data:
            with open(self.locker, 'w') as f:
                isinstance(f, file)
                for host, pid in self._data:
                    l = '%s %s\n' % (host, pid)
                    f.write(l)
            os.chmod(self.locker, 0777)

    def lock(self):
        self._parse()
        data = (self._host, self._pid)
        if data not in self._data:
            self._data.append(data)
        return self._dump()

    def unlock(self):
        self._parse()
        data = (self._host, self._pid)
        while data in self._data:
            self._data.remove(data)
        return self._dump()

    def isLocked(self):
        return os.path.isfile(self.locker)


def lock(path):
    return FileLock(path).lock()


def unlock(path):
    return FileLock(path).unlock()


def isLocked(path):
    return FileLock(path).isLocked()
