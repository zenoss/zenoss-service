#!/usr/bin/env bash

#####
# This script is here because I want the files that this guy spits out to have
# non-root ownership, and serviced will panic if run in a container under a 
# UID that doesn't really exist
#
# Example:
#  ./add_user.sh $UID
#  ./add_user.sh 1000

set -e

groupadd --gid $2 builder
useradd --uid $1 --gid $2 --comment "" builder
