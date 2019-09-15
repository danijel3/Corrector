#!/usr/bin/env bash

docker image save corrector | gzip - > corrector.tar.gz
scp corrector.tar.gz whisper:~/corrector