from google.cloud import secretmanager
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
server_ip   = '10.10.10.1'
endpoint    = 'wgpi.ddns.net'
listen_port = '51820'
allowed_ips = ['10.10.10.0/24', '192.168.0.0/24', '10.10.10.1/32']

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "phronesis-dev-f169beb7eb5a.json"

# GCP SECRETS MANAGER - GET SECRETS
def access_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

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
        
def serverConfig():
    serverPrivateKey = access_secret('WG_PRIVATE_KEY')
    server_config = "[Interface]\n" \
        f"Address = {server_ip}\n" \
        f"ListenPort = {listen_port}\n" \
        f"PrivateKey = {serverPrivateKey}\n"
        
    for row in getPeers():
        server_config += f"[Peer]\n" \
            f"PublicKey = {row.publicKey}\n" \
            f"AllowedIPs = {row.ipAddress}\n"
            
    print("*"*10 + " Server-Conf " + "*"*10)
    print(server_config)
    with open(f"server.conf", "wt") as f:
        f.write(server_config)
        
    print('Server config created successfully...')
    
def clientConfig(wgPeerConfig, privKey):
    print(wgPeerConfig)
    print(privKey)
    client_config = f"[Interface]\n" \
        f"Address = {wgPeerConfig['ipAddress']}\n" \
        f"PrivateKey = {privKey}\n"

    serverPublicKey = access_secret('WG_PUBLIC_KEY')
    client_config += f"[Peer]\n" \
        f"PublicKey = {serverPublicKey}\n" \
        f"AllowedIPs = {', '.join(allowed_ips)}\n" \
        f"DNS = {server_ip}\n" \
        f"Endpoint = {endpoint}\n"
        
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
    serverConfig()
    
def wgInit():
    subprocess.check_output("wg-quick up wg0.conf", shell=True).decode("utf-8").strip()
    os.remove('wg0.conf')

if __name__ == "__main__":
    addPeer()