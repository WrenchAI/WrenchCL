#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#
import logging

from sshtunnel import SSHTunnelForwarder

from ..Tools.WrenchLogger import Logger

logger = Logger()
logging.getLogger("paramiko").setLevel(40)

class _SshTunnelManager:
    """
    Manages the SSH tunnel for securely connecting to a remote database server. This class uses the SSHTunnelForwarder
    to establish and manage the SSH tunnel.

    Attributes:
        config (dict): Configuration dictionary containing SSH and database connection details.
        ssh_config (dict): Configuration dictionary specific to SSH tunneling.
        tunnel (SSHTunnelForwarder): Instance of the SSHTunnelForwarder to manage the SSH tunnel.
    """

    def __init__(self, config):
        """
        Initializes the _SshTunnelManager with the given configuration.

        :param config: Configuration dictionary containing SSH and database connection details.
                       Example:
                       {
                           "PGHOST": "database_host",
                           "PGPORT": 5432,
                           "PGDATABASE": "database_name",
                           "PGUSER": "database_user",
                           "PGPASSWORD": "database_password",
                           "SSH_TUNNEL": {
                               "SSH_SERVER": "ssh_server",
                               "SSH_PORT": 22,
                               "SSH_USER": "ssh_user",
                               "SSH_PASSWORD": "ssh_password",
                               "SSH_KEY_PATH": "path_to_ssh_key"
                           }
                       }
        :type config: dict
        """
        self.config = config
        self.ssh_config = config['SSH_TUNNEL']
        self.tunnel = None

    def start_tunnel(self):
        """
        Starts the SSH tunnel using the provided SSH configuration. The tunnel forwards a local port to the
        remote database server.

        :returns: A tuple containing the local bind address and port.
        :rtype: tuple
        """
        self.tunnel = SSHTunnelForwarder(
            ssh_address_or_host=(self.ssh_config['SSH_SERVER'], self.ssh_config['SSH_PORT']),
            ssh_username=self.ssh_config['SSH_USER'],
            ssh_password=self.ssh_config.get('SSH_PASSWORD', None),
            ssh_pkey=self.ssh_config.get('SSH_KEY_PATH', None),
            remote_bind_address=(self.config['PGHOST'], self.config['PGPORT'])
        )
        self.tunnel.start()
        return '127.0.0.1', self.tunnel.local_bind_port

    def stop_tunnel(self):
        """
        Stops the SSH tunnel if it is currently running.
        """
        if self.tunnel:
            self.tunnel.stop()

