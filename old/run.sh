#!/bin/bash
source .env
python3 upload_pdfs_to_openwebui_v3.py \
    -e 'msonstein@doyonutilities.com' \
    -p '!!BCohm211bcohm2' \
    --pdfs '/home/marks/docling/pdf/Contract.pdf' \
    --url 'http://du-webui' \
    --token 'sk-f1287dd823de48719bbd29df55d0c5d3' \
    -k 'b9805f64-1f9a-4146-af55-a488c89563dd'

#    --pdfs '/home/marks/docling/pdf'

#    --list   


#    --email 'msonstein@doyonutilities.com' \
#    --pwd '!!BCohm211bcohm2' \
#    --token 'sk-f1287dd823de48719bbd29df55d0c5d3' \
#    --knowledge-id '092f9730-5aa0-48d1-90eb-8b85fc81537a' \
