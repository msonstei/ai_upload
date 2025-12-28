BASE="http://du-webui"   # e.g. http://localhost:8080
TOKEN="${OPEN_API}"

# 1️⃣  OPTIONS – does the server claim POST is allowed?
curl -v -i -X OPTIONS "$BASE/api/v1/files" \
     -H "Authorization: Bearer $TOKEN"
echo 
# 2️⃣  Minimal POST – no file, just the multipart headers (helps see a clearer error)
curl -i -X POST "$BASE/api/files" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/dev/null;filename=dummy.pdf"
echo 
# 3️⃣  Full POST – the same request the script makes (replace the path with a real file)
curl -i -X POST "$BASE/api/files" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@$(pwd)/pdf/Contract.pdf"
echo 
echo 
echo 
BASE="http://du-webui"   # e.g. http://localhost:8080
TOKEN="${OPEN_KEY}"

# 1️⃣  OPTIONS – does the server claim POST is allowed?
curl -v -i -X OPTIONS "$BASE/api/v1/files" \
     -H "Authorization: Bearer $TOKEN"
echo 
# 2️⃣  Minimal POST – no file, just the multipart headers (helps see a clearer error)
curl -i -X POST "$BASE/api/files" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@/dev/null;filename=dummy.pdf"
echo 
# 3️⃣  Full POST – the same request the script makes (replace the path with a real file)
curl -i -X POST "$BASE/api/files" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@$(pwd)/pdf/Contract.pdf"
echo 
echo 

