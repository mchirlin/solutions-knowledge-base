"""
Pytest configuration and shared fixtures for dynamic SAIL testing.

Uses appian-locust (in standalone mode, no Locust load framework) to:
  1. Optionally deploy a SAIL interface via a web API
  2. Open the rendered page via appian-locust's site visitor
  3. Provide a SailUiForm fixture for interaction tests

Environment variables:
  APPIAN_HOST       – Appian base URL (default: eng-test-aidc-dev.appianpreview.com)
  APPIAN_USERNAME   – login user  (default: admin.user)
  APPIAN_PASSWORD   – login password (default: ineedtoadminister)
  APPIAN_SITE       – site URL stub (default: test-site)
  APPIAN_PAGE       – page URL stub (default: test-site)
  DEPLOY_API_PATH   – web API path for deploying SAIL (default: /suite/webapi/tooySww)
  SKIP_DEPLOY       – set to "1" to skip the deploy step (use existing page)
"""

# gevent monkey-patch MUST happen before any other imports touch ssl/socket
from gevent import monkey
monkey.patch_all()

import os
import sys
import pytest
import requests

# ── appian-locust must be importable ──────────────────────────────────
APPIAN_LOCUST_PATH = os.path.expanduser("~/repo/appian-locust")
if APPIAN_LOCUST_PATH not in sys.path:
    sys.path.insert(0, APPIAN_LOCUST_PATH)

from appian_locust.appian_client import appian_client_without_locust

# ── Environment / defaults ────────────────────────────────────────────
HOST = os.environ.get("APPIAN_HOST", "https://eng-test-aidc-dev.appianpreview.com")
DEPLOY_API_PATH = os.environ.get("DEPLOY_API_PATH", "/suite/webapi/tooySw")
DEPLOY_API = f"{HOST}{DEPLOY_API_PATH}"
SITE_NAME = os.environ.get("APPIAN_SITE", "test-site")
PAGE_NAME = os.environ.get("APPIAN_PAGE", "test-interface")
SKIP_DEPLOY = os.environ.get("SKIP_DEPLOY", "0") == "1"

USERNAME = os.environ.get("APPIAN_USERNAME", "admin.user")
PASSWORD = os.environ.get("APPIAN_PASSWORD", "ineedtoadminister")


def _read_sail_file(path: str) -> str:
    """Read a .sail file relative to the repo root."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full = os.path.join(repo_root, path)
    with open(full, "r") as f:
        return f.read()


def deploy_sail_interface(sail_expression: str, auth: tuple) -> bool:
    """
    POST the SAIL expression to the deploy web API so the test site
    renders it on the next visit.
    """
    resp = requests.post(
        DEPLOY_API,
        data=sail_expression,
        headers={"Content-Type": "text/plain"},
        auth=auth,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Deploy failed ({resp.status_code}): {resp.text}\n"
            f"URL: {DEPLOY_API}\n"
            f"Hint: Set SKIP_DEPLOY=1 if the page is already deployed, "
            f"or set DEPLOY_API_PATH to the correct web API endpoint."
        )
    return True


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def appian_auth():
    """Resolve credentials (env vars or fail fast)."""
    if not USERNAME or not PASSWORD:
        pytest.skip("Set APPIAN_USERNAME and APPIAN_PASSWORD env vars to run dynamic tests")
    return [USERNAME, PASSWORD]


@pytest.fixture(scope="session")
def appian_client(appian_auth):
    """
    Standalone appian-locust client (no Locust framework).
    Logs in once for the entire test session.
    """
    client = appian_client_without_locust(HOST)
    client.login(auth=appian_auth)
    client.get_client_feature_toggles()
    yield client
    client.logout()


@pytest.fixture(scope="module")
def deployed_contact_form(appian_auth):
    """Deploy the contact details SAIL interface to the test site."""
    if SKIP_DEPLOY:
        return True
    sail = _read_sail_file("sail/AS_FM_captureUserContactDetails.sail")
    deploy_sail_interface(sail, tuple(appian_auth))
    return True


@pytest.fixture()
def contact_form(appian_client, deployed_contact_form):
    """
    Open a fresh instance of the contact form for each test.
    Returns a SailUiForm ready for interaction.
    """
    form = appian_client.visitor.visit_site(SITE_NAME, PAGE_NAME)
    return form
