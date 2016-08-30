#!/usr/bin/env python

import json

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


class BigQueryWriter(object):
    RETRIES = 2

    def put(self, rows):
        response = self.bigquery.tabledata().insertAll(
            projectId=self.project_id,
            datasetId=self.dataset_id,
            tableId=self.table_name,
            body={
                'rows': rows
            }
        ).execute(num_retries=self.RETRIES)

        if response['kind'] == "bigquery#tableDataInsertAllResponse" and len(response) == 1:
            return True
        else:
            raise ValueError(json.dumps(response))

    def __init__(self, project_id, dataset_id, table_name, credentials_path):

        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_name = table_name

        self.credentials = GoogleCredentials.from_stream(credentials_path)
        self.bigquery = discovery.build('bigquery', 'v2', credentials=self.credentials)


