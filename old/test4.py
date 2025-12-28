#!/usr/bin/env python3
"""
Upload every *.pdf in ./pdf to Open‑WebUI and attach each file to an existing
knowledge entry (knowledge_id).  The script now supports both the old
`/api/files/upload` and the new `/api/files` upload endpoints.
"""

import sys
import json
import argparse
import pathlib
import getpass
from typing import Dict, List

import requests
from tqdm import tqdm
from tabulate import tabulate

# ----------------------------------------------------------------------
# --------------------------- CONFIGURATION ---------------------------
# ----------------------------------------------------------------------
DEFAULT_BASE_URL = "http://du-webui"   # change if needed
PDF_DIR = pathlib.Path("pdf")                # folder that contains PDFs
CHUNK_SIZE = 8192                            # bytes per read
knowledge_id='092f9730-5aa0-48d1-90eb-8b85fc81537a'

# ----------------------------------------------------------------------
# --------------------------- HELPERS ---------------------------------
# ----------------------------------------------------------------------
def auth_headers(token: str = None, user: str = None, pwd: str = None) -> Dict[str, str]:
    """Return a dict with the correct Authorization header."""
    if token:
        return {"Authorization": f"Bearer {token}"}
    if user and pwd:
        import base64
        b64 = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return {"Authorization": f"Basic {b64}"}
    raise ValueError("You must supply either a token or (user + pwd).")


def get_server_version(base_url: str, headers: Dict[str, str]) -> str:
    """Try a few known version‑endpoints and return the first string we get."""
    for path in ("/api/version", "/api/info", "/version"):
        try:
            resp = requests.get(f"{base_url.rstrip('/')}{path}", headers=headers, timeout=5)
            if resp.ok:
                # `/api/version` returns plain text, `/api/info` returns JSON.
                try:
                    return resp.json().get("version", resp.text.strip())
                except Exception:
                    return resp.text.strip()
        except Exception:
            continue
    return "unknown"


def upload_one_file(base_url: str,
                    headers: Dict[str, str],
                    file_path: pathlib.Path,
                    upload_endpoint: str) -> str:
    """
    Stream‑upload a single file.
    Returns the `file_id` string on success.
    """
    url = f"{base_url.rstrip('/')}{upload_endpoint}"
    file_size = file_path.stat().st_size

    # ------------------------------------------------------------------
    # Build a tiny wrapper that lets `requests` stream the file while we
    # update the tqdm bar.
    # ------------------------------------------------------------------
    class TqdmReader:
        def __init__(self, generator):
            self.gen = generator
            self.buffer = b""

        def read(self, n=-1):
            # `requests` will call this repeatedly until it gets b"".
            if n == -1:
                # read everything (used only for the very last chunk)
                data = b"".join(self.gen)
            else:
                while len(self.buffer) < n:
                    try:
                        self.buffer += next(self.gen)
                    except StopIteration:
                        break
                data, self.buffer = self.buffer[:n], self.buffer[n:]
            pbar.update(len(data))
            return data

    # ------------------------------------------------------------------
    # Generator that yields raw bytes from the file (no extra memory copy)
    # ------------------------------------------------------------------
    def chunk_generator():
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

    # ------------------------------------------------------------------
    # Show a progress bar that is updated from the reader class above
    # ------------------------------------------------------------------
    with tqdm(total=file_size,
              unit="B",
              unit_scale=True,
              unit_divisor=1024,
              desc=f"Uploading {file_path.name}",
              leave=False) as pbar:

        files = {"file": (file_path.name, TqdmReader(chunk_generator()))}
        resp = requests.post(url, headers=headers, files=files)

    # ------------------------------------------------------------------
    # 405 → caller may be using the wrong endpoint, let the caller decide
    # ------------------------------------------------------------------
    if resp.status_code == 405:
        raise RuntimeError("Method Not Allowed (405) – wrong upload endpoint.")
    if resp.status_code != 200:
        raise RuntimeError(f"Upload failed [{resp.status_code}] {resp.text}")

    payload = resp.json()
    file_id = payload.get("file_id")
    if not file_id:
        raise RuntimeError(f"Unexpected upload response: {payload}")
    return file_id


def attach_to_knowledge(base_url: str,
                        headers: Dict[str, str],
                        file_id: str,
                        knowledge_id: str) -> Dict:
    """
    Attach an already‑uploaded file to an existing knowledge entry.
    Returns the JSON representation of the knowledge document after the
    attachment.
    """
    url = f"{base_url.rstrip('/')}/api/knowledge/{file_id}"
    params = {"knowledge_id": knowledge_id}
    resp = requests.put(url, headers=headers, params=params)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Attaching file_id={file_id} to knowledge_id={knowledge_id} "
            f"failed [{resp.status_code}] {resp.text}"
        )
    return resp.json()


def list_recent_knowledge(base_url: str,
                         headers: Dict[str, str],
                         limit: int = 10) -> List[Dict]:
    """Convenient helper – show the newest knowledge entries."""
    url = f"{base_url.rstrip('/')}/api/knowledge"
    resp = requests.get(url, headers=headers, params={"limit": limit})
    resp.raise_for_status()
    return resp.json()


