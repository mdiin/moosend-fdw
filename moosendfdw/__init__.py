from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres
from datetime import datetime

try:
    from urllib2.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

from logging import DEBUG, ERROR, WARNING

import json
import re

def coerce_column_value(value, column_type):
    if value is None:
        return None
    if column_type == "integer":
        return int(value);
    if column_type == "text":
        return str(value);
    if column_type == "timestamp with time zone":
        timestamp_re = re.compile(r"^/Date\((\d+)([+-])(\d{4})\)/$")
        match = timestamp_re.match(value)
        (unix_timestamp, tz_mod, tz) = match.groups()
        return datetime.utcfromtimestamp(int(unix_timestamp) / 1000);
    if column_type == "timestamp without time zone":
        timestamp_re = re.compile(r"^/Date\((\d+)([+-])(\d{4})\)/$")
        match = timestamp_re.match(value)
        (unix_timestamp, tz_mod, tz) = match.groups()
        return datetime.fromtimestamp(int(unix_timestamp) / 1000);
    return value;

class MoosendFDW(ForeignDataWrapper):
    """A foreign data wrapper for Moosend

    The following options are accepted:

    - api_key (Required)
    - list_id (Required)
    - primary_key (Required for updates)
    - page_size (Optional, defaults to 500)

    Column types available are:

    - integer
    - text
    - timestamp with time zone
    - timestamp without time zone

    Have fun!"""

    def __init__(self, options, columns):
        super(MoosendFDW, self).__init__(options, columns)
        self.endpoint_url = 'http://api.moosend.com/v3/'
        self.api_key = options.get('api_key', None)
        self.list_id = options.get('list_id', None)
        self.primary_key_column_name = options.get('primary_key', None)
        self.page_size = options.get('page_size', 500)

        if self.api_key is None:
            log_to_postgres("MoosendFDW: You must supply an API key to Moosend in the options.", ERROR)

        if self.list_id is None:
            log_to_postgres("MoosendFDW: You must supply a mailing list ID in the options.", ERROR)

        self.columns = columns

    @property
    def rowid_column(self):
        if self.primary_key_column_name is not None:
            return self.primary_key_column_name

        return super.rowid_column

    def fetch_page(self, page_num):
        response = urlopen(self.endpoint_url
                           + 'lists/'
                           + self.list_id
                           + '/subscribers/Subscribed.json?'
                           + 'apikey=' + self.api_key
                           + '&Page=' + str(page_num)
                           + '&PageSize=' + str(self.page_size))
        results = json.loads(
            response.read()
        )

        log_to_postgres(results)
        if results["Code"] != 0:
            log_to_postgres("MoosendFDW: " + results["Error"], ERROR)
            return (None, None)

        return (results["Context"], results["Context"]["Paging"]["TotalPageCount"])

    def col(self, column, subscriber):
        try:
            return coerce_column_value(subscriber[column], self.columns[column].base_type_name)
        except KeyError:
            for field in subscriber["CustomFields"]:
                if field["Name"] == column:
                    return coerce_column_value(field["Value"], self.columns[column].base_type_name)
        log_to_postgres("MoosendFDW: " + column + " could not be matched to output from Moosend API.", WARNING)
        return None

    def execute(self, quals, columns):
        first_batch, total_pages = self.fetch_page(1)

        if first_batch is None:
            return

        for subscriber in first_batch["Subscribers"]:
            yield {c: self.col(c, subscriber) for c in self.columns}

        for page_num in range(2, total_pages + 1):
            batch, x = self.fetch_page(page_num)
            for subscriber in batch["Subscribers"]:
                yield {c: self.col(c, subscriber) for c in self.columns}

    #def insert(self, new_values):

    #def update(self, old_values, new_values):

    #def delete(self, old_values):

