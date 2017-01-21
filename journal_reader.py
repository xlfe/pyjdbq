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
import itertools
from tzlocal import get_localzone
import time

# get local timezone
local_tz = get_localzone()

valid_fields = ['priority', 'message', 'errno', 'syslog_facility', 'syslog_identifier', 'syslog_pid', '_pid', '_uid',
                '_gid', 'unit', '_comm', '_exe', '_cmdline', '_cap_effective', '_audit_session', '_audit_loginuid',
                '_systemd_cgroup', '_systemd_session', '_systemd_unit', '_systemd_user_unit', '_systemd_owner_uid',
                '_systemd_slice', '_selinux_context', '_boot_id', '_machine_id', '_hostname', '_transport',
                '_kernel_device', '_kernel_subsystem', '_udev_sysname', '_udev_devnode', '_udev_devlink', 'code_file',
                'code_line', 'code_function', '__realtime_timestamp', '_source_realtime_timestamp']

def chunker(iterable, chunksize):
    """
    Return elements from the iterable in `chunksize`-ed lists. The last returned
    chunk may be smaller (if length of collection is not divisible by `chunksize`).

    >>> print list(chunker(xrange(10), 3))
    [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    """
    i = iter(iterable)
    while True:
        wrapped_chunk = [list(itertools.islice(i, int(chunksize)))]
        if not wrapped_chunk[0]:
            break
        yield wrapped_chunk.pop()

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
        self.log = log
        self.total_shipped = 0
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

        if not self.bucket or len(self.bucket) == 1:
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

        while self.poll.poll():
            if self.journal.process() != journal.APPEND:
                continue

            #get all entries currently available
            for entry in self.journal:
                #print transform_entry(entry)
                self.bucket.append(transform_entry(entry))
                self.cursor = entry['__CURSOR']

            self.check_bucket()

    def ship_logs(self):
        """
        Now ship the logs to BigQuery
        """
        count = len(self.bucket)
        for chunk in chunker(self.bucket, self.COUNT_THRESHOLD):
            self.writer.put(chunk)
        self.last_ship = datetime.datetime.now()
        self.save_cursor()
        self.log.debug('SHIPPED count={}'.format(count))
        self.total_shipped += count
        if self.total_shipped > 500:
            self.log.info('SHIPPED count={}'.format(self.total_shipped))
            self.total_shipped = 0
        self.bucket = []




