#!/usr/bin/env python
"""
A script used to mimic cancelling of redundant builds in circleCi. This
is currently an unsupported feature for workflows in CircleCi-2.0:
https://discuss.circleci.com/t/auto-cancel-redundant-builds-not-working-for-workflow/13852

This script is to be used as a entry point for a workflow:

e.g.
                          -> Run frontend tests
                        /                      \
*Job Running this script                        -> Aggregate results
                        \                      /
                          -> Run Backend tests


Making this assumption, the script will cancel jobs that:
* Are of a job step that aren't running this script
* Are of the same job step but are a lower build number.
"""


import json
import os
import urllib2


def get_circle_base_url(project_target):
    """Create circle base url used against the v1.1 API.

    Arguments:
        project_target {string} -- project target in circleCi <Org>/<Project>

    Returns:
        string -- url that can be used to access
    """

    return "https://circleci.com/api/v1.1/project/github/{}".format(project_target)


class JobInfo(object):
    def __init__(self, job_num, job_step_name):
        self.job_num = job_num
        self.job_step_name = job_step_name


def get_running_jobs_for_branch(circle_base_url, branch_name, circle_token):
    """Returns all running jobs for the provided branch_name.
    """
    running_jobs = []
    running_jobs_url = "{CIRCLE_BASE_URL}/tree/{CIRCLE_BRANCH}?circle-token={TOKEN}".format(
        CIRCLE_BASE_URL=circle_base_url,
        CIRCLE_BRANCH=branch_name,
        TOKEN=circle_token)
    print 'Retrieving running jobs for %s' % branch_name
    request = urllib2.Request(running_jobs_url, headers={"Accept": "application/json"})
    contents = urllib2.urlopen(request).read()
    json_contents = json.loads(contents)

    for job_dict in json_contents:
        if job_dict.get('status') == 'running':
            build_num = job_dict.get('build_num')
            job_name = job_dict.get('build_parameters').get('CIRCLE_JOB')
            job_info = JobInfo(build_num, job_name)
            running_jobs.append(job_info)

    print "Found {} running jobs".format(len(running_jobs))
    return running_jobs


def filter_jobs_to_cancel(current_job_name, current_job_id, list_of_job_info):
    """ This filters for jobs that should be cancelled.

    There are two cases a job should be cancelled.
    1. If a job has the same name as the current job and is of a lower job_id.
    2. Has a different job name. This is because there is the possibility that
       a different workflow started before the current job but will have moved onto
       different parts of the workflow (hence a different job name). It also has
       the option to have a higher job number, if it's kicked off after the current job.

    """
    running_jobs = []
    for job_info in list_of_job_info:
        job_num = job_info.job_num
        job_step_name = job_info.job_step_name

        if job_step_name != current_job_name:
            running_jobs.append(job_num)
        elif job_num < current_job_id:
            running_jobs.append(job_num)

    return running_jobs


def cancel_job(circle_base_url, circle_token, job_id):
    cancel_url = "{CIRCLE_BASE_URL}/{JOB_ID}/cancel?circle-token={TOKEN}".format(
        CIRCLE_BASE_URL=circle_base_url,
        JOB_ID=job_id,
        TOKEN=circle_token
    )
    # Adding a data field makes it so it calls a POST
    request = urllib2.Request(cancel_url, data={}, headers={"Accept": "application/json"})
    urllib2.urlopen(request).read()
    print "Cancelled job: {}".format(job_id)


if __name__ == "__main__":
    org_name = os.environ['CIRCLE_PROJECT_USERNAME']
    project_name = os.environ['CIRCLE_PROJECT_REPONAME']
    branch_name = os.environ['CIRCLE_BRANCH']
    build_num = int(os.environ['CIRCLE_BUILD_NUM'])
    job_name = os.environ['CIRCLE_JOB']
    # The token is created by going to https://circleci.com/gh/<org>/<project/edit#api
    # Then we set it as an environment variable for the build by setting CIRCLE_TOKEN at
    # https://circleci.com/gh/<org>/<project/edit#env-vars
    circle_token = os.environ['CIRCLE_TOKEN']

    project_target = "{}/{}".format(org_name, project_name)
    circle_base_url = get_circle_base_url(project_target)

    job_run_info = get_running_jobs_for_branch(
        circle_base_url, branch_name, circle_token)
    running_job_ids = filter_jobs_to_cancel(job_name, build_num, job_run_info)
    for job_id in running_job_ids:
        cancel_job(circle_base_url, circle_token, job_id)
