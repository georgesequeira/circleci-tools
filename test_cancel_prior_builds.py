from cancel_prior_builds import (
    get_running_jobs_for_branch,
    filter_jobs_to_cancel,
    JobInfo)
from StringIO import StringIO
import unittest
import urllib2


FIRST_BUILD = 1
SECOND_BUILD = 2
NON_RUNNING_BUILD = 3
TEST_GET_JOBS_RETURN = """
[
  {
    "all_commit_details": [],
    "all_commit_details_truncated": false,
    "branch": "george-t123",
    "build_num": %s,
    "build_time_millis": null,
    "build_parameters": {
        "CIRCLE_JOB": "job1"
    },
    "build_url": "https://circleci.com/gh/Org/project/4464",
    "canceled": false,
    "compare": "https://github.com/Org/project/compare/george-t123",
    "messages": [],
    "parallel": 5,
    "platform": "2.0",
    "start_time": "2018-03-19T19:44:51.358Z",
    "status": "running"
  },
  {
    "all_commit_details": [],
    "all_commit_details_truncated": false,
    "branch": "george-t123",
    "build_num": %s,
    "build_time_millis": null,
    "build_parameters": {
        "CIRCLE_JOB": "job1"
    },
    "build_url": "https://circleci.com/gh/Org/project/4466",
    "canceled": false,
    "compare": "https://github.com/Org/project/compare/george-t123",
    "messages": [],
    "parallel": 5,
    "platform": "2.0",
    "start_time": "2018-03-19T19:44:51.358Z",
    "status": "running"
  },
  {
    "all_commit_details": [],
    "all_commit_details_truncated": false,
    "branch": "george-t123",
    "build_num": %s,
    "build_time_millis": null,
    "build_parameters": {
        "CIRCLE_JOB": "job1"
    },
    "build_url": "https://circleci.com/gh/Org/project/4466",
    "canceled": false,
    "compare": "https://github.com/Org/project/compare/george-t123",
    "messages": [],
    "parallel": 5,
    "platform": "2.0",
    "start_time": "2018-03-19T19:44:51.358Z",
    "status": "stopped"
  }
]
""" % (FIRST_BUILD, SECOND_BUILD, NON_RUNNING_BUILD)


class GetRunningJobsHandler(urllib2.HTTPSHandler):

    def https_open(self, req):
        if '/tree/' in req.get_full_url():
            resp = urllib2.addinfourl(
                StringIO(TEST_GET_JOBS_RETURN),
                "",
                req.get_full_url())
            resp.code = 200
            resp.msg = "OK"
            return resp


class TestJobManager(unittest.TestCase):

    def test_get_job_run_info(self):
        opener = urllib2.build_opener(GetRunningJobsHandler)
        urllib2.install_opener(opener)
        job_infos = get_running_jobs_for_branch(
            'https://circleci.com/base_url/tree/', 'branch', 'token_1')
        self.assertEquals(2, len(job_infos))
        job_info_ids = [ji.job_num for ji in job_infos]
        self.assertNotIn(NON_RUNNING_BUILD, job_info_ids)
        self.assertIn(FIRST_BUILD, job_info_ids)
        self.assertIn(SECOND_BUILD, job_info_ids)

        expected_job_name = 'job1'
        for ji in job_infos:
            self.assertEquals(expected_job_name, ji.job_step_name)

    def test_find_prior_running_jobs_doesnt_list_new_of_same_job(self):
        test_cancel_job_name = "canceller of jobs"
        current_job_id = 123
        list_of_job_info = [JobInfo(124, test_cancel_job_name)]
        self.assertEquals(0, len(filter_jobs_to_cancel(
            test_cancel_job_name, current_job_id, list_of_job_info)))

    def test_find_prior_running_jobs_lists_higher_id_if_different_job(self):
        test_cancel_job_name = "canceller of jobs"
        cancel_me_name = 'cancel me'
        current_job_id = 123
        list_of_job_info = [JobInfo(127, cancel_me_name)]
        result = filter_jobs_to_cancel(
            test_cancel_job_name, current_job_id, list_of_job_info)

        self.assertEquals(1, len(result))
        self.assertEquals(127, result[0])

    def test_find_prior_running_jobs_lists_prior_of_same_job(self):
        test_cancel_job_name = "canceller of jobs"
        current_job_id = 123
        list_of_job_info = [JobInfo(122, test_cancel_job_name)]
        result = filter_jobs_to_cancel(
            test_cancel_job_name, current_job_id, list_of_job_info)
        self.assertEquals(1, len(result))
        self.assertEquals(122, result[0])
