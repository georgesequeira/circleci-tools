# CircleCi Tools

This repo was inspired by an issue with CircleCI-2.0 Workflows described here: https://discuss.circleci.com/t/auto-cancel-redundant-builds-not-working-for-workflow/13852/30

In short: If you have two workflows running for the same branch, we want the newer one to run and cancel the older one.

This REPO has a simple script `cancel_prior_builds.py` that will accomplish this by calling the job cancel API.


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


# How to use?
This repo has a Docker image built so that you can simply add the following to your current CircleCi-2.0 config

```
version: 2
jobs:
  cancel_prior_builds:
    docker:
      - image: gt50201/circleci-tools:latest
    working_directory: ~/tools
    parallelism: 1
    steps:
      - run: ./cancel_prior_builds.py

..
..
..

workflows:
  version: 2
  something_descriptive_or_not:
    jobs:
      - cancel_prior_builds
      - childJob1:
          requires:
            - cancel_prior_builds
        - childJob2:
          requires:
            - cancel_prior_builds
```
