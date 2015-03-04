# -*- coding: utf-8 -*-
__author__ = 'wanghuan'
__maintainer__ = 'wanghuan'

import os
import getpass

import MClientAPI
import MTemplateAPI

import mustersubmit as submit
import filelock as fl
import utils


class MusterSubmit(submit.MusterSubmitBase):

    def setupJob(self, job):
        assert isinstance(job, MClientAPI.MJob)
        job.setParentId(-1)
        job.setJobType(MClientAPI.MJob.kJobTypeJob)
        job.setPriority(50)
        job.setTemplateID(101)
        job.setMaximumNodes(1)
        job.setIncludedPools('instances')


def main():
    script = utils.getCmdScript()
    taskDirs = utils.getTaskDirs()
    if not taskDirs:
        return

    ms = MusterSubmit()
    for path in taskDirs:
        latestFile = utils.getLatestFile(path)
        if fl.isLocked(latestFile):
            continue

        filename = os.path.basename(latestFile)
        job = {'name': '%s-cleanup by %s' % (filename, getpass.getuser()),
               'shot': filename.split('.')[0],
               'job_file': latestFile,
               'script_file': script,
               'output_folder': os.path.dirname(latestFile),
               }
        ms.sendJob(job)
    ms.disconnect()
    return


if __name__ == '__main__':
    main()
