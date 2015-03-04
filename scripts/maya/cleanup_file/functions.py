# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import os
import traceback
import sys
import pymel.core as pm

import tank

import errorhandling
import mayautils.decorators as decorators
import mayautils as mutils
import layer_manager.functions as functions


def getAssetName(node):
    if False:
        isinstance(node, pm.nt.DependNode)

    ref = node.referenceFile()
    if ref:
        return ref.path.namebase.split('.')[0]


def getNextAvailableNamespace(name):
    num = 1
    result = name
    while pm.namespace(exists=result, recurse=True):
        result = name + str(num)
        num += 1
    return result


@errorhandling.MayaHandler
@decorators.d_promptSaveScene(u'当前操作不可撤销，是否需要先保存文件？')
@decorators.d_showWaitCursor
@decorators.d_noUndo
def fixNamespaces():
    mutils.log('Fixing assets namespace...')
    pm.namespace(setNamespace=':')
    count = 0
    assets = functions.getAssets()
    assets_by_name = dict()
    for type_, masters in assets.iteritems():
        for m in masters:
            name = getAssetName(m)
            assets_by_name.setdefault(name, list())
            assets_by_name.get(name).append(m)

    garbage = set()
    for name, masters in assets_by_name.iteritems():
        for m in masters:
            ns = m.namespace().strip(':')
            # skip if namespace is perfect
            if name == ns:
                continue

            # restricted case, no trailing digits allowed
            if len(masters) == 1:
                target = name
                if pm.namespace(exists=target):
                    bak = getNextAvailableNamespace(target+'_bak')
                    mutils.log('Renaming conflicting namespace %s to %s', target, bak)
                    pm.namespace(rename=(target, bak))
                    count += 1
            # skip if namespace is ok
            elif ns.startswith(name) and ns[len(name):].isdigit():
                continue
            # loose case, trailing digits is ok
            else:
                target = getNextAvailableNamespace(name)

            mutils.log('Renaming namespace %s to %s', ns, target)
            pm.namespace(rename=(ns, target))
            count += 1
            while ':' in ns:
                ns = ':'.join(ns.split(':')[:-1])
                garbage.add(ns)

    for namespace in garbage:
        mutils.log('Removing useless namespace: %s', namespace)
        pm.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
        count += 1

    mutils.log('%s operation(s) performed.', count)
    return count


@errorhandling.MayaHandler
@decorators.d_showWaitCursor
@decorators.d_unifyUndo
@decorators.d_maintainSceneSelection
def rebuildHierarchy():
    mutils.log('Rebuilding outliner hierarchy...')
    count = 0
    assets = functions.getAssets()
    topGrp = '|assets'
    if pm.general.objExists(topGrp):
        topGrp = pm.nt.Transform(topGrp)
    else:
        mutils.log('Creating null: %s', topGrp)
        topGrp = pm.general.group(empty=True, name=topGrp)
        count += 1
    for type_, masters in assets.iteritems():
        parent = '|'.join([topGrp.name(long=True), type_])
        if pm.general.objExists(parent):
            parent = pm.nt.Transform(parent)
        else:
            mutils.log('Creating null: %s', type_)
            parent = pm.general.group(empty=True, name=type_, parent=topGrp)
            count += 1
        for master in masters:
            if not parent.hasChild(master):
                mutils.log('Pareting %s to %s', master, parent)
                parent.addChild(master)
                count += 1
    mutils.log('%s operation(s) performed.', count)
    return count


@errorhandling.MayaHandler
@decorators.d_showWaitCursor
@decorators.d_unifyUndo
def removeUseless(animCurves=False, objectSets=False,
                  referenceNodes=False, transforms=False):
    mutils.log('Removing useless nodes...')
    useless = []

    # animation curves
    if animCurves:
        curves = pm.general.ls(type='animCurve')
        for c in mutils.progressIter(curves, status='Processing animation curves...'):
            if False:
                isinstance(c, pm.nt.AnimCurve)
            if c.outputs():
                continue
            if c.isReferenced():
                continue
            useless.append(c)

    # ViewSelectedSet for isolate selection
    if objectSets:
        sets = pm.general.ls(exactType='objectSet')
        for s in mutils.progressIter(sets, status='Processing object sets...'):
            if False:
                isinstance(s, pm.nt.ObjectSet)
            if s.outputs():
                continue
            if s.isReferenced():
                continue
            if s.usedBy.inputs():
                continue
            useless.append(s)

    count = 0
    for n in mutils.progressIter(useless, status='Deleting nodes...'):
        try:
            mutils.log('Removing node: %s', n)
            pm.general.delete(n)
            count += 1
        except:
            traceback.print_exc()

    # _UNKNOWN_REF_NODE_
    if referenceNodes:
        count += pm.mel.RNdeleteUnused()

    # empty groups
    if transforms:
        pm.mel.source('cleanUpScene.mel')
        count += pm.mel.deleteEmptyGroups()

    mutils.log('Removed %s useless node(s).', count)
    return count


@errorhandling.MayaHandler
@decorators.d_showWaitCursor
@decorators.d_unifyUndo
def renameAnimCurves():
    mutils.log('Renaming animation curves...')
    count = 0
    curves = pm.general.ls(type='animCurve')
    for c in mutils.progressIter(curves, status='Renaming animation curves...'):
        if False:
            isinstance(c, pm.nt.AnimCurve)

        if c.isReferenced():
            continue

        targets = c.output.outputs(plugs=True, type=('transform', 'joint'))
        if not targets:
            continue

        if not pm.system.referenceQuery(targets[0].node(), isNodeReferenced=True):
            continue

        properName = targets[0].name().split('|')[-1].replace('.', '_')
        currentName = c.name()
        if currentName == properName:
            continue

        if pm.general.objExists(properName):
            if pm.nt.DependNode(properName).isReferenced():
                pm.warning('Conflicting name "%s" exists and is referenced, skipping...'
                           % properName)
                continue

            pm.general.rename(properName, properName+'_bak')

        c.rename(properName)
        assert c.name() == properName, 'New name is still invalid!'

        mutils.log('Renamed curve %s to %s.', currentName, properName)
        count += 1

    mutils.log('Renamed %s curve(s).', count)
    return count


def addFileInfo(source_file, start_time, end_time):
    pm.system.fileInfo('CleanupSource', source_file)
    pm.system.fileInfo('CleanupStart', start_time)
    pm.system.fileInfo('CleanupEnd', end_time)


def versionUp(source_file):
    tk = tank.sgtk_from_path(source_file)
    template = tk.templates.get('maya_shot_work')
    fields = template.get_fields(source_file)
    path = source_file
    while os.path.exists(path):
        fields['version'] += 1
        path = template.apply_fields(fields)
    return pm.system.saveAs(path)
