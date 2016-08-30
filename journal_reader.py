"""

Read from journald log

Set the frequency to add logs to the table using

"""

import select
from systemd import journal
import datetime
from uuid import UUID
import json
import pytz
from tzlocal import get_localzone

# get local timezone
local_tz = get_localzone()

valid_fields = ['priority', 'message', 'errno', 'syslog_facility', 'syslog_identifier', 'syslog_pid', '_pid', '_uid',
                '_gid', 'unit', '_comm', '_exe', '_cmdline', '_cap_effective', '_audit_session', '_audit_loginuid',
                '_systemd_cgroup', '_systemd_session', '_systemd_unit', '_systemd_user_unit', '_systemd_owner_uid',
                '_systemd_slice', '_selinux_context', '_boot_id', '_machine_id', '_hostname', '_transport',
                '_kernel_device', '_kernel_subsystem', '_udev_sysname', '_udev_devnode', '_udev_devlink', 'code_file',
                'code_line', 'code_function', '__realtime_timestamp', '_source_realtime_timestamp']

def convert_value(value):
    if type(value) == UUID:
        return str(value)
    elif isinstance(value, datetime.datetime):
        #return a UTC timestamp - conversion required because systemd returns a naive timestamp...
        return local_tz.localize(value).isoformat()
    elif isinstance(value, datetime.timedelta):
        return value.total_seconds()
    return str(value)

def transform_entry(entry):

    t = {}
    extra = {}

    for k,v in entry.iteritems():

        if k.lower() in valid_fields:
            t[k.lower()] = convert_value(entry[k])

        elif k.startswith('__') is False:
            extra[k.lower()] = convert_value(entry[k])

    if extra:
        t['extra'] = json.dumps(extra)

    return {
        'insertId': entry['__CURSOR'],
        'json': t
    }

class JournalReader(object):

    def __init__(self, writer, log, args):

        self.writer = writer
        j = journal.Reader()
        j.log_level(journal.LOG_DEBUG)
        self.log = log
        self.CURSOR_FILE = args.cursor
        self.COUNT_THRESHOLD = args.count
        self.SECOND_THRESHOLD = args.timeout

        try:
            with open(self.CURSOR_FILE,'r') as cfile:
                self.cursor = cfile.read()
            j.seek_cursor(self.cursor)
            self.log.info('Loaded cursor from file')
        except IOError:
            #No cursor - start from the earliest available data
            self.log.info('No cursor start from the start')
            j.seek_head()

        j.get_previous()

        p = select.poll()
        p.register(j, j.get_events())

        self.journal = j
        self.poll = p
        self.bucket = []
        self.last_ship = None

    def save_cursor(self):
        with open(self.CURSOR_FILE,'w') as cfile:
            cfile.write(self.cursor)

    @property
    def seconds_since_last_ship(self):
        if not self.last_ship:
            return self.SECOND_THRESHOLD + 10
        return (datetime.datetime.now() - self.last_ship).total_seconds()

    def check_bucket(self):
        """
        Do we need to ship the log entries yet?
        """

        if not self.bucket:
            self.log.debug('Nothing in bucket')
            return False

        if len(self.bucket) >= self.COUNT_THRESHOLD:
            self.log.debug('Bucket is full')
            self.ship_logs()

        elif self.seconds_since_last_ship >= self.SECOND_THRESHOLD:
            self.log.debug('Timeout passed')
            self.ship_logs()

        self.log.debug('not ready to ship')
        return False


    def run(self):
        """

        """

        while True:

            #get all entries currently available
            for entry in self.journal:
                self.bucket.append(transform_entry(entry))
                self.cursor = entry['__CURSOR']

                self.check_bucket()
            else:
                self.check_bucket()

            max_delay = self.SECOND_THRESHOLD - self.seconds_since_last_ship

            if max_delay < 0:
                #wait indefinately for something to ship...
                self.poll.poll()
            else:
                self.poll.poll(max_delay*1000)

            if self.journal.process() != journal.APPEND:
                #Ignore NOP and INVALIDATE entries
                self.log.debug('NOP or INVALIDATE')
                continue


    def ship_logs(self):
        """
        Now ship the logs to BigQuery
        """
        count = len(self.bucket)
        self.writer.put(self.bucket)
        self.last_ship = datetime.datetime.now()
        self.save_cursor()
        self.log.info('SHIPPED count={}'.format(count))
        self.bucket = []




