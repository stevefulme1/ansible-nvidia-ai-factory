# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Redfish REST client for DGX BMC management."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class RedfishClient(object):
    """Thin wrapper around the DMTF Redfish REST API on DGX BMC."""

    def __init__(self, base_url, username, password, validate_certs=True):
        """Initialize the Redfish client.

        Args:
            base_url: Base URL of the BMC (e.g. ``https://dgx-bmc``).
            username: BMC username for Basic authentication.
            password: BMC password for Basic authentication.
            validate_certs: Whether to verify TLS certificates.
        """
        if not HAS_REQUESTS:
            raise ImportError("The 'requests' library is required.")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.verify = validate_certs
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def get(self, path):
        """Issue a GET request to a Redfish resource.

        Args:
            path: Resource path relative to the base URL
                  (e.g. ``/redfish/v1/Systems/1``).

        Returns:
            Parsed JSON response as a dict.

        Raises:
            requests.exceptions.HTTPError: On non-2xx responses.
        """
        url = "{0}{1}".format(self.base_url, path)
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def post(self, path, payload=None):
        """Issue a POST request (used for Redfish Actions).

        Args:
            path: Action URI (e.g.
                  ``/redfish/v1/Systems/1/Actions/ComputerSystem.Reset``).
            payload: JSON-serialisable dict for the request body.

        Returns:
            Parsed JSON response as a dict, or empty dict on 204.

        Raises:
            requests.exceptions.HTTPError: On non-2xx responses.
        """
        url = "{0}{1}".format(self.base_url, path)
        resp = self.session.post(url, json=payload or {})
        resp.raise_for_status()
        if resp.status_code == 204:
            return {}
        return resp.json()

    def get_collection(self, path):
        """Retrieve all members of a Redfish collection.

        Automatically follows ``Members@odata.nextLink`` for pagination.

        Args:
            path: Collection path (e.g. ``/redfish/v1/Systems``).

        Returns:
            List of member dicts.
        """
        members = []
        while path:
            data = self.get(path)
            members.extend(data.get("Members", []))
            path = data.get("Members@odata.nextLink")
        return members
