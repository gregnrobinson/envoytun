from google.cloud import bigquery
from google.cloud import storage
from google.cloud import secretmanager
from datetime import datetime
import base64

# ENVIRONMENT SETTINGS
project_id = "phronesis-310405"
dataset_id = "wireguard"
table_id = "peers"
filename = "/tmp/server.conf"

# WIREGUARD SETTINGS
server_ip = '10.0.0.1'
endpoint = 'wgpi.ddns.net'
listen_port = '51820'
iptables = "eno1"
allowed_ips = ['10.0.0.0/24', '192.168.0.0/24', '10.0.0.1/32']


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


def timestamp():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    gcs_timestamp = now.strftime('%Y-%m-%d%H%M%S')
    return timestamp, gcs_timestamp


def gcs():
    # UPLOAD TO GCS
    gcs_client = storage.Client()
    bucket = gcs_client.get_bucket('wg-server-config')
    blob = bucket.blob("wg0.conf")
    blob.upload_from_filename(filename)

    print(
        "File {} uploaded to {}.".format(
            blob, filename
        )
    )

# GCP SECRETS MANAGER - GET SECRETS


def access_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')


def serverConfig(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
   #f"Address = {server_ip}\n" \
    serverPrivateKey = access_secret('WG_PRIVATE_KEY')
    server_config = "[Interface]\n" \
        f"ListenPort = {listen_port}\n" \
        f"PrivateKey = {serverPrivateKey}\n"
    #server_config += f"PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o {iptables} -j MASQUERADE\n" \
    #    f"PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o {iptables} -j MASQUERADE\n"

    for row in getPeers():
        server_config += f"[Peer]\n" \
            f"PublicKey = {row.publicKey}\n" \
            f"AllowedIPs = {row.ipAddress}\n"

    print("*"*10 + " Server-Conf " + "*"*10)
    print(server_config)
    with open(f"/tmp/server.conf", "wt") as f:
        f.write(server_config)

    print('Server config created successfully...')

    gcs()
