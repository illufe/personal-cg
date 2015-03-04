# -*- coding:utf-8 -*-
'''
This module contains functions to selectively load/defer references to speed up file openning.
It utilizes Maya's built-in LoadSettings functionality, so will not make any changes to the scene file on disk.
'''
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import maya.cmds as cmds
import errorhandling


@errorhandling.MayaHandler
def load_by_ref_nodes(file_path, ref_nodes, reverse=False):
    '''Selectively load file by reference node names.

    @ file_path: path to maya scene file to load
    @ ref_nodes: list of reference node names, e.g. ['carRN', 'set:manRN']
    @ reverse: if this is set to True, defer ref_nodes instead of loading them
    '''
    cmds.file(file_path, open=True, buildLoadSettings=True)

    numSettings = cmds.selLoadSettings(query=True, numSettings=True)
    refNodes = cmds.selLoadSettings(*range(numSettings), query=True, referenceNode=True)
    for id_, refNode in enumerate(refNodes):
        if id_ == 0:
            continue

        if not refNode:
            continue

        id_ = str(id_)
        if refNode in ref_nodes:
            print 'Reference node to', 'defer' if reverse else 'load', ':', refNode
            defer = reverse
        else:
            defer = not reverse
        cmds.selLoadSettings(id_, edit=True, deferReference=defer)

    cmds.file(file_path, open=True, force=True, loadSettings='implicitLoadSettings')


@errorhandling.MayaHandler
def load_by_file_names(file_path, file_names):
    '''Selectively load file by reference file names.

    @ file_path: path to maya scene file to load
    @ file_names: list of reference file short names, e.g. ['car.ma', 'man.ma']
    '''
    cmds.file(file_path, open=True, buildLoadSettings=True)

    numSettings = cmds.selLoadSettings(query=True, numSettings=True)
    fileNames = cmds.selLoadSettings(*range(numSettings), query=True, fileName=True, shortName=True)
    for id_, fileName in enumerate(fileNames):
        if id_ == 0:
            continue

        if fileName in file_names:
            continue

        id_ = str(id_)
        cmds.selLoadSettings(id_, edit=True, deferReference=True)

    cmds.file(file_path, open=True, force=True, loadSettings='implicitLoadSettings')
