#!/usr/bin/env bash
# Here's how you run this:
# screen -DS puller bash ev3dev/gitpuller.sh

while sleep 10; do git pull origin master; done