#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from .require_module import gate_imports

try:
    from sshtunnel import SSHTunnelForwarder
except ImportError:
    SSHTunnelForwarder = None
    gate_imports(False, 'aws', 'sshtunnel')

from WrenchCL.Tools.ccLogBase import logger


class _SshTunnelManager:
    """
    Handles creation and teardown of an SSH tunnel to a remote database host.
    Requires config with SSH credentials and target DB host/port.
    """

    def __init__(self, config: dict):
        """
        Initialize SSH tunnel manager with DB + SSH credentials.

        :param config: Dictionary with DB and SSH config:
            - PGHOST, PGPORT, PGPASSWORD, etc.
            - SSH_TUNNEL:
                - SSH_SERVER
                - SSH_PORT
                - SSH_USER
                - (SSH_PASSWORD | SSH_KEY_PATH)
        """
        self.config = config
        self.ssh_config = config.get("SSH_TUNNEL", {})
        self.tunnel: SSHTunnelForwarder | None = None

        self._validate_ssh_config()

        # Mask sensitive fields for safe logging
        def mask(val):
            return f"{val[:3]}...{val[-3:]}" if isinstance(val, str) and len(val) > 6 else val

        safe_config = {k: mask(v) if k == "PGPASSWORD" else v for k, v in self.config.items()}
        safe_ssh_config = {
                k: mask(v) if k in {"SSH_PASSWORD", "SSH_KEY_PATH"} else v
                for k, v in self.ssh_config.items()
                }

        logger.debug(f"SSH Tunnel Manager initialized with config: {safe_config}")
        logger.debug(f"SSH-specific configuration: {safe_ssh_config}")

    def _validate_ssh_config(self):
        """Raise if essential SSH tunnel credentials are missing."""
        required = ["SSH_SERVER", "SSH_PORT", "SSH_USER"]
        for key in required:
            if key not in self.ssh_config:
                raise ValueError(f"Missing required SSH config: {key}")

        if not (self.ssh_config.get("SSH_PASSWORD") or self.ssh_config.get("SSH_KEY_PATH")):
            raise ValueError("SSH tunnel requires either SSH_PASSWORD or SSH_KEY_PATH")

    def start_tunnel(self) -> tuple[str, int]:
        """
        Starts the SSH tunnel.

        :returns: Local bind address and port tuple.
        :raises Exception: If tunnel fails to start.
        """
        logger.debug(
                f"Starting SSH tunnel to {self.ssh_config['SSH_SERVER']}:{self.ssh_config['SSH_PORT']} "
                f"as user {self.ssh_config['SSH_USER']}"
                )

        self.tunnel = SSHTunnelForwarder(
                ssh_address_or_host=(self.ssh_config["SSH_SERVER"], self.ssh_config["SSH_PORT"]),
                ssh_username=self.ssh_config["SSH_USER"],
                ssh_password=self.ssh_config.get("SSH_PASSWORD"),
                ssh_pkey=self.ssh_config.get("SSH_KEY_PATH"),
                remote_bind_address=(self.config["PGHOST"], self.config["PGPORT"])
                )

        try:
            self.tunnel.start()
        except Exception as e:
            logger.error(f"Failed to start SSH tunnel: {e}")
            raise

        logger.debug(f"SSH tunnel active at 127.0.0.1:{self.tunnel.local_bind_port}")
        return "127.0.0.1", self.tunnel.local_bind_port

    def stop_tunnel(self):
        """Stops the tunnel if running."""
        if self.tunnel:
            logger.debug("Stopping SSH tunnel...")
            self.tunnel.stop()
            logger.debug("SSH tunnel stopped.")
