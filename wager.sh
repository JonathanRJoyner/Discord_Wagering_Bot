#!/bin/sh
python3 interaction.py &
python3 scheduler.py && fg
