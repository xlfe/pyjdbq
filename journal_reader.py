"""

Read from journald log

# Privileged programs (currently UID 0) may attach OBJECT_PID= to a message. This will instruct systemd-journald to attach additional fields on behalf of the caller:
#
# OBJECT_PID=PID
# PID of the program that this message pertains to.
#
# OBJECT_UID=, OBJECT_GID=, OBJECT_COMM=, OBJECT_EXE=, OBJECT_CMDLINE=, OBJECT_AUDIT_SESSION=, OBJECT_AUDIT_LOGINUID=, OBJECT_SYSTEMD_CGROUP=, OBJECT_SYSTEMD_SESSION=, OBJECT_SYSTEMD_OWNER_UID=, OBJECT_SYSTEMD_UNIT=, OBJECT_SYSTEMD_USER_UNIT=
# These are additional fields added automatically by systemd-journald. Their meaning is the same as _UID=, _GID=, _COMM=, _EXE=, _CMDLINE=, _AUDIT_SESSION=, _AUDIT_LOGINUID=, _SYSTEMD_CGROUP=, _SYSTEMD_SESSION=, _SYSTEMD_UNIT=, _SYSTEMD_USER_UNIT=, and _SYSTEMD_OWNER_UID= as described above, except that the process identified by PID is described, instead of the process which logged the message.

"""

import select
from systemd import journal
from datetime import datetime

class JournalReader(object):
    CURSOR_FILE = '/tmp/pyjqbq-journal-cursor'
    COUNT_THRESHOLD = 500
    SECOND_THRESHOLD = 60

    def __init__(self):

        j = journal.Reader()
        j.log_level(journal.LOG_DEBUG)

        try:
            with open(self.CURSOR_FILE,'r') as cfile:
                self.cursor = cfile.read()
            j.seek_cursor(self.cursor)
        except IOError:
            #No cursor - start from the earliest available data
            j.seek_head()

        j.get_previous()

        p = select.poll()
        p.register(j, j.get_events())

        self.journal = j
        self.poll = p
        self.bucket = []
        self.last_ship = datetime.now()

    def full_bucket(self):
        """
        Do we need to ship the log entries yet?
        """

        if len(self.bucket) >= self.COUNT_THRESHOLD:
            return True

        if (datetime.now() - self.last_ship).total_seconds() >= self.SECOND_THRESHOLD:
            return True

        return False

    def run(self):

        while self.poll.poll():
            if self.journal.process() != journal.APPEND:
                #Ignore NOP and INVALIDATE entries
                continue

            for entry in self.journal:
                self.bucket.append(entry)

                if self.full_bucket():
                    self.ship_logs()

    def ship_logs(self):
        """
        Now ship the logs to BigQuery
        """
        raise NotImplementedError()




