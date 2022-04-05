#!/usr/bin/python
from setuptools import setup
import os


# See WEBLCM_PYTHON_EXTRA_MODULES in weblcm_python.mk or equivalent
environment_variable_value = os.environ.get('WEBLCM_PYTHON_EXTRA_MODULES', '')
add_modules = []
if len(environment_variable_value) > 0:
	extra_modules = [s.strip() for s in environment_variable_value.split()]
	if 'WEBLCM_PYTHON_BLUETOOTH' in extra_modules:
		add_modules += ['weblcm_bluetooth', 'weblcm_ble', 'weblcm_bluetooth_plugin',
		                'weblcm_bluetooth_ble', 'weblcm_bluetooth_ble_logger',
		                'weblcm_tcp_connection', 'bt_module_extended',
		                'weblcm_bluetooth_controller_state']
	if 'WEBLCM_PYTHON_HID' in extra_modules:
		add_modules += ['weblcm_hid_barcode_scanner']
	if 'WEBLCM_PYTHON_VSP' in extra_modules:
		add_modules += ['weblcm_vsp_connection']


setup(
	name='weblcm-python',
	version='1.0',
	py_modules=[
		'__main__', 'weblcm_network', 'weblcm_log', 'weblcm_def', 'weblcm_swupdate',
		'weblcm_users', 'weblcm_files', 'weblcm_advanced', 'weblcm_network_status',
		'weblcm_settings', 'weblcm_datetime', 'weblcm_modem'
	] + add_modules
)
