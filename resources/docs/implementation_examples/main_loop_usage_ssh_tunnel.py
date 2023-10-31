import os

import psycopg2
from sshtunnel import SSHTunnelForwarder

from WrenchCL import rdsInstance, wrench_logger

# Read the content of the .pem file
with open('wrench-bastion.pem', 'r') as file:
    rsa_key_content = file.read()

# Set the environment variable
os.environ['RSA_KEY'] = rsa_key_content

ssh_config_rsa = {
    'SSH_TUNNEL' : {
        'SSH_SERVER': '34.201.30.245',
        'SSH_PORT': 22,
        'SSH_USER': 'ec2-user',
        'USE_RSA_ENV': True
    },
    'PGHOST': 'qa-wrench-ai.ce5sivkxtgbs.us-east-1.rds.amazonaws.com',
    'PGPORT': 5432,
    'PGDATABASE': 'enricher',
    'PGUSER': 'svs-rds',
    'PGPASSWORD': 'nBenZUi6hGzpkQqMs9cHkcAVqsyDVNQvrymN58Md'
}

# Use RDS class with RSA key from environment variable
rdsInstance.load_configuration(ssh_config_rsa)
rdsInstance._connect()
rdsInstance.execute_query('SELECT * FROM "SummitVentureStudios".svs_assignees limit 10')
