#!/bin/bash
set -e

env | sed 's/^/export /' > /tmp/env
echo "* * * * * django . /tmp/env && /usr/local/bin/python /app/manage.py cron >> /app/logs/cron 2>&1" > /etc/cron.d/spistresci

rsyslogd
cron
tail -f /var/log/syslog
