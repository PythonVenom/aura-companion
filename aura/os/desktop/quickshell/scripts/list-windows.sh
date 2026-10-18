#!/bin/bash
wmctrl -l | awk '{ 
    id=$1; 
    title=substr($0, index($0,$4)); 
    gsub(/"/, "\\\"", title);
    if (title != "") print "{\"id\":\""id"\",\"title\":\""title"\"},"
}' | sed '$ s/,$//' | awk 'BEGIN{print "["} {print} END{print "]"}'
