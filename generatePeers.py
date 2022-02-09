from google.cloud import bigquery
from google.cloud import storage
from google.cloud.storage import blob
from datetime import datetime

# ENVIRONMENT SETTINGS
project_id = "phronesis-dev"
dataset_id = "wireguard"
table_id   = "peers"
filename    = "server.conf"

def timestamp():
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    gcs_timestamp = now.strftime('%Y-%m-%d%H%M%S')
    return timestamp, gcs_timestamp

def peerConfig():
    # BIGQUERY SETTINGS
    bq_client = bigquery.Client()
    table = '{}.{}.{}'.format(project_id, dataset_id, table_id)

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

    # Start the query, passing in the extra configuration.
    query_job = bq_client.query(
        sql,
        # Location must match that of the dataset(s) referenced in the query
        # and of the destination table.
        location="US",
        job_config=job_config,
    )  # API request - starts the query

    query_job.result()  # Waits for the query to finish

    server_config = "[Interface]\n"
    for row in query_job:
        server_config += f"[Peer]\n" \
            f"PublicKey = {row.publicKey}\n" \
            f"AllowedIPs = {row.ipAddress}\n"

    print("*"*10 + " Server-Conf " + "*"*10)
    print(server_config)
    with open(f"server.conf", "wt") as f:
        f.write(server_config)

def gcs():
    # UPLOAD TO GCS
    gcs_client = storage.Client()
    bucket = gcs_client.get_bucket('wg-server-config')
    blob = bucket.blob("%s.conf" % timestamp()[1])
    blob.upload_from_filename(filename)

    print(
        "File {} uploaded to {}.".format(
            blob, filename
        )
    )

if __name__ == "__main__":
    peerConfig()
    gcs()
