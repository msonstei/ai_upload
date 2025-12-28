docker exec -it open-webui /bin/sh   # or /bin/bash if present
# inside the container:
apk add --no-cache curl jq   # (Alpine) – install tools if they are missing
curl -v -X POST http://127.0.0.1:80/api/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username":"msonstein@doyonutilities.com","password":"!!BCohm211bcohm2"}'
