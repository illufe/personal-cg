# -*- coding:utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import traceback
import datetime
import getpass
import uuid
import inspect
import pprint
import functools
import sys
import os

import studio_xmpp

LOG_ROOT = '/mnt/trash/log/exceptions'
if sys.platform == "win32":
    LOG_ROOT = LOG_ROOT.replace('/mnt/trash', 'T:')


class StudioException(Exception):
    pass


class UserException(StudioException):
    pass


class ProcessedException(StudioException):
    '''
    This is to identify exceptions already processed by error handler,
    to prevent processing the same error from hierarchical handlers.
    '''
    pass


class BaseHandler(object):
    '''
    Decorator for error handling.
    It is doing the following things:

    - Catch unexpected exceptions;
    - Assemble critical infomation for debugging;
    - Log error to file;
    - Send IM to maintainer with detailed info;
    - Throw user-friendly feedback/warning;
    - Interrupt further execution.
    '''
    def __init__(self, func):
        self.func = func
        module = inspect.getmodule(func)
        self.maintainer = __maintainer__
        self.maintainer = getattr(module, '__author__', self.maintainer)
        self.maintainer = getattr(module, '__maintainer__', self.maintainer)
        functools.update_wrapper(self, func)
        return

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        except StudioException or os.getenv('LOCAL_MODE'):
            raise
        except:
            trace = inspect.trace()
            frame, _file, _, function, _, _ = trace[-1]
            mess = ('Exception!\n'
                    'Time: %s\n'
                    'User: %s\n'
                    'File: %s\n'
                    'Func: %s\n'
                    'Maintainer: %s\n'
                    '\n'
                    ) % (datetime.datetime.now(),
                         getpass.getuser(),
                         _file,
                         function,
                         self.maintainer,
                         )
            mess += traceback.format_exc().strip()
            mess += '\n\nLocal variables at outer most frame:\n'
            try:
                mess += pprint.pformat(frame.f_locals)
            except:
                traceback.print_exc()
                mess += 'Failed retrieving local variables.'
            self.send(mess)
            self.show(mess)
            raise ProcessedException(sys.exc_info()[1])
        return

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return functools.partial(self, obj)

    def send(self, mess):
        log_dir = os.path.join(LOG_ROOT,
                               self.maintainer,
                               datetime.date.today().strftime('%Y%m%d'))
        if not os.path.exists(log_dir):
            try:
                original_umask = os.umask(0)
                os.makedirs(log_dir, mode=0777)
            finally:
                os.umask(original_umask)

        log = os.path.join(log_dir, str(uuid.uuid1())+'.log')
        with open(log, 'w') as f:
            f.write(mess)

        msg = 'Exception!\n'
        msg += 'file://' + log.replace('T:', '/mnt/trash').replace('\\', '/')
        sender = studio_xmpp.Sender()
        sender.send(self.maintainer, msg)
        return

    def show(self, mess):
        print mess


class MayaHandler(BaseHandler):
    '''
    Error handler for Maya scripts.
    Show dialog with error info in GUI mode.
    '''
    def show(self, mess):
        BaseHandler.show(self, mess)
        import maya.cmds as cmds
        if cmds.about(batch=True):
            return

        if cmds.confirmDialog(title='Error',
                              message=(u'出错啦！错误信息已经发给TD，请稍等。\n'
                                       u'An unexpected exception occured!\n'
                                       u'Error message has been sent to TD.'),
                              button=('Ok', 'Show Details')) == 'Show Details':
            cmds.confirmDialog(message=mess)


class SuppressError(BaseHandler):
    '''
    Decorator to suppress all exceptions from the decorated function.
    This will also suppress return values from the original function,
    instead, return True if no exception occured, False other wise.
    '''
    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
            return True
        except:
            traceback.print_exc()
            return False


def exit_with_error_code(f):
    '''
    Decorator to force exit after evaluation;
    with exit code 1, when exception occured.
    '''
    def wrapped(*a, **kw):
        try:
            return f(*a, **kw)
        except:
            traceback.print_exc()
            exit(1)
        else:
            exit()

    wrapped.__name__ = f.__name__
    wrapped.__doc__ = f.__doc__

    return wrapped


@BaseHandler
def test(a, b=3, c='test'):
    d = a + b + c
    return d


@BaseHandler
def test2():
    test(3)


if __name__ == '__main__':
    test2()
