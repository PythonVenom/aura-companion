#!/bin/bash
curl -s "wttr.in/?format=%t+%C" | sed 's/+/ /g'
