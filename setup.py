#!/usr/bin/python
from setuptools import setup
import os


environment_variable_value = os.environ.get('WEBLCM_PYTHON_EXTRA_MODULES', '')
if len(environment_variable_value) > 0:
	extra_modules = [s.strip() for s in environment_variable_value.split()]
else:
	extra_modules = []


setup(
	name='weblcm-python',
	version='1.0',
	py_modules=[
		'__main__', 'weblcm_network', 'weblcm_log', 'weblcm_def', 'weblcm_swupdate',
		'weblcm_users', 'weblcm_files', 'weblcm_advanced', 'weblcm_network_status',
		'weblcm_settings', 'weblcm_datetime', 'weblcm_modem'
	] + extra_modules
)
