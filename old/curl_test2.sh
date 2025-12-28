BASE="http://du-webui"   # e.g. http://localhost:8080
TOKEN="sk-9f3d08b64518474fb8219de725e8efd6"

echo $BASE
echo $TOKEN
# 1️⃣  OPTIONS – does the server claim POST is allowed?
curl -v -i -X OPTIONS "$BASE/api/v1/files" \
     -H "Authorization: Bearer $TOKEN", -H "Accept: application/json"

# 2️⃣  Minimal POST – no file, just the multipart headers (helps see a clearer error)
curl -v -i "$BASE/api/v1/files" \
     -H "Authorization: Bearer $TOKEN" , -H "Accept: application/json" \
     -F "file=@/dev/null;filename=dummy.pdf"

# 3️⃣  Full POST – the same request the script makes (replace the path with a real file)
curl -v -i "$BASE/api/v1/files" \
     -H "Authorization: Bearer $TOKEN", -H "Accept: application/json" \
     -F "file=@pdf/Contract.pdf"
