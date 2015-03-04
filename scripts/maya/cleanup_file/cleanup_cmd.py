# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import sys
import os
import time
import traceback
import pymel.core as pm

import studio_xmpp
import errorhandling
import filelock as fl

import functions
import utils


@errorhandling.exit_with_error_code
def main():
    file_to_open = os.path.normpath(sys.argv[1])

    dirname = os.path.dirname(file_to_open)
    latest = utils.getLatestFile(dirname)
    # abort if file is no longer the latest version
    if not os.path.samefile(file_to_open, latest):
        return

    # abort if file is currently in use
    if fl.isLocked(file_to_open):
        return

    time_start = time.ctime()
    pm.system.openFile(file_to_open)

    count = 0
    count += functions.removeUseless(animCurves=True,
                                     objectSets=True,
                                     referenceNodes=True)
    count += functions.fixNamespaces()
    count += functions.rebuildHierarchy()
    count += functions.renameAnimCurves()

    # abort if no operation has been done
    if count == 0:
        return

    fl.unlock(file_to_open)
    # abort if file is used by others
    if fl.isLocked(file_to_open):
        return

    time_end = time.ctime()
    functions.addFileInfo(file_to_open, time_start, time_end)
    new_file = functions.versionUp(file_to_open)
    new_file.chmod(0777)

    old_file = pm.Path(file_to_open)
    owner = old_file.get_owner()
    sender = studio_xmpp.Sender()
    sender.send(owner,
                u'已经清理优化了你的工程文件，请使用新版！\n'
                u'源文件：%s\n'
                u'新版本：%s\n'
                u'（目前是测试阶段，打开新版本发现问题的话，请尽快通知TD。）'
                %(old_file.basename(),
                  new_file.basename()))


if __name__ == '__main__':
    main()
