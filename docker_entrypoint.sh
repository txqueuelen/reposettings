#!/usr/bin/env sh

if [ -n "$CONFIG" ]; then
    echo "$CONFIG" > reposettings.yml
fi

if [ ! -e reposettings.yml ]; then
    echo "Cannot find reposettings.yml. Either set \$CONFIG to the yaml contents or mount a config file."
    exit 1
fi

python3 /reposettings/reposettings.py reposettings.yml
