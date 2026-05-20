# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""REST client for the NVIDIA NGC Catalog API."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class NgcClient(object):
    """Client for the NVIDIA NGC Catalog REST API v2."""

    API_BASE = "https://api.ngc.nvidia.com/v2"

    def __init__(self, api_key, api_base=None, validate_certs=True):
        """Initialize the NGC client.

        Args:
            api_key: NGC API key used as Bearer token.
            api_base: Override for the API base URL (testing).
            validate_certs: Whether to verify TLS certificates.
        """
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required.")
        self.api_base = (api_base or self.API_BASE).rstrip("/")
        self.session = requests.Session()
        self.session.verify = validate_certs
        self.session.headers.update({
            "Authorization": "Bearer {0}".format(api_key),
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _url(self, path):
        return "{0}{1}".format(self.api_base, path)

    def get(self, path, params=None):
        """GET a resource.

        Args:
            path: API path (e.g. ``/orgs``).
            params: Optional query parameters dict.

        Returns:
            Parsed JSON response.
        """
        resp = self.session.get(self._url(path), params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, payload=None):
        """POST to create a resource.

        Args:
            path: API path.
            payload: JSON body dict.

        Returns:
            Parsed JSON response.
        """
        resp = self.session.post(self._url(path), json=payload or {})
        resp.raise_for_status()
        return resp.json()

    def put(self, path, payload=None):
        """PUT to update a resource.

        Args:
            path: API path.
            payload: JSON body dict.

        Returns:
            Parsed JSON response.
        """
        resp = self.session.put(self._url(path), json=payload or {})
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

    def list_orgs(self):
        """List organizations the caller has access to."""
        return self.get("/orgs")

    def list_models(self, org):
        """List models in an organization."""
        return self.get("/org/{0}/models".format(org))

    def get_model(self, org, model_name):
        """Get a specific model."""
        return self.get("/org/{0}/models/{1}".format(org, model_name))

    def list_containers(self, org):
        """List container images in an organization."""
        return self.get("/org/{0}/containers".format(org))

    def get_container(self, org, container_name):
        """Get a specific container image."""
        return self.get("/org/{0}/containers/{1}".format(org, container_name))
