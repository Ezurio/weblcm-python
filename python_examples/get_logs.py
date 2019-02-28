from systemd import journal

j = journal.Reader()
j.this_boot()
# j.log_level(journal.LOG_INFO)
# j.add_match(_SYSTEMD_UNIT="systemd-udevd.service")
for entry in j:
	print(str(entry['__REALTIME_TIMESTAMP']) + " " + entry['SYSLOG_IDENTIFIER'] + ":" + entry['MESSAGE'])
	# print(entry)
