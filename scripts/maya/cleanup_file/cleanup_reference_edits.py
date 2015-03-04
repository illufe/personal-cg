#!/usr/autodesk/maya/bin/mayapy
import maya.cmds as cmds
import sys
import os


removing = {'setAttr': ('Shape.', 'tweak', '.inputComponent', 'skinCluster', '.w[', '.override', '.ai'),
            'connectAttr': ('.dagSetMembers', 'SG', '.drawOverride', '.drawInfo', '.ai'),
            }

preserving = {'setAttr': ('.translate', '.rotate'),
              'connectAttr': ('.ouput', ),
              }



def main(path, pathout=None):
    cmds.file(path, o=True, loadReferenceDepth='none')
    references = cmds.ls(references=True) or list()
    for ref in references:
        for cmd, patterns in removing.iteritems():
            edits = cmds.referenceQuery(ref, editStrings=True, editCommand=cmd, showDagPath=False)
            for edit in edits:
                if any(p in edit for p in patterns)\
                   and not any(p in edit for p in preserving.get(cmd)):
                    print 'Removing:', edit
                    cmds.referenceEdit(edit.split()[1],
                                       failedEdits=True,
                                       successfulEdits=True,
                                       editCommand=cmd,
                                       removeEdits=True)

    pathout = pathout or '.fixed'.join(os.path.splitext(path))
    print 'Saving file to', pathout
    cmds.file(rename=pathout)
    cmds.file(save=True)



if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        print sys.argv
        print 'Usage: mayapy %s path/to/file.ma' % __file__
        sys.exit(1)

    import maya.standalone
    maya.standalone.initialize()

    path = sys.argv[1]
    pathout = sys.argv[2] if len(sys.argv) > 2 else None
    main(path, pathout)
