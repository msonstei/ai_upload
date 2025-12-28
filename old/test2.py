#!/usr/bin/env python3
"""
Upload a file to Open‑WebUI and add it to the Knowledge base
using the /api/v1/files and /api/v1/knowledge/{file_id} endpoints.

Author: <your name>
"""

import os
import sys
import json
import argparse
from pathlib import Path

import requests
from tqdm import tqdm

# ----------------------------------------------------------------------
# Configuration ---------------------------------------------------------
# ----------------------------------------------------------------------
DEFAULT_BASE_URL = "http://du-webui"   # change if needed
DEFAULT_TOKEN = "sk-9f3d08b64518474fb8219de725e8efd6"
# ----------------------------------------------------------------------
# Helper functions ------------------------------------------------------
# ----------------------------------------------------------------------
def _auth_headers(token: str = None, user: str = None, pwd: str = None) -> dict:
    """
    Build the Authorization header.
    Prefer a Bearer token; fall back to Basic auth if user/pwd are supplied.
    """
    if token:
        return {"Authorization": f"Bearer {token}"}
    elif user and pwd:
        import base64
        b64 = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return {"Authorization": f"Basic {b64}"}
    else:
        raise ValueError("Either a token or (user & pwd) must be supplied.")


def upload_file(base_url: str, headers: dict, file_path: Path) -> str:
    """
    POST /api/v1/files
    Returns the `file_id` of the newly uploaded file.
    """
    url = f"{base_url.rstrip('/')}/api/v1/files"

    # Open‑WebUI expects a `multipart/form-data` request with the field name `file`.
    # We stream the file to avoid loading the whole thing into memory.
    file_size = file_path.stat().st_size

    with file_path.open("rb") as f:
        # tqdm wraps the file object to show a progress bar.
        with tqdm(total=file_size, unit="B", unit_scale=True,
                  desc=f"Uploading {file_path.name}", leave=False) as pbar:
            def gen():
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    pbar.update(len(chunk))
                    yield chunk

            # `files` dict automatically sets the correct multipart headers.
            files = {"file": (file_path.name, gen())}
            resp = requests.post(url, headers=headers, files=files)

    if resp.status_code != 200:
        raise RuntimeError(
            f"❌ File upload failed [{resp.status_code}] {resp.text}"
        )

    data = resp.json()
    # The API returns: {"file_id": "<uuid>", "filename": "...", ...}
    file_id = data.get("file_id")
    if not file_id:
        raise RuntimeError(f"❌ Unexpected response from /api/v1/files: {data}")

    print(f"✅ Uploaded → file_id = {file_id}")
    return file_id


def add_to_knowledge(base_url: str, headers: dict, file_id: str) -> dict:
    """
    PUT /api/v1/knowledge/{file_id}
    Returns the knowledge‑document object as JSON.
    """
    url = f"{base_url.rstrip('/')}/api/v1/knowledge/{file_id}"
    # No body is required – the server will read the file referenced by file_id.
    resp = requests.put(url, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(
            f"❌ Adding to knowledge failed [{resp.status_code}] {resp.text}"
        )

    doc = resp.json()
    print(f"✅ Knowledge entry created → doc_id = {doc.get('id')}")
    return doc


def list_knowledge(base_url: str, headers: dict, limit: int = 10) -> None:
    """
    GET /api/v1/knowledge?limit=...
    Handy to verify that the document is now searchable.
    """
    url = f"{base_url.rstrip('/')}/api/v1/knowledge"
    params = {"limit": limit}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    items = resp.json()
    print("\n🔎 Recent knowledge entries (most recent first):")
    for i, entry in enumerate(items, 1):
        print(f"{i:2}. id={entry.get('id')[:8]}…  file_id={entry.get('file_id')[:8]}…  "
              f"title={entry.get('title') or '-'}")


# ----------------------------------------------------------------------
# CLI entry point -------------------------------------------------------
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Upload a file to Open‑WebUI and add it to the Knowledge base."
    )
    parser.add_argument("filepath", type=Path,
                        help="Path to the local file you want to ingest.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help="Root URL of the Open‑WebUI server (default: %(default)s).")
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--token", help="Bearer token (preferred).")
    auth.add_argument("--user", help="Username (will prompt for password).")
    parser.add_argument("--pwd", help="Password (if you provide --user without --pwd you will be prompted).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only upload the file, do not call /knowledge endpoint.")
    parser.add_argument("--list", action="store_true",
                        help="After the operation, list the most recent knowledge entries.")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Build auth headers
    # ------------------------------------------------------------------
    if args.token:
        headers = _auth_headers(token=args.token)
    else:
        pwd = args.pwd
        if pwd is None:
            import getpass
            pwd = getpass.getpass(prompt="Password: ")
        headers = _auth_headers(user=args.user, pwd=pwd)

    # ------------------------------------------------------------------
    # Sanity checks
    # ------------------------------------------------------------------
    if not args.filepath.is_file():
        sys.exit(f"❌ File not found: {args.filepath}")

    # ------------------------------------------------------------------
    # 3️⃣ (optional) list recent knowledge entries
    # ------------------------------------------------------------------
    if args.list:
        headers = _auth_headers(token=args.token)
        list_knowledge(args.base_url, headers, 10)
        url = f'{args.base_url}/api/v1/knowledge/list'
        print(url)
        try:
            list_knowledge(args.base_url, headers)
        except Exception as exc:
            print(f"⚠️  Could not list knowledge: {exc}")


    # ------------------------------------------------------------------
    # 1️⃣ Upload file → file_id
    # ------------------------------------------------------------------
    try:
        file_id = upload_file(args.base_url, headers, args.filepath)
    except Exception as exc:
        sys.exit(f"❌ Upload error: {exc}")

    # ------------------------------------------------------------------
    # 2️⃣ (optional) add to knowledge base
    # ------------------------------------------------------------------
    if not args.dry_run:
        try:
            _ = add_to_knowledge(args.base_url, headers, file_id)
        except Exception as exc:
            sys.exit(f"❌ Knowledge error: {exc}")

    # ------------------------------------------------------------------
    # 3️⃣ (optional) list recent knowledge entries
    # ------------------------------------------------------------------
    if args.list:
        try:
            list_knowledge(args.base_url, headers)
        except Exception as exc:
            print(f"⚠️  Could not list knowledge: {exc}")

    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
