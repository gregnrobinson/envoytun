#!/bin/bash
apt install net-tools -y
ifconfig wg0 10.0.0.1 netmask 255.255.255.0 up
wg syncconf wg0 /etc/wireguard/wg0.conf
