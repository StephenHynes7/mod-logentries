#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Hynes Stephen, sthynes8@gmail.com
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

"""This Class is a plugin for Logentries which will forward data to your Logentris account.
   A free 30 Day Trial can be started here https://logentries.com/quick-start/
"""

import urllib2
import json
import re
import time
import datetime
from collections import deque

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'log_data',
    'external': False,
}


def get_instance(plugin):
    logger.debug("Get a Logentries broker for plugin %s" % plugin.get_name())
    instance = Logentries_Broker(plugin)
    return instance


class Logentries_Broker(BaseModule):
    # Class for Logentries Broker

    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.uuid_regex = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        self.host = getattr(
            modconf, 'host', 'https://js.logentries.com/v1/logs/')
        self.token = getattr(modconf, 'token', None)
        if self.token is None:
            self.is_uuid = bool(re.match(self.uuid_regex, self.token))
            if not self.is_uuid:
                raise Exception
        self.endpoint = self.host + self.token
        self.queue_size = getattr(modconf, 'queue_size', 10)
        self.queue = deque([])

    def init(self):
        logger.info(
            "[Logentries Broker] I init the %s server connection to %s" %
            (self.get_name(), str(self.endpoint)))

    def send_data(self):
        while len(self.queue) > 0:
            data = self.queue.popleft()
            timestamp = datetime.datetime.fromtimestamp(
                time.getime()).strftime('%H:%M:%S %d-%m-%Y')
            msg = json.dumps(
                {"event": {'timestamp': timestamp, 'data': data['log']}})
            req = urllib2.Request(self.endpoint, msg)
            try:
                urllib2.urlopen(req)
            except urllib2.URLError as e:
                logger.error("Can't send log message to Logentries %s", e)

    def manage_logentries_brok(self, b):
        data = b.data
        if data is None:
            return
        self.queue.append(data)
        if len(self.queue) >= self.queue_size:
            logger.debug("Queue is full, sending logs to Logentries")
            self.send_data()
