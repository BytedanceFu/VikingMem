#!/usr/bin/env python3
import asyncio
import csv
import json
import os
import sys
from typing import List, Dict
from dotenv import load_dotenv
from volcenginesdkarkruntime import AsyncArk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_utils.response_judge import locomo_response_timeline, locomo_eval_doubao
from search_memory import search_all_memories, load_queries

load_dotenv()


async def evaluate_single_query(
    doubao_client: AsyncArk,
    query_data: Dict,
    group_id: str = 'locomo_test_01',
    semaphore: asyncio.Semaphore = None
) -> Dict:
    async def _evaluate():
        query = query_data['query']
        gold_answer = query_data['answer']
        user_ids = query_data['query_user'].split(',')
        
        memories_result = search_all_memories(query, user_ids, group_id)
        
        event_memories = memories_result['event_memories']
        user_profiles = memories_result['user_profiles']
        timeline_memories = memories_result['timeline_memories']
        
        user_profile_str = json.dumps(user_profiles, ensure_ascii=False)
        timeline_str = "\n\n".join(timeline_memories)
        
        response = await locomo_response_timeline(
            llm_client=doubao_client,
            memories=event_memories,
            user_profile=user_profile_str,
            question=query,
            timeline_memory_str=timeline_str
        )
        
        is_correct = await locomo_eval_doubao(
            doubao_client=doubao_client,
            question=query,
            gold_answer=gold_answer,
            response=response
        )
        
        return {
            'query_index': query_data['query_index'],
            'query': query,
            'gold_answer': gold_answer,
            'response': response,
            'is_correct': is_correct
        }
    
    if semaphore:
        async with semaphore:
            return await _evaluate()
    else:
        return await _evaluate()


async def evaluate_all_queries(
    csv_path: str = 'data/query.csv',
    group_id: str = 'locomo_test_01',
    start: int = 1,
    end: int = None,
    output_path: str = 'data/eval_results.json',
    workers: int = 4
):
    doubao_client = AsyncArk(api_key=os.getenv("ARK_API_KEY"))
    semaphore = asyncio.Semaphore(workers)
    
    existing_results = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                for item in data:
                    existing_results[item['query_index']] = item
                print(f"Loaded {len(existing_results)} existing results from {output_path}")
            except:
                pass
    
    queries = load_queries(csv_path)
    
    if end is not None:
        queries = queries[start-1:end]
    else:
        queries = queries[start-1:]
    
    results = []
    pending_queries = []
    
    for i, q in enumerate(queries):
        if q['query_index'] in existing_results:
            print(f"Skipping query {q['query_index']} (already evaluated)")
            results.append(existing_results[q['query_index']])
        else:
            pending_queries.append(q)
    
    print(f"Pending queries to evaluate: {len(pending_queries)}")
    
    tasks = [
        evaluate_single_query(doubao_client, q, group_id, semaphore)
        for q in pending_queries
    ]
    
    completed_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(completed_results):
        q = pending_queries[i]
        if isinstance(result, Exception):
            print(f"Error in query {q['query_index']}: {result}")
            results.append({
                'query_index': q['query_index'],
                'query': q['query'],
                'gold_answer': q['answer'],
                'response': '',
                'is_correct': False,
                'error': str(result)
            })
        else:
            results.append(result)
        
        if (i + 1) % 50 == 0 or (i + 1) == len(pending_queries):
            print(f"Progress: {i + 1}/{len(pending_queries)} completed")
            save_results(results, output_path)
    
    correct_count = sum(1 for r in results if r.get('is_correct', False))
    total_count = len(results)
    
    print("\n" + "=" * 50)
    print(f"Evaluation Summary")
    print("=" * 50)
    print(f"Total queries: {total_count}")
    print(f"Correct: {correct_count}")
    print(f"Wrong: {total_count - correct_count}")
    print(f"Accuracy: {correct_count / total_count * 100:.2f}%")
    
    return results


def save_results(results: List[Dict], output_path: str = 'data/eval_results.json'):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Locomo dataset with memory retrieval')
    parser.add_argument('--csv', default='data/query.csv', help='Path to query CSV file')
    parser.add_argument('--group', default='locomo_test_01', help='Group ID for memory search')
    parser.add_argument('--start', type=int, default=1, help='Start index (1-based)')
    parser.add_argument('--end', type=int, default=None, help='End index (inclusive)')
    parser.add_argument('--output', default='data/eval_results.json', help='Output results file')
    parser.add_argument('--workers', type=int, default=4, help='Number of concurrent queries')
    
    args = parser.parse_args()
    
    results = asyncio.run(evaluate_all_queries(
        csv_path=args.csv,
        group_id=args.group,
        start=args.start,
        end=args.end,
        output_path=args.output,
        workers=args.workers
    ))
    
    save_results(results, args.output)
