#!/usr/bin/env python3
import json
import csv
import os
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

load_dotenv()

API_KEY = os.getenv('MEMORY_API_KEY')
Domain = "api-knowledgebase.mlp.cn-beijing.volces.com"


class MemoryAPIError(Exception):
    pass


def check_response_code(response_json: Dict) -> Dict:
    code = response_json.get('code', -1)
    if code != 0:
        raise MemoryAPIError(f"API returned non-zero code: {code}, message: {response_json.get('message', '')}")
    return response_json


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(lambda e: isinstance(e, MemoryAPIError))
)
def search_memory(
    collection_name: str,
    query: str,
    user_ids: List[str],
    group_id: str,
    memory_type: List[str],
    limit: int
) -> Dict[str, Any]:
    url = f"https://{Domain}/api/memory/search"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "collection_name": collection_name,
        "query": query,
        "filter": {
            "user_id": user_ids,
            "group_id": group_id,
            "memory_type": memory_type
        },
        "limit": limit
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data, ensure_ascii=False))
    response_json = response.json()
    return check_response_code(response_json)


def extract_event_memories(result_list: List[Dict]) -> List[str]:
    memories = []
    for item in result_list:
        memory_info = item.get('memory_info', {})
        original_messages = memory_info.get('original_messages', '')
        if original_messages:
            memories.append(original_messages)
    return memories


def extract_user_profiles(result_list: List[Dict]) -> Dict[str, str]:
    profiles = {}
    for item in result_list:
        user_id_list = item.get('user_id', [])
        if user_id_list:
            user_id = user_id_list[0]
            memory_info = item.get('memory_info', {})
            user_profile = memory_info.get('user_profile', '')
            if user_profile:
                profiles[user_id] = user_profile
    return profiles


def extract_timeline_memories(result_list: List[Dict]) -> List[str]:
    timeline_strs = []
    for item in result_list:
        memory_info = item.get('memory_info', {})
        event_history = memory_info.get('event_history', [])
        topic_name = memory_info.get('topic_name', '')
        
        if event_history and topic_name:
            events_str = "\n- ".join(event_history)
            timeline_str = f"Topic of this memory: {topic_name}\nEvent history:\n- {events_str}"
            timeline_strs.append(timeline_str)
    return timeline_strs


def search_all_memories(query: str, user_ids: List[str], group_id: str = 'locomo_test_02'):
    event_result = search_memory(
        collection_name='locomo_collection',
        query=query,
        user_ids=user_ids,
        group_id=group_id,
        memory_type=['sys_event_v2'],
        limit=12
    )
    
    profile_result = search_memory(
        collection_name='locomo_collection',
        query=query,
        user_ids=user_ids,
        group_id=group_id,
        memory_type=['sys_profile_v1'],
        limit=1
    )
    
    timeline_result = search_memory(
        collection_name='locomo_collection',
        query=query,
        user_ids=user_ids,
        group_id=group_id,
        memory_type=['memory_summary_entity'],
        limit=5
    )
    
    event_list = event_result.get('data', {}).get('result_list', [])
    profile_list = profile_result.get('data', {}).get('result_list', [])
    timeline_list = timeline_result.get('data', {}).get('result_list', [])
    
    event_memories = extract_event_memories(event_list)
    user_profiles = extract_user_profiles(profile_list)
    timeline_memories = extract_timeline_memories(timeline_list)
    
    return {
        'event_memories': event_memories,
        'user_profiles': user_profiles,
        'timeline_memories': timeline_memories
    }


def load_queries(csv_path: str) -> List[Dict]:
    queries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            queries.append({
                'query_index': row['query_index'],
                'query': row['query'],
                'answer': row['answer'],
                'query_user': row['query_user']
            })
    return queries


if __name__ == '__main__':
    queries = load_queries('data/query.csv')
    
    for q in queries[:3]:
        print(f"\nQuery {q['query_index']}: {q['query']}")
        user_ids = q['query_user'].split(',')
        print(f"User IDs: {user_ids}")
        
        result = search_all_memories(q['query'], user_ids)
        
        print(f"Event memories count: {len(result['event_memories'])}")
        print(f"User profiles: {result['user_profiles']}")
        print(f"Timeline memories count: {len(result['timeline_memories'])}")
        print("-" * 50)
