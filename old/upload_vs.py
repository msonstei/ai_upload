#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
upload_pdfs_to_openwebui_v2.py

A minimal, robust script that:
  1. Authenticates to Open‑WebUI (JWT endpoint)
  2. Uploads one or more PDF files via /api/files
  3. (Optionally) creates a knowledge entry that points to the uploaded file
  4. Prints clear success / error messages

It works with any recent Open‑WebUI version (>= 0.6) *and* with the legacy
0.5.x JWT endpoint (/api/auth/jwt) – the script auto‑detects which one to use.
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import requests

# ----------------------------------------------------------------------
# Configuration (adjust only if you really need to)
# ----------------------------------------------------------------------
DEFAULT_BASE_URL = "http://du-webui"          # host:port that resolves from your client
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "YOUR_PASSWORD"           # <-- put the real password or pass via CLI
DEFAULT_SECRET_KEY = None                     # optional – only needed if you want to set a custom JWT secret

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def configure_logging(verbose: bool) -> None:
    """Set up a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%H:%M:%S",
    )


def detect_token_endpoint(base_url: str, username: str, password: str) -> Tuple[str, str]:
    """
    Try the modern `/api/auth/token` first; if it 404/405, fall back to the legacy
    `/api/auth/jwt`. Return a tuple (endpoint_path, description).
    """
    session = requests.Session()
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/json"}

    # 1️⃣ modern endpoint
    modern = "/api/auth/token"
    try:
        r = session.post(f"{base_url}{modern}", json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            logging.debug("Modern token endpoint works.")
            return modern, "modern"
    except requests.RequestException as exc:
        logging.debug(f"Modern token endpoint request error: {exc}")

    # 2️⃣ legacy endpoint
    legacy = "/api/auth/jwt"
    try:
        r = session.post(f"{base_url}{legacy}", json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            logging.debug("Legacy token endpoint works.")
            return legacy, "legacy"
    except requests.RequestException as exc:
        logging.debug(f"Legacy token endpoint request error: {exc}")

    # If we get here, neither worked – raise a helpful error.
    raise RuntimeError(
        f"Unable to obtain a JWT from {base_url}. "
        "Tried both /api/auth/token and /api/auth/jwt and got no 200 response."
    )


def get_jwt(base_url: str, username: str, password: str) -> str:
    """Fetch a JWT and return the raw token string."""
    endpoint, kind = detect_token_endpoint(base_url, username, password)
    url = f"{base_url}{endpoint}"
    logging.info(f"Requesting JWT via {kind} endpoint: {url}")

    resp = requests.post(
        url,
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    # ----- error handling -------------------------------------------------
    if resp.status_code != 200:
        # Try to give as much info as possible
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(
            f"Failed to obtain JWT (HTTP {resp.status_code}). Response: {detail}"
        )

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Server returned non‑JSON payload: {resp.text}") from exc

    if "access_token" not in data:
        raise RuntimeError(f"Unexpected JWT payload shape: {data}")

    token = data["access_token"]
    logging.debug(f"Received JWT (truncated): {token[:30]}…")
    return token


def upload_file(base_url: str, jwt: str, pdf_path: Path) -> dict:
    """
    Upload a single PDF via the multipart endpoint.
    Returns the decoded JSON dictionary that Open‑WebUI sends back
    (it contains at least a `file_id` key on success).
    """
    upload_url = f"{base_url}/api/files"
    logging.info(f"Uploading {pdf_path.name} → {upload_url}")

    # ---- 1️⃣ Build the multipart payload ---------------------------------
    # NOTE: **DO NOT** set a Content‑Type header – `requests` will add the correct
    #       multipart boundary automatically.
    files = {"file": (pdf_path.name, pdf_path.open("rb"), "application/pdf")}

    # ---- 2️⃣ Send the request --------------------------------------------
    try:
        resp = requests.post(
            upload_url,
            headers={"Authorization": f"Bearer {jwt}"},   # only Authorization is needed
            files=files,
            timeout=30,
        )
    finally:
        # Close the file handle *immediately* – `requests` reads the stream
        # synchronously, so we can safely close it after the request finishes.
        files["file"][1].close()

    # ---- 3️⃣ Guard the response -----------------------------------------
    if resp.status_code != 200:
        # The server usually returns a JSON error object, but it can also be plain text.
        try:
            err_detail = resp.json()
        except Exception:
            err_detail = resp.text
        raise RuntimeError(
            f"Upload of {pdf_path.name} failed (HTTP {resp.status_code}). "
            f"Server response: {err_detail}"
        )

    try:
        payload = resp.json()
    except json.JSONDecodeError:
        # If the payload is not JSON we fall back to raw text – this is where
        # the `'str' object has no attribute 'items'` error used to happen.
        raise RuntimeError(
            f"Open‑WebUI returned non‑JSON data for {pdf_path.name}: {resp.text}"
        )

    # The successful payload looks like:
    #   {"file_id": "xxxxxxxxxxxxxx", "filename": "...", "size": 12345, ...}
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Unexpected response type for {pdf_path.name}: expected dict, got {type(payload)}"
        )

    logging.debug(f"Upload response JSON: {json.dumps(payload, indent=2)}")
    return payload


def create_knowledge_entry(
    base_url: str,
    jwt: str,
    file_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Create a knowledge entry that references the uploaded file.
    Returns the JSON payload returned by the `/api/knowledge` endpoint.
    """
    url = f"{base_url}/api/knowledge"
    payload = {
        "file_id": file_id,
        "title": title or f"Document – {file_id[:8]}",
        "description": description or "",
    }
    logging.info(f"Creating knowledge entry for file_id={file_id}")

    resp = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {jwt}"},
        timeout=15,
    )

    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(
            f"Failed to create knowledge entry (HTTP {resp.status_code}). Response: {detail}"
        )

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Non‑JSON response from knowledge endpoint: {resp.text}") from exc

    logging.debug(f"Knowledge entry response: {json.dumps(data, indent=2)}")
    return data


