# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""REST client for NVIDIA Base Command Manager (BCM) CMDaemon API."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class BcmClient(object):
    """Client for the BCM CMDaemon REST API (port 8081)."""

    def __init__(self, base_url, username=None, password=None,
                 token=None, validate_certs=True):
        """Initialize the BCM client.

        Authenticates via username/password or an existing token.

        Args:
            base_url: CMDaemon URL (e.g. ``https://bcm-head:8081``).
            username: CMDaemon username (optional if *token* given).
            password: CMDaemon password (optional if *token* given).
            token: Pre-existing auth token (optional).
            validate_certs: Whether to verify TLS certificates.
        """
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required.")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = validate_certs
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        if token:
            self.session.headers["Authorization"] = "Bearer {0}".format(token)
        elif username and password:
            self._authenticate(username, password)

    def _authenticate(self, username, password):
        """Obtain an auth token from CMDaemon.

        Args:
            username: CMDaemon username.
            password: CMDaemon password.
        """
        url = "{0}/api/auth/login".format(self.base_url)
        resp = self.session.post(url, json={
            "username": username,
            "password": password,
        })
        resp.raise_for_status()
        data = resp.json()
        token = data.get("token", data.get("access_token", ""))
        self.session.headers["Authorization"] = "Bearer {0}".format(token)

    def _url(self, path):
        return "{0}{1}".format(self.base_url, path)

    def get(self, path, params=None):
        """GET a resource.

        Args:
            path: API path (e.g. ``/api/nodes``).
            params: Optional query parameters.

        Returns:
            Parsed JSON response.
        """
        resp = self.session.get(self._url(path), params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, payload=None):
        """POST to create or act on a resource.

        Args:
            path: API path.
            payload: JSON body dict.

        Returns:
            Parsed JSON response.
        """
        resp = self.session.post(self._url(path), json=payload or {})
        resp.raise_for_status()
        return resp.json()

    def delete(self, path):
        """DELETE a resource.

        Args:
            path: API path.

        Returns:
            True on success.
        """
        resp = self.session.delete(self._url(path))
        resp.raise_for_status()
        return True

    # ---- Convenience methods ----

    def list_nodes(self, category=None):
        """List cluster nodes, optionally filtered by category."""
        params = {}
        if category:
            params["category"] = category
        return self.get("/api/nodes", params=params)

    def get_node(self, node_name):
        """Get details for a single node."""
        return self.get("/api/nodes/{0}".format(node_name))

    def list_jobs(self, state=None):
        """List workload jobs, optionally filtered by state."""
        params = {}
        if state:
            params["state"] = state
        return self.get("/api/jobs", params=params)

    def get_job(self, job_id):
        """Get details for a single job."""
        return self.get("/api/jobs/{0}".format(job_id))

    def submit_job(self, payload):
        """Submit a new workload job."""
        return self.post("/api/jobs", payload=payload)

    def cancel_job(self, job_id):
        """Cancel a running job."""
        return self.post("/api/jobs/{0}/cancel".format(job_id))
