from google.cloud import bigquery
from datetime import datetime
from socket import inet_aton

import json
import subprocess
import ipaddress
import socket
import struct
import os

# ENVIRONMENT SETTINGS
project_id = "phronesis-dev"
dataset_id = "wireguard"
table_id   = "peers"
filename    = "config.json"

# WIREGUARD SETTINGS
iptables        = 'en01'
serverPublicKey = 'SVk0ZpdgR8TkHbG/PuNoBS1jgkOwEBCQvvOG9qB+byg='
server_ip       = '10.0.0.1'
dns             = '192.168.0.210'
endpoint        = 'wgpi.ddns.net'
listen_port     = '51820'
allowed_ips     = ['10.0.0.0/24', '192.168.0.0/24', '10.0.0.1/32']

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "phronesis-dev-f169beb7eb5a.json"

def write_json(new_data, filename='config.json'):
    with open(filename,'a') as file:
       file.write(json.dumps(new_data))
       file.write('\n')
       file.close()

def timestamp():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    return timestamp

def bqLoad():
    # BIGQUERY SETTINGS
    bq_client = bigquery.Client()
    table = '{}.{}.{}'.format(project_id, dataset_id, table_id)

    # LOAD METRICS INTO BIGQUERY
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.autodetect = True

    with open(filename, "rb") as source_file:
        job = bq_client.load_table_from_file(
            source_file,
            table,
            location="US",  # Must match the destination dataset location.
            job_config=job_config,
        )

    print(job.result())
    print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table))
    
def getPeers():
    # BIGQUERY SETTINGS
    bq_client = bigquery.Client()

    # LOAD METRICS INTO BIGQUERY
    job_config = bigquery.QueryJobConfig()
    
    sql = """
        SELECT t.*
        FROM (SELECT t.*,
                     ROW_NUMBER() OVER (PARTITION BY ipAddress
                                        ORDER BY time DESC
                                       ) as seqnum
              FROM `wireguard.peers` t
             ) t
        WHERE seqnum = 1;
        """
        
    query_job = bq_client.query(
        sql,
        location="US",
        job_config=job_config,
    ) 
    query_job.result()
    return(query_job)

def getNewIp():
    # PRINT LAST ENTRY
    ipAddresses = []
    for row in getPeers():
        ipAddresses.append("{}".format(row.ipAddress))
            
    sortedIps = sorted(ipAddresses, key=lambda ip: struct.unpack("!L", inet_aton(ip))[0])
    print(sortedIps)
        
    newIp = ipaddress.ip_address(sortedIps[-1]) + 1
    print(newIp)
        
    return(newIp)
    
def clientConfig(wgPeerConfig, privKey):
    print(wgPeerConfig)
    print(privKey)
    client_config = f"[Interface]\n" \
        f"Address = {wgPeerConfig['ipAddress']}\n" \
        f"DNS = {dns}\n" \
        f"PrivateKey = {privKey}\n"
    client_config += f"PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {iptables} -j MASQUERADE\n" \
        f"PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {iptables} -j MASQUERADE\n"

    
    client_config += f"[Peer]\n" \
        f"PublicKey = {serverPublicKey}\n" \
        f"AllowedIPs = {', '.join(allowed_ips)}\n" \
        f"Endpoint = {endpoint}:{listen_port}\n"
        
    print("*"*10 + f" client-config " + "*"*10)
    print(client_config)
    with open(f"wg0.conf", "wt") as f:
        f.write(client_config)
        
    print('Client config created successfully...')
    
def addPeer():
    privKey = subprocess.check_output(
        "wg genkey", shell=True).decode("utf-8").strip()
    pubKey = subprocess.check_output(
        f"echo '{privKey}' | wg pubkey", shell=True).decode("utf-8").strip()

    wgPeerConfig = {'id': socket.gethostname() + '-' + privKey[0:5],
                    'ipAddress': str(getNewIp()),
                    'publicKey': pubKey,
                    'time': timestamp()}

    print(json.dumps(wgPeerConfig, indent=1))
    write_json(wgPeerConfig, 'config.json')
    bqLoad()
    os.remove('config.json')
    clientConfig(wgPeerConfig, privKey)
    #wgInit()

def baseConfig():
    privKey = subprocess.check_output(
        "wg genkey", shell=True).decode("utf-8").strip()
    pubKey = subprocess.check_output(
        f"echo '{privKey}' | wg pubkey", shell=True).decode("utf-8").strip()

    wgPeerConfig = {'id': socket.gethostname() + '-' + privKey[0:5],
                    'ipAddress': '10.0.0.2',
                    'publicKey': pubKey,
                    'time': timestamp()}

if __name__ == "__main__":
    addPeer()
    #baseConfig()