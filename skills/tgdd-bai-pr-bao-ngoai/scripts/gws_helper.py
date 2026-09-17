#!/usr/bin/env python3
"""Shared gws CLI wrapper for the PR article pipeline.

Every workspace rule about Google Workspace access is enforced here in one
place: the MWG company profile, the `command gws` form that bypasses shell
aliases, and the keyring noise that gws writes to stderr.
"""
import json
import os
import subprocess
import sys

GWS_CONFIG_DIR = os.path.expanduser("~/.config/gws")
EXPECTED_ACCOUNT = os.environ.get("GWS_EXPECTED_ACCOUNT", "")


def _env():
    env = dict(os.environ)
    env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = GWS_CONFIG_DIR
    return env


def gws(service, resource, method, params=None, body=None, upload=None,
        upload_type=None, helper=None, extra=None, cwd=None):
    """Call gws and return the parsed JSON response.

    `helper` runs a `+name` helper command (e.g. `+upload`) instead of a
    resource/method pair. Helpers accept absolute paths; `files create
    --upload` does not, so prefer the helper for binary uploads.
    """
    cmd = ["gws", service]
    if helper:
        cmd.append(helper)
        if extra:
            cmd += extra
    else:
        cmd += [resource, method]
    cmd += ["--format", "json"]
    if params:
        cmd += ["--params", json.dumps(params)]
    if body:
        cmd += ["--json", json.dumps(body)]
    if upload:
        cmd += ["--upload", upload]
        if upload_type:
            cmd += ["--upload-content-type", upload_type]
    if extra and not helper:
        cmd += extra

    proc = subprocess.run(cmd, capture_output=True, text=True, env=_env(), cwd=cwd)
    raw = "\n".join(
        line for line in proc.stdout.splitlines()
        if not line.startswith("Using keyring backend")
    ).strip()

    if proc.returncode != 0 or not raw:
        sys.stderr.write("gws call failed: %s\n" % " ".join(cmd[:5]))
        sys.stderr.write((proc.stdout or "")[-1500:] + "\n")
        sys.stderr.write((proc.stderr or "")[-1500:] + "\n")
        raise SystemExit(1)

    data = json.loads(raw)
    if isinstance(data, dict) and "error" in data:
        sys.stderr.write("gws API error: %s\n" % json.dumps(data["error"])[:800])
        raise SystemExit(1)
    return data


def assert_account():
    """Refuse to write to the wrong Google account.

    Getting this wrong publishes a client's article into a personal Drive, so
    it is checked before any write rather than trusted from configuration.

    Set GWS_EXPECTED_ACCOUNT to the address that should own the output. Leaving
    it unset skips the check and says so, rather than silently blocking every
    run or silently writing wherever gws happens to be logged in.
    """
    profile = gws("gmail", "users", "getProfile", params={"userId": "me"})
    actual = profile.get("emailAddress", "")
    if not EXPECTED_ACCOUNT:
        sys.stderr.write(
            "GWS_EXPECTED_ACCOUNT is not set — writing as %s without checking.\n"
            % actual)
        return actual
    if actual != EXPECTED_ACCOUNT:
        sys.stderr.write(
            "Wrong Google account: %s (expected %s). Stopping before any write.\n"
            % (actual, EXPECTED_ACCOUNT))
        raise SystemExit(1)
    return actual


def create_folder(name, parent):
    return gws("drive", "files", "create",
               body={"name": name,
                     "mimeType": "application/vnd.google-apps.folder",
                     "parents": [parent]})["id"]


def upload_file(path, parent, name):
    """Upload binary media via the +upload helper (accepts absolute paths)."""
    return gws("drive", None, None, helper="+upload",
               extra=[path, "--parent", parent, "--name", name])["id"]


def share_anyone_reader(file_id):
    gws("drive", "permissions", "create",
        params={"fileId": file_id},
        body={"role": "reader", "type": "anyone"})


def share_anyone_writer(file_id):
    """Anyone with the link may edit.

    This is the agreed hand-off mode for a PR article: the newspaper's editor
    edits the Doc in place instead of mailing revisions back. It also means
    anyone holding the link can change or delete the content, so it is applied
    only to the delivered article, never to source or evidence files.
    """
    gws("drive", "permissions", "create",
        params={"fileId": file_id},
        body={"role": "writer", "type": "anyone"})


def folder_id_from(value):
    """Accept a raw folder ID or any Drive folder URL."""
    value = value.strip()
    for marker in ("/folders/", "id="):
        if marker in value:
            value = value.split(marker, 1)[1]
    return value.split("?")[0].split("&")[0].split("/")[0]
