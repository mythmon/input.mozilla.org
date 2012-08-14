#!/bin/bash

set -e

SVN="/usr/bin/svn"
INPUT_DIR="/data/input/python/input.mozilla.com/reporter"
VENDOR_DIR="$INPUT_DIR/vendor"

SYNC_DIR="/data/input/www/django/input.mozilla.com/reporter/"

# update locales
pushd locale > /dev/null
$SVN revert -R .
$SVN up
./compile-mo.sh .
popd > /dev/null

echo -e "Updating vendor..."
cd $VENDOR_DIR
git pull
git submodule sync
git submodule update --init --recursive

echo -e "Updating reporter..."
cd $INPUT_DIR
git fetch origin

# Note: We're deploying from the master branch now to shave off some
# workflow steps because this is a dead project. (willkg)
git checkout origin/master
git submodule update --init

cd /data/input;
/usr/bin/rsync -aq --exclude '.git*' --delete /data/input/python/ /data/input/www/django

cd $SYNC_DIR
# FIXME: Commenting this out because it's not working.
# /usr/bin/python26 $VENDOR_DIR/src/schematic/schematic migrations

# Pull in highcharts.src.js - our lawyers make us do this.
/usr/bin/python26 $INPUT_DIR/manage.py cron get_highcharts
/usr/bin/python26 $INPUT_DIR/manage.py compress_assets

# FIXME: Commenting this out because it's not working.
# if [ -d $SYNC_DIR/migrations/sites ]; then
#   /usr/bin/python26 $VENDOR_DIR/src/schematic/schematic migrations/sites
# fi

# Clustering commented out because it takes too long during release.
# If urgent, start by hand (in a screen). If not urgent, wait until clustering
# cron job reoccurs.
#su - apache -s /bin/sh -c '/usr/bin/python26 /data/input/www/django/input.mozilla.com/reporter/manage.py cron cluster'

/data/input/deploy
#/data/bin/omg_push_generic_live.sh .

#/data/bin/issue-multi-command.py generic 'service httpd reload'

