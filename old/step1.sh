USER='msonstein@doyonutilities.com'
PASS='!!BCohm211bcohm2'

# 1️⃣  Verify the correct path is reachable
#curl -i -X OPTIONS http://du-webui/api/files   # you should see "Allow: GET, POST, ..." and a 200 status

curl -X 'POST' \
  'http://du-webui/api/v1/auths/signin' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "msonstein@doyonutilities.com",
  "password": "!!BCohm211bcohm2"
}'

curl -X 'POST' \
  'http://du-webui/api/v1/files/?process=true&process_in_background=true' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@pdf/Contract.pdf;type=application/pdf' \
  -F 'metadata={"additionalProp1":{}}'

# 2️⃣  Get a JWT (if you already have one, skip this step)
#WEBUI_JWT=$(curl -v -X 'POST' 'http://du-webui/api/auths/signin' \ #/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":$USER,"password":$PASS}' | jq -r .access_token)
#echo("$WEBUI_JWT")

# 3️⃣  Try uploading a tiny dummy file (just to prove the endpoint works)
#curl -i -X POST http://du-webui/api/v1/files \
#   -H "Authorization: Bearer $KEY" \
#   -F "file=@/dev/null;filename=dummy.pdf"
