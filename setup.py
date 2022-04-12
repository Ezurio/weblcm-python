#!/usr/bin/python

from setuptools import setup
import os

environment_variable_value = os.environ.get('WEBLCM_PYTHON_EXTRA_PACKAGES', '')
if len(environment_variable_value) > 0:
    extra_packages = [s.strip() for s in environment_variable_value.split()]
else:
    extra_packages = []

setup(
    name='weblcm-python',
    version='1.0',
    packages=['weblcm'] + extra_packages,
    scripts=['weblcm-python'],
)
