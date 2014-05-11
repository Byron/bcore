#!/usr/bin/env bash
# NOTE: this script must be executed from bdevel travis tests, assuming to be at the bdevel root

context=lib/components/core/src/python/bcmd/tests
bin/posix/be @$context go daemon-command || exit
# daemonize it
[ ! -f pidfile ] || exit
bin/posix/be @$context go daemon-command -d pidfile || exit

# when it returned, pid file sholdn't exist anymore - it's hard to test for it in this async mode we are in 
[ ! -f pidfile ] || exit
