#!/bin/bash
#python addPeer.py
wg-quick up /etc/wireguard/wg0.conf

ping 10.0.0.1 -c 5
ping 10.0.0.1 -i 30 &

status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start my_second_process: $status"
  exit $status
fi

#/usr/local/bin/envoy -c /etc/envoy/envoy.yaml --concurrency 1

sleep infinity