# ----------------------------------------------------------------------
# --------------------------- MAIN LOGIC -------------------------------
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description=(
            "Upload every *.pdf in ./pdf to Open‑WebUI and attach each file "
            "to an existing knowledge entry (knowledge_id)."
        )
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Root URL of the Open‑WebUI server (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--knowledge-id",
        required=True,
        help="ID of the knowledge entry you want to attach the PDFs to.",
    )
    parser.add_argument(
        "--upload-endpoint",
        default="/api/v1/files",            # new style – will be overridden automatically if 405 is seen
        help="Path (relative to base‑url) that accepts POST uploads. "
             "Default `/api/files`.  Use `/api/files/upload` for older servers.",
    )
    auth = parser.add_mutually_exclusive_group(required=True)
    auth.add_argument("--token", help="Bearer token (preferred).")
    auth.add_argument("--user", help="Username (will be prompted for password).")
    parser.add_argument("--pwd", help="Password (if omitted you will be prompted).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only upload files, do NOT attach to the knowledge entry.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="After processing, list the most recent knowledge entries (limit 10).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Build the auth header
    # ------------------------------------------------------------------
    if args.token:
        headers = auth_headers(token=args.token)
    else:
        pwd = args.pwd or getpass.getpass(prompt="Password: ")
        headers = auth_headers(user=args.user, pwd=pwd)

    # ------------------------------------------------------------------
    # Print server version (helps you know which API you are using)
    # ------------------------------------------------------------------
    version = get_server_version(args.base_url, headers)
    print(f"🖥️  Open‑WebUI server version: {version}")

    # ------------------------------------------------------------------
    # Verify PDF directory exists
    # ------------------------------------------------------------------
    if not PDF_DIR.is_dir():
        sys.exit(f"❌  Directory '{PDF_DIR}' does not exist or is not a folder.")
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        sys.exit(f"❌  No *.pdf files found in folder '{PDF_DIR}'.")

    print(f"\n🚀  Found {len(pdf_files)} PDF file(s) in '{PDF_DIR}'.\n")

    # ------------------------------------------------------------------
    # Process each PDF
    # ------------------------------------------------------------------
    results = []        # for the final table

    for pdf_path in pdf_files:
        try:
            # ---------- 1️⃣  Upload ----------
            try:
                file_id = upload_one_file(
                    args.base_url, headers, pdf_path, args.upload_endpoint
                )
            except RuntimeError as e:
                # If we got a 405, retry automatically with the legacy endpoint.
                if "Method Not Allowed" in str(e):
                    legacy_endpoint = "/api/files/upload"
                    print(
                        f"⚠️  {pdf_path.name}: {e} – retrying with legacy endpoint "
                        f"`{legacy_endpoint}` ..."
                    )
                    file_id = upload_one_file(
                        args.base_url, headers, pdf_path, legacy_endpoint
                    )
                else:
                    raise

            # ---------- 2️⃣  (optional) attach ----------
            knowledge_doc_id = "<dry‑run>"
            if not args.dry_run:
                attach_resp = attach_to_knowledge(
                    args.base_url, headers, file_id, args.knowledge_id
                )
                knowledge_doc_id = attach_resp.get("id", "<no‑id>")
            results.append(
                {
                    "pdf": pdf_path.name,
                    "file_id": file_id,
                    "knowledge_doc_id": knowledge_doc_id,
                }
            )
            print(
                f"✅  {pdf_path.name} → file_id={file_id[:8]}… → "
                f"knowledge_doc_id={knowledge_doc_id[:8]}…"
            )
        except Exception as exc:
            print(f"❌  Failed processing {pdf_path.name}: {exc}")
            results.append(
                {"pdf": pdf_path.name, "file_id": "<error>", "knowledge_doc_id": "<error>"}
            )

    # ------------------------------------------------------------------
    # Pretty‑print a summary table
    # ------------------------------------------------------------------
    print("\n=== Summary =====================================================")
    print(
        tabulate(
            results,
            headers={"pdf": "PDF", "file_id": "File‑ID", "knowledge_doc_id": "Knowledge‑Doc‑ID"},
            tablefmt="github",
        )
    )
    # ------------------------------------------------------------------
    # Optional sanity‑check: list the newest knowledge entries
    # ------------------------------------------------------------------
    if args.list:
        try:
            recent = list_recent_knowledge(args.base_url, headers)
            print("\n🔎  10 most recent knowledge entries:")
            for i, entry in enumerate(recent, start=1):
                print(
                    f"{i:2}. id={entry.get('id')[:8]}…  "
                    f"file_id={entry.get('file_id')[:8]}…  "
                    f"title={entry.get('title') or '-'}"
                )
        except Exception as exc:
            print(f"⚠️  Could not list knowledge entries: {exc}")

    print("\n🎉  Done!\n")


if __name__ == "__main__":
    main()
