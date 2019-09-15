#!/usr/bin/env bash

docker run --rm -e "DB_HOST=172.17.0.1" -e "DB_PORT=27017" -p 80:80 corrector
