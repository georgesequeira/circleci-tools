FROM python:2.7.14-slim

USER root

RUN useradd --create-home circleci

USER circleci

RUN mkdir /home/circleci/tools
COPY --chown=circleci:circleci ./cancel_prior_builds.py tools/