def process_one_pdf(
    base_url: str,
    jwt: str,
    pdf_path: Path,
    create_knowledge: bool,
) -> None:
    """Upload a single PDF and (optionally) create a knowledge entry."""
    try:
        upload_payload = upload_file(base_url, jwt, pdf_path)
    except Exception as exc:
        logging.error(f"❌ Failed processing {pdf_path.name}: {exc}")
        return

    # --------------------------------------------------------------
    # At this point `upload_payload` is a dict – we can safely use .items()
    # --------------------------------------------------------------
    file_id = upload_payload.get("file_id")
    if not file_id:
        # Defensive – this should never happen on a 200 response, but we guard anyway.
        logging.error(
            f"⚠️ Upload succeeded but response lacks `file_id`. Full payload: {upload_payload}"
        )
        return

    logging.info(f"✅ Uploaded {pdf_path.name} → file_id={file_id}")

    if create_knowledge:
        try:
            kn_payload = create_knowledge_entry(base_url, jwt, file_id, title=pdf_path.stem)
        except Exception as exc:
            logging.error(f"⚠️ Knowledge entry creation failed for {pdf_path.name}: {exc}")
        else:
            logging.info(
                f"🧠 Knowledge entry created – ID: {kn_payload.get('knowledge_id', 'unknown')}"
            )


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload one or more PDFs to Open‑WebUI (JWT auth)."
    )
    parser.add_argument(
        "pdfs",
        nargs="+",
        type=Path,
        help="Path(s) to the PDF file(s) you want to upload.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help="Base URL of the Open‑WebUI instance (default: %(default)s).",
    )
    parser.add_argument(
        "-u",
        "--username",
        default=DEFAULT_USERNAME,
        help="Open‑WebUI username (default: %(default)s).",
    )
    parser.add_argument(
        "-p",
        "--password",
        default=DEFAULT_PASSWORD,
        help="Open‑WebUI password (default: %(default)s).",
    )
    parser.add_argument(
        "--no-knowledge",
        dest="create_knowledge",
        action="store_false",
        default=True,
        help="Skip the optional creation of a knowledge entry after upload.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show full request/response bodies (debug level).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_cli()
    configure_logging(args.verbose)

    # ------------------------------------------------------------------
    # 1️⃣ Authenticate → JWT
    # ------------------------------------------------------------------
    try:
        jwt_token = get_jwt(args.url, args.username, args.password)
    except Exception as exc:
        logging.error(f"❌ Authentication failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2️⃣ Upload each PDF
    # ------------------------------------------------------------------
    for pdf_path in args.pdfs:
        if not pdf_path.is_file():
            logging.error(f"⚠️ Skipping non‑existent file: {pdf_path}")
            continue
        process_one_pdf(args.url, jwt_token, pdf_path, args.create_knowledge)


if __name__ == "__main__":
    main()
