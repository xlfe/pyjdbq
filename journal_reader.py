import select
from systemd import journal

j = journal.Reader()
j.log_level(journal.LOG_INFO)

# j.add_match(_SYSTEMD_UNIT="systemd-udevd.service")
j.seek_tail()
j.get_previous()
# j.get_next() # it seems this is not necessary.

p = select.poll()
p.register(j, j.get_events())


# Privileged programs (currently UID 0) may attach OBJECT_PID= to a message. This will instruct systemd-journald to attach additional fields on behalf of the caller:
#
# OBJECT_PID=PID
# PID of the program that this message pertains to.
#
# OBJECT_UID=, OBJECT_GID=, OBJECT_COMM=, OBJECT_EXE=, OBJECT_CMDLINE=, OBJECT_AUDIT_SESSION=, OBJECT_AUDIT_LOGINUID=, OBJECT_SYSTEMD_CGROUP=, OBJECT_SYSTEMD_SESSION=, OBJECT_SYSTEMD_OWNER_UID=, OBJECT_SYSTEMD_UNIT=, OBJECT_SYSTEMD_USER_UNIT=
# These are additional fields added automatically by systemd-journald. Their meaning is the same as _UID=, _GID=, _COMM=, _EXE=, _CMDLINE=, _AUDIT_SESSION=, _AUDIT_LOGINUID=, _SYSTEMD_CGROUP=, _SYSTEMD_SESSION=, _SYSTEMD_UNIT=, _SYSTEMD_USER_UNIT=, and _SYSTEMD_OWNER_UID= as described above, except that the process identified by PID is described, instead of the process which logged the message.



while p.poll():
    if j.process() != journal.APPEND:
        continue

    # Your example code has too many get_next() (i.e, "while j.get_next()" and "for event in j") which cause skipping entry.
    # Since each iteration of a journal.Reader() object is equal to "get_next()", just do simple iteration.
    for entry in j:
        if entry['MESSAGE'] != "":
            print(str(entry['__REALTIME_TIMESTAMP'] )+ ' ' + entry['MESSAGE'])

            d={
                "__CURSOR": "s=7a21f60d8b474a968def5877e0e2d899;i=ecbc;b=dd707a9d389e4ad79e19a3f0f6b9579f;m=1338c3823;t=53ace3472db0a;x=5148263d5d8f497b",
                "__REALTIME_TIMESTAMP": "1472032201169674",
                "__MONOTONIC_TIMESTAMP": "5159794723",
                "_BOOT_ID": "dd707a9d389e4ad79e19a3f0f6b9579f",
                "_UID": "0",
                "_GID": "0",
                "_SYSTEMD_SLICE": "system.slice",
                "_MACHINE_ID": "f137185ae6794af08819dec11effe24b",
                "_CAP_EFFECTIVE": "3fffffffff",
                "_TRANSPORT": "syslog",
                "SYSLOG_FACILITY": "9",
                "_SYSTEMD_CGROUP": "/system.slice/crond.service",
                "_SYSTEMD_UNIT": "crond.service",
                "_HOSTNAME": "router.home",
                "_SELINUX_CONTEXT": "system_u:system_r:system_cronjob_t:s0-s0:c0.c1023",
                "SYSLOG_IDENTIFIER": "anacron",
                "_COMM": "anacron",
                "_EXE": "/usr/sbin/anacron",
                "_CMDLINE": "/usr/sbin/anacron -s",
                "SYSLOG_PID": "1454",
                "_PID": "1454",
                "_SOURCE_REALTIME_TIMESTAMP": "1472032201169558"
            }
