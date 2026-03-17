#!/usr/bin/env python3
import json
import os
import ast
import requests
from dotenv import load_dotenv

load_dotenv()

AK = os.getenv('AAKK')
SK = os.getenv('SSKK')
Domain = "api-knowledgebase.mlp.cn-beijing.volces.com"


def load_schema(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        try:
            return ast.literal_eval(content)
        except:
            return json.loads(content)


def create_memory_collection():
    event_schema = load_schema('event_type/sys_event_v2.py')
    profile_schema = load_schema('profile_type/memory_summary_entity.py')

    path = '/api/memory/collection/create'
    payload = {
        'CollectionName': "locomo_collection",
        'Description': "Locomo dataset memory collection",
        'BuiltinProfileTypes': ["sys_profile_v1"],
        'CustomEventTypeSchemas': [event_schema],
        'CustomProfileTypeSchemas': [profile_schema],
    }

    url = f"https://{Domain}{path}"
    
    headers = {
        'Content-Type': 'application/json',
    }

    try:
        from volcengine.base.Request import Request
        from volcengine.Credentials import Credentials
        from volcengine.auth.SignerV4 import SignerV4

        r = Request()
        r.set_shema("https")
        r.set_method("POST")
        r.set_host(Domain)
        r.set_path(path)
        r.set_body(json.dumps(payload))
        
        credentials = Credentials(AK, SK, 'air', 'cn-north-1')
        SignerV4.sign(r, credentials)
        
        rsp = requests.request(
            method=r.method,
            url=f"{r.schema}://{r.host}{r.path}",
            headers=r.headers,
            data=r.body,
        )
    except ImportError:
        print("Warning: volcengine library not found. Falling back to basic request.")
        print("Note: This may not work correctly without proper authentication.")
        rsp = requests.post(url, json=payload, headers=headers)

    print(f"Status Code: {rsp.status_code}")
    print(f"Response: {rsp.json()}")
    
    return rsp


if __name__ == '__main__':
    create_memory_collection()
