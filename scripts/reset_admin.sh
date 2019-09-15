#!/usr/bin/env bash

if [ $# -ne 1 ] ; then
  echo ./reset_admin.sh [www container id]
  exit
fi

docker exec --interactive $1 python < scripts/create_admin.py