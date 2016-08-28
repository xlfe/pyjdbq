"""
pyjdbq (journald to big query)

stream journald logs into a biq query table
"""

import argparse
import json
import logging

from bigquery_writer import BigQueryWriter
from journal_reader import JournalReader

def get_logger(debug=False):
    log = logging.getLogger('pyjdbq')
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--dataset', help='BigQuery dataset', default='logs')
    parser.add_argument('--table', help='BigQuery table', default='pyjdbq')
    parser.add_argument('--creds', help='JSON credentials file for BigQuery', default='./credentials.json')

    parser.add_argument('--cursor', help='Full path to store the cursor file', default='/tmp/pyjdbq-journal-cursor')
    parser.add_argument('--count', help='Events to store before inserting', type=int, default=500)
    parser.add_argument('--timeout', help='Seconds to wait for COUNT logs before inserting anyway', type=int, default=30)

    parser.add_argument('--debug', action='store_true', help='Extra verbose')
    args = parser.parse_args()

    try:
        with open(args.creds, 'r') as credentials_json:
            credentials = json.load(credentials_json)
        project_id = credentials['project_id']
    except IOError:
        print 'No credentials file found using path: {}'.format(args.creds)
        print 'Please create a service account and select "Furnish a new private key" in JSON format'
        print 'The service account requires Big Query "Data Editor" permissions to write the logs'
        exit()

    writer = BigQueryWriter(project_id, args.dataset, args.table, args.creds)
    log = get_logger(debug=args.debug)
    reader = JournalReader(writer=writer, log=log, args=args)
    reader.run()




