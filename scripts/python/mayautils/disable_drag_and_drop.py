# -*- coding: utf-8 -*-
'''
This is a workaround for a bug in Maya 2013.
Saving scene after accidentally dropped file(s) with unrecognized format, such as an icon/shortcut from desktop,
to any viewports, will result in a corrupted Maya file, losing all animation on referenced assets.
It is fixed in Maya 2015. So for Maya 2013, we simply disable the DnD functionality.
'''
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import getpass
import sys
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.OpenMaya as om

import shotgun_connection
import mayautils.decorators


def isRequired():
    if cmds.about(batch=True):
        return False

    if not cmds.about(version=True).startswith('2013'):
        return False

    sg = shotgun_connection.Connection()
    user = sg.find_one('HumanUser', [['login', 'is', getpass.getuser()]], ['department'])
    if not user:
        return False

    if user['department']['name'] not in ('Animation', 'Pipeline'):
        return False

    return True


def registerEvent():
    global JOB_ID
    if globals().has_key('JOB_ID'):
        cmds.warning('Script Job already exists.')
        return JOB_ID

    JOB_ID = cmds.scriptJob(event=('modelEditorChanged', denyDrops))
    return JOB_ID


@mayautils.decorators.d_noUndo
def denyDrops(*args):
    try:
        from PySide import QtGui
        import shiboken
    except:
        cmds.warning('Cannot import PySide or shiboken, skipping...')
        return

    panels = args or cmds.lsUI(panels=True, l=True) or list()
    for p in panels:
        if not cmds.objectTypeUI(p) == 'modelEditor':
            continue

        cmds.setFocus(p)
        mp = cmds.playblast(activeEditor=True)
        mp = omui.MQtUtil.findControl(mp)

        try:
            mp = shiboken.wrapInstance(long(mp), QtGui.QWidget)
        except OverflowError:
            continue

        if mp.acceptDrops():
            mp.setAcceptDrops(False)
            om.MGlobal.displayInfo('Denied drops for editor: %s' % p)

