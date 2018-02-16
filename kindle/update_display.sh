#!/bin/sh
cd /tmp
curl -O http://lunchbox:5000/kindle-signage.png && eips -fg kindle-signage.png