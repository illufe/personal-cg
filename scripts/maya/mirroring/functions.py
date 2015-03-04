# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import pymel.core as pm

import errorhandling
import mayautils as mutils
import mayautils.decorators as decorators


KEYWORD_FK = ('Fk', '_finger', 'Settings')
KEYWORD_LT = 'L_'
KEYWORD_RT = 'R_'
KEYWORD_CT = 'C_'
ATTRS_CT = ('translateX', 'rotateY', 'rotateZ')
AXIS_MAP = {
    '_arm': 'C_neck1_ctrl',
    '_leg': 'C_hips2_ctrl',
    '_ear': 'headTp_ctrl',
}


def isFK(ctrl):
    name = getRawName(ctrl)
    return any(i in name for i in KEYWORD_FK)


def isLeft(ctrl):
    name = getRawName(ctrl)
    return name.startswith(KEYWORD_LT)


def isRight(ctrl):
    name = getRawName(ctrl)
    return name.startswith(KEYWORD_RT)


def isCenter(ctrl):
    name = getRawName(ctrl)
    if name.startswith(KEYWORD_CT):
        return True

    if not isLeft(ctrl) and not isRight(ctrl):
        return True

    return False


def getRawName(ctrl):
    ctrl = pm.nt.Transform(ctrl)
    name = ctrl.nodeName(stripNamespace=True)
    return name


def getMirrorCtrl(ctrl):
    name = getRawName(ctrl)
    if isLeft(ctrl):
        target = name.replace(KEYWORD_LT, KEYWORD_RT, 1)
    elif isRight(ctrl):
        target = name.replace(KEYWORD_RT, KEYWORD_LT, 1)
    else:
        return

    target = ctrl.replace(name, target)
    if pm.general.objExists(target):
        return pm.nt.Transform(target)


def getSharedParent(nodes, include_self=True):
    node = pm.nt.DagNode(nodes[0])
    parent = node
    while parent:
        for n in nodes:
            n = pm.nt.DagNode(n)
            if parent.isParentOf(n):
                continue
            if include_self and parent == n:
                continue
            break
        else:
            break
        parent = parent.getParent()
    return parent


def getAxis(ctrl, mctrl=None):
    ctrl = pm.nt.Transform(ctrl)
    namespace = ctrl.namespace()
    name = getRawName(ctrl)
    result = None
    for key, axis in AXIS_MAP.items():
        if key in name:
            result = namespace + axis
            break

    if result and pm.general.objExists(result):
        return pm.nt.Transform(result)

    if mctrl:
        return getSharedParent([ctrl, mctrl])


def mirrorCenter(ctrl, animation=False):
    ctrl = pm.nt.Transform(ctrl)
    for name in ATTRS_CT:
        if not ctrl.hasAttr(name):
            continue

        attr = ctrl.attr(name)
        if attr.isLocked():
            continue

        if animation:
            pm.animation.scaleKey(ctrl, attribute=name, valuePivot=0.0, valueScale=-1.0)
            mode = 'animation'
        else:
            value = attr.get()
            value *= -1
            attr.set(value)
            mode = 'value'

        pm.system.displayInfo('Scaled %s for %s by -1.' % (mode, attr))


def mirrorFK(ctrl, mctrl, animation=False, ignore_attrs=[], deferred=True):
    ctrl = pm.nt.Transform(ctrl)
    mctrl = pm.nt.Transform(mctrl)
    attrs = ctrl.listAnimatable()
    callbacks = []
    for attr in attrs:
        if False: isinstance(attr, pm.general.Attribute)

        name = attr.name(includeNode=False)
        if name in ignore_attrs:
            continue

        if not mctrl.hasAttr(name):
            continue

        mattr = mctrl.attr(name)
        if mattr.isLocked():
            continue

        if animation:
            mode = 'animation'
            pm.animation.copyKey(ctrl, attribute=name)
            pm.animation.pasteKey(mctrl, attribute=name, option='replaceCompletely')
        else:
            mode = 'value'
            value = attr.get()
            if value == mattr.get():
                continue

            callback = mutils.Callback(mattr.set, value)
            if deferred:
                callbacks.append(callback)
            else:
                callback()

        pm.system.displayInfo('Copied %s from %s to %s.' % (mode, attr, mattr))
    return callbacks


@decorators.d_maintainSceneSelection
def mirrorIK(ctrl, mctrl, maxis, deferred=True):
    callbacks = mirrorFK(ctrl, mctrl, animation=False,
                         ignore_attrs=['translateX', 'translateY', 'translateZ',
                                       'rotateX', 'rotateY', 'rotateZ'],
                         deferred=deferred)

    source = pm.nt.Transform(ctrl)
    target = pm.nt.Transform(mctrl)
    mirror = pm.nt.Transform(maxis)

    sMatrix = source.getMatrix(worldSpace=True)
    mMatrix = mirror.getMatrix(worldSpace=True)
    rMatrix = pm.dt.Matrix([-1, 0, 0, 0,
                            0, 1, 0, 0,
                            0, 0, 1, 0,
                            0, 0, 0, 1])
    rMatrix2 = pm.dt.Matrix([-1, 0, 0, 0,
                             0, -1, 0, 0,
                             0, 0, -1, 0,
                             0, 0, 0, 1])

    tMatrix = sMatrix * mMatrix.inverse() * rMatrix * mMatrix
    tMatrix = rMatrix2 * tMatrix

    temp = pm.general.spaceLocator()
    temp.setMatrix(tMatrix, worldSpace=True)
    rotation = temp.getRotation(space='world')
    pm.general.delete(temp)

    callback1 = mutils.Callback(target.setMatrix, tMatrix, worldSpace=True)
    callback2 = mutils.Callback(target.setRotation, rotation, space='world')
    if deferred:
        callbacks.append(callback1)
        callbacks.append(callback2)
    else:
        callback1()
        callback2()

    pm.system.displayInfo('Mirrored pose from %s to %s by %s.' % (ctrl, mctrl, maxis))
    return callbacks


@errorhandling.MayaHandler
@decorators.d_unifyUndo
def mirrorSelected(animation=False, select=True, sort_selection=True):
    selection = pm.general.selected(transforms=True)
    mutils.testAndRaise(selection, 'No control selected!')

    if sort_selection:
        selection.sort(key=isCenter, reverse=True)

    if select:
        pm.general.select(clear=True)

    commands = []
    for ctrl in mutils.progressIter(selection):
        if isCenter(ctrl):
            mctrl = ctrl
            mirrorCenter(ctrl, animation=animation)
        else:
            mctrl = getMirrorCtrl(ctrl)
            if not mutils.testAndWarn(mctrl, 'Mirror control for %s not found, skipping...'%ctrl):
                continue

            if isFK(ctrl):
                callbacks = mirrorFK(ctrl, mctrl, animation=animation)
                commands.extend(callbacks)
            else:
                if animation:
                    pm.warning('Cannot mirror animation for IK control(%s), skipping...'%ctrl)
                    continue

                maxis = getAxis(ctrl, mctrl)
                if mutils.testAndWarn(maxis, 'Axis for %s not found, skipping...'%ctrl):
                    callbacks = mirrorIK(ctrl, mctrl, maxis)
                    commands.extend(callbacks)
        if select:
            pm.general.select(mctrl, add=True)

    for command in mutils.progressIter(commands):
        command()
