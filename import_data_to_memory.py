#!/usr/bin/env python3
import json
import csv
import os
import time
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MEMORY_API_KEY')
Domain = "api-knowledgebase.mlp.cn-beijing.volces.com"
DEFAULT_SLEEP_MS = 100


def import_session_to_memory(collection_name, group_id, messages):
    url = f"https://{Domain}/api/memory/session/add"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    unique_speakers = []
    seen = set()
    for msg in messages:
        rid = msg["role_id"]
        if rid not in seen:
            unique_speakers.append(msg)
            seen.add(rid)
        if len(unique_speakers) == 2:
            break
    
    default_user_id = unique_speakers[0]['role_id'] if len(unique_speakers) > 0 else ""
    default_user_name = unique_speakers[0]['role_name'] if len(unique_speakers) > 0 else ""
    default_assistant_id = unique_speakers[1]['role_id'] if len(unique_speakers) > 1 else ""
    default_assistant_name = unique_speakers[1]['role_name'] if len(unique_speakers) > 1 else ""
    time_ts = messages[0]['time'] if len(messages) > 0 else 0

    # print(f"Default User: {default_user_id} ({default_user_name})")
    # print(f"Default Assistant: {default_assistant_id} ({default_assistant_name})")
    # print(f"Time: {time_ts}")
    # print(f"Messages: {messages}")
    # print(f"group_id: {group_id}", type(group_id))
    
    data = {
        "collection_name": collection_name,
        "messages": messages,
        "metadata": {
            "group_id": group_id,
            "default_user_id": default_user_id,
            "default_user_name": default_user_name,
            "default_assistant_id": default_assistant_id,
            "default_assistant_name": default_assistant_name,
            "time": time_ts
        }
    }
    
    time.sleep(DEFAULT_SLEEP_MS / 1000)
    response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))
    return response


def import_csv_to_memory(csv_path, collection_name, group_id, start, end, workers):
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        futures = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for i, row in enumerate(reader, start=1):
                if i < start:
                    continue
                if end is not None and i > end:
                    break
                messages = json.loads(row['messages'])
                futures[executor.submit(import_session_to_memory, collection_name, group_id, messages)] = i

            for future in as_completed(futures):
                i = futures[future]
                try:
                    response = future.result()
                    print(f"Imported row {i}")
                    print(f"Status Code: {response.status_code}")
                    print(f"Response: {response.text}")
                except Exception as e:
                    print(f"Imported row {i}")
                    print(f"Error: {e}")
                print("-" * 50)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='data/output_test.csv')
    parser.add_argument('--collection', default='locomo_collection')
    parser.add_argument('--group', default='locomo_test_01')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=None)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()

    if args.start < 1:
        raise ValueError('start must be >= 1')
    if args.end is not None and args.end < args.start:
        raise ValueError('end must be >= start')
    if args.workers < 1:
        raise ValueError('workers must be >= 1')

    import_csv_to_memory(
        csv_path=args.csv,
        collection_name=args.collection,
        group_id=args.group,
        start=args.start,
        end=args.end,
        workers=args.workers
    )
