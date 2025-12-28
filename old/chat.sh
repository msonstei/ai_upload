echo "${OPEN_KEY}"
curl -v -X POST http://du-webui/api/chat/completions \
  -H "Authorization: Bearer ${OPEN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:120b",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'

