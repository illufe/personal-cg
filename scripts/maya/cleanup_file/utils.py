# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import os
import glob

import shotgun_connection


def getCmdScript():
    script = os.path.dirname(__file__)
    script = os.path.join(script, 'cleanup_cmd.py')
    assert os.path.isfile(script), 'Cleanup script not found: %s' % script
    return script


def getVersions():
    global SG
    SG = shotgun_connection.Connection()
    return SG.find('Version',
                       [['created_at', 'in_last', (1, 'DAY')],
                        ['sg_version_type', 'is', 'Daily'],
                        ['code', 'contains', 'ani.animation']],
                       ['code', 'sg_version_folder'])


def toTaskDir(version):
    version_dir = version['sg_version_folder']['local_path'][:-1]
    publish_dir = os.path.dirname(version_dir)
    task_dir = publish_dir.replace('/proj/', '/work/', 1).replace('/publish', '/task/maya')
    return task_dir


def getTaskDirs():
    result = set()
    versions = getVersions()
    for v in versions:
        taskDir = toTaskDir(v)
        if os.path.isdir(taskDir):
            result.add(taskDir)
    result = list(result)
    result.sort()
    return result


def getLatestFile(path):
    files = glob.glob(path+'/*.ani.animation.v*.ma')
    files.sort()
    return files[-1]
