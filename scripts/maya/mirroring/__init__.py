# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import mayautils

from functions import mirrorSelected as main

COMMAND_POSE_NAME = 'MirrorPose'
COMMAND_POSE_ANNOTATION = 'Mirror current pose for selected controls.'
COMMAND_POSE_STRING = '__import__("mirroring",fromlist=".").main()'
COMMAND_POSE_HOTKEY = 'm'
COMMAND_ANIM_NAME = 'MirrorAnim'
COMMAND_ANIM_ANNOTATION = 'Mirror animation for selected controls.'
COMMAND_ANIM_STRING = '__import__("mirroring",fromlist=".").main(animation=True)'
COMMAND_ANIM_HOTKEY = 'M'

mayautils.assignDefaultHotkey(COMMAND_POSE_NAME,
                              COMMAND_POSE_STRING,
                              COMMAND_POSE_ANNOTATION,
                              COMMAND_POSE_HOTKEY)

mayautils.assignDefaultHotkey(COMMAND_ANIM_NAME,
                              COMMAND_ANIM_STRING,
                              COMMAND_ANIM_ANNOTATION,
                              COMMAND_ANIM_HOTKEY)
