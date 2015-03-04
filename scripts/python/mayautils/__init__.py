# -*- coding:utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import functools
import traceback
import sys

import errorhandling as err


class Callback(object):

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args):
        return self.func(*self.args, **self.kwargs)


class MayaException(err.UserException):
    def __init__(self, message):
        err.UserException.__init__(self, message)
        cmds.confirmDialog(title='Maya Error',
                           message=message,
                           icon='warning')
        cmds.evalDeferred(functools.partial(sys.stdout.write, ''))
        return


def testAndRaise(condition, message):
    if not condition:
        raise MayaException(message)


def testAndWarn(condition, message):
    if not condition:
        cmds.warning(message)
    return condition


def progressIter(items, isInterruptable=True, **kwargs):
    if not items:
        return

    kwargs.setdefault('title', 'Progress')
    kwargs.setdefault('status', 'Processing....')

    isShown = False
    try:
        cmds.progressWindow(maxValue=len(items), isInterruptable=isInterruptable, **kwargs)
        cmds.refresh()
        isShown = True
    except:
        traceback.print_exc()

    try:
        for i in items:
            if isShown:
                cmds.progressWindow(edit=True, step=1)
                if cmds.progressWindow(query=True, isCancelled=True):
                    break
            yield i
    finally:
        if isShown:
            cmds.progressWindow(endProgress=True)
            cmds.refresh()


def log(info, *args):
    OpenMaya.MGlobal.displayInfo(info%args)


@err.MayaHandler
def assignDefaultHotkey(cmd_name, cmd_string, cmd_annotation, cmd_hotkey):
    exists = cmds.runTimeCommand(cmd_name, exists=True)
    if exists:
        cmds.runTimeCommand(cmd_name, edit=True, delete=True)

    runtime = cmds.runTimeCommand(cmd_name,
                                  command=cmd_string,
                                  category='User',
                                  annotation=cmd_annotation)
    if not exists:
        command = cmds.nameCommand(command=runtime,
                                   sourceType='python',
                                   annotation=cmd_annotation)
        cmds.hotkey(altModifier=True,
                    keyShortcut=cmd_hotkey,
                    releaseName=command,
                    releaseCommandRepeat=True)

        cmds.evalDeferred(Callback(log, 'Assigned default hotkey (ALT+%s) for command: %s.',
                                   cmd_hotkey, cmd_name))
    return


def getRefNodesFromNodes(nodes, include_parents=False):
    referenced = cmds.ls(nodes, referencedNodes=True)
    refNodes = set()
    for node in referenced:
        refNode = cmds.referenceQuery(node, referenceNode=True)
        refNodes.add(refNode)

    if include_parents:
        parentNodes = set()
        for refNode in refNodes:
            parent = cmds.referenceQuery(refNode, referenceNode=True, parent=True)
            while parent:
                parentNodes.add(parent)
                parent = cmds.referenceQuery(parent, referenceNode=True, parent=True)
        refNodes.update(parentNodes)

    return refNodes


def getRefNodesFromSelection(include_parents=False):
    selection = cmds.ls(selection=True, referencedNodes=True)
    if testAndWarn(selection, 'No referenced node selected!'):
        return getRefNodesFromNodes(selection, include_parents=include_parents)


def getMemoryUsage(verbose=True):
    mem = cmds.memory(sum=True)
    if verbose:
        log('Maya Memory Usage:')
        for m in mem:
            log(m.rstrip())

    mem = sum(float(i.strip().split()[0]) for i in mem if i.strip())
    if verbose:
        log(('%.3f Mb\tTotal' % mem).rjust(17))

    return mem
