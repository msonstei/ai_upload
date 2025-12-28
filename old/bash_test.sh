#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------
# Configuration – change only if your host/port or credentials differ
# ------------------------------------------------------------------
HOST="du-webui"                     # e.g. du-webui:8080 if you expose a non‑standard port
BASE="http://${HOST}"
USERNAME="msonstein@doyonutilities.com"                    # <-- replace
PASSWORD="!!BCohm211bcohm2"            # <-- replace
PDF_PATH="pdf/Contract.pdf"   # <-- replace with a real file
WEBUI_JWT="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjMxMzlhMjVhLWIwMzYtNDk0ZS1iYmQzLTlhN2Q1MDRhYmRjNiIsImp0aSI6ImZjNDAxZDg5LTZlMzQtNGJiYS1iNzhlLWQzZGQ5YjE2ZGMyMCJ9._nULo_RSmBdB5fPir9pfOMHQedddyuNZDu0k5BFN3nM"
# ------------------------------------------------------------------
# 1️⃣  Get a JWT (you can also copy one from UI → Settings → API Tokens)
# ------------------------------------------------------------------
WEBUI_JWT=$(curl -v -X POST "${BASE}/api/auth/jwt" \
   -H "Content-Type: application/json" \
   -d '{"username":"${USERNAME}","password":"${PASSWORD}"}' |
   jq -r .access_token)

if [[ -z "$WEBUI_JWT" || "$WEBUI_JWT" == "null" ]]; then
   echo "❌ Failed to obtain a JWT – check username/password."
   exit 1
fi
echo "✅ JWT acquired (first 30 chars): ${WEBUI_JWT:0:30}..."

# ------------------------------------------------------------------
# 2️⃣  Verify the token carries the right scopes (optional but helpful)
# ------------------------------------------------------------------
echo "🔎 Token scopes:"
echo "$WEBUI_JWT" | cut -d '.' -f2 | base64 -d | jq .scopes

# ------------------------------------------------------------------
# 3️⃣  Make sure the *real* API endpoint is reachable and allows POST
# ------------------------------------------------------------------
echo "🔎 Checking OPTIONS on /api/files …"
curl -s -i -X OPTIONS "${BASE}/api/files" \
   -H "Authorization: Bearer ${WEBUI_JWT}" | head -n 10

# ------------------------------------------------------------------
# 4️⃣  Upload the PDF (real file)
# ------------------------------------------------------------------
echo "📤 Uploading ${PDF_PATH} …"
FILE_ID=$(curl -s -X POST "${BASE}/api/files" \
   -H "Authorization: Bearer ${WEBUI_JWT}" \
   -F "file=@${PDF_PATH}" |
   jq -r .file_id)

if [[ -z "$FILE_ID" || "$FILE_ID" == "null" ]]; then
   echo "❌ Upload failed – you probably still have a method‑filter in a proxy."
   exit 1
fi
echo "✅ Uploaded → file_id=${FILE_ID}"

# ------------------------------------------------------------------
# 5️⃣  Create a knowledge document that points to the uploaded file
# ------------------------------------------------------------------
KNOW_ID=$(curl -s -X POST "${BASE}/api/knowledge" \
   -H "Authorization: Bearer ${WEBUI_JWT}" \
   -H "Content-Type: application/json" \
   -d "{\"title\":\"$(basename "${PDF_PATH}")\",\"file_id\":\"${FILE_ID}\"}" |
   jq -r .knowledge_id)

if [[ -z "$KNOW_ID" || "$KNOW_ID" == "null" ]]; then
   echo "❌ Knowledge‑doc creation failed."
   exit 1
fi
echo "✅ Knowledge doc created → knowledge_id=${KNOW_ID}"
