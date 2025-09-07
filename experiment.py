import os
import requests
import json
from datetime import datetime, timezone, timedelta
import csv
from volcengine.base.Request import Request
from volcengine.Credentials import Credentials
from volcengine.auth.SignerV4 import SignerV4
import pandas as pd
import ast
import openai
from eval import locomo_response, locomo_grader

AK = "your AK" # please see https://www.volcengine.com/docs/84313/1783347 for how to get ak/sk
SK = "your SK"
Domain = "api-knowledgebase.mlp.cn-beijing.volces.com"

client = openai.AsyncAzureOpenAI(
    azure_endpoint="your_url",
    api_key="your_api_key"
)


def get_dataset(url_file_path: str):

    try:
        with open(url_file_path, 'r', encoding='utf-8') as f:
            dataset_url = f.readline().strip()

        if not dataset_url:
            print(f"wrong: {url_file_path} is empty or an invalid url")
            exit()

        if "github.com" in dataset_url and "/blob/" in dataset_url:
            dataset_url = dataset_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    except FileNotFoundError:
        print(f"could not find {url_file_path}")
        exit()

    response = requests.get(dataset_url)
    response.raise_for_status()
    json_content = response.text

    output_filename = dataset_url.split('/')[-1]
    output_json_path = os.path.join(dataset_dir, output_filename)

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

    except IOError as e:
        print(f"save dataset failed {e}")
        exit()


def convert_to_millis(time_str):
    _tz = timezone(timedelta(hours=8))
    format_str = "%I:%M %p on %d %B, %Y"
    local_time = datetime.strptime(time_str, format_str).replace(tzinfo=_tz)
    utc_time = local_time.astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    millis = int((utc_time - epoch).total_seconds() * 1000)

    return millis


def process_json_to_csv(json_file_path: str, csv_file_path: str) -> None:
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        csv_rows = []

        for item in data:
            if not isinstance(item, dict) or 'conversation' not in item:
                continue

            conversation = item['conversation']
            if not isinstance(conversation, dict):
                continue

            sessions = {}
            for key in conversation:
                if key.startswith('session_') and not key.endswith('_date_time'):
                    session_num = key.split('_')[1]
                    date_time_key = f"session_{session_num}_date_time"
                    if date_time_key in conversation:
                        sessions[key] = conversation[date_time_key]

            for session_key, session_date_time in sessions.items():
                session_data = conversation.get(session_key, [])
                if not isinstance(session_data, list):
                    continue

                formatted_dialogues = []
                for dialogue in session_data:
                    if not isinstance(dialogue, dict) or 'speaker' not in dialogue or 'text' not in dialogue:
                        continue

                    speaker = dialogue['speaker']
                    text = dialogue['text']
                    blip_caption = dialogue.get('blip_caption')
                    img_description = f'(description of attached image: {blip_caption})' if blip_caption is not None else ''

                    role_name = ""
                    role = ""
                    if speaker:
                        role = "user"
                        role_name = speaker

                    formatted_dialogue = {
                        "role": role,
                        "role_name": role_name,
                        "content": text + img_description
                    }
                    formatted_dialogues.append(formatted_dialogue)

                dialogues_per_row = 50
                for i in range(0, len(formatted_dialogues), dialogues_per_row):
                    row = []
                    for j in range(dialogues_per_row):
                        idx = i + j
                        if idx < len(formatted_dialogues):
                            dialogue = formatted_dialogues[idx].copy()
                            dialogue['time'] = convert_to_millis(session_date_time)
                            row.append(dialogue)
                    if row:
                        csv_rows.append(row)

        with open(csv_file_path, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['messages', 'build_index'])
            for idx, row in enumerate(csv_rows):
                writer.writerow([json.dumps(row, ensure_ascii=False), idx])

    except FileNotFoundError:
        print(f"file path {json_file_path} not found")
    except json.JSONDecodeError:
        print("JSON invalid")
    except Exception as e:
        print(f"{str(e)}")


def generate_query_csv(json_file_path: str, csv_file_path: str) -> None:
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        csv_rows = []
        for item in data:
            if not isinstance(item, dict) or 'qa' not in item:
                continue

            qa_list = item['qa']
            conversation = item['conversation']
            speaker_a = conversation.get('speaker_a', '')
            speaker_b = conversation.get('speaker_b', '')
            if not isinstance(qa_list, list):
                continue

            for qa in qa_list:
                if not isinstance(qa, dict):
                    continue
                question = qa.get('question', '')
                answer = qa.get('answer', '')
                category = qa.get('category', '')
                if category == 5 or category == '5':
                    continue

                csv_rows.append({
                    'query': question,
                    'answer': answer,
                    'category': category,
                    'user': speaker_a + ',' + speaker_b
                })

        with open(csv_file_path, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['query_index', 'query', 'answer', 'category', 'query_user'])
            writer.writeheader()
            for idx, row in enumerate(csv_rows, start=1):
                writer.writerow({
                    'query_index': idx,
                    'query': row['query'],
                    'answer': row['answer'],
                    'category': row['category'],
                    'query_user': row['user']
                })

    except Exception as e:
        print(f"{str(e)}")


def prepare_request(method, path, ak, sk, data=None):
  r = Request()
  r.set_shema("http")
  r.set_method(method)
  r.set_host(Domain)
  r.set_path(path)

  if data is not None:
    r.set_body(json.dumps(data))
  credentials = Credentials(ak, sk, 'air', 'cn-north-1')
  SignerV4.sign(r, credentials)
  return r


def internal_request(method, api, payload, params=None):

  req = prepare_request(
                        method = method,
                        path = api,
                        ak = AK,
                        sk = SK,
                        data = payload)

  r = requests.request(method=req.method,
          url="{}://{}{}".format(req.schema, req.host, req.path),
          headers=req.headers,
          data=req.body,
          params=params,
      )
  return r


def create_memory_base(collection_name):
    path = '/api/memory/collection/create'
    playload = {
        'CollectionName': collection_name,
        'Description': "test description",
        'BuiltinEventTypes': ["sys_event_v1", "sys_profile_collect_v1"],
        'BuiltinEntityTypes': ["sys_profile_v1"],
    }
    rsp = internal_request('POST', path, playload)
    print(rsp.json())


def add_memory(messages, session_id, collection_name):
    path = "/api/memory/session/add"
    default_user_id = messages[0]["role_name"]
    default_assistant_id = messages[1]["role_name"]
    playload = {
        "collection_name": collection_name,
        "session_id": session_id,
        "messages": messages,
        "metadata": {
            "default_user_id": default_user_id,
            "default_assistant_id": default_assistant_id,
            "time": messages[0]["time"]
        }
    }
    rsp = internal_request('POST', path, playload)


def search_memory(collection_name, query, query_users):
    path = "/api/memory/search"
    playload = {
        "collection_name": collection_name,
        "query": query,
        "limit": 15,
        "filter": {
            "user_id": query_users,
            "memory_type": ["sys_event_v1"]
        }
    }

    rsp = internal_request('POST', path, playload)
    return rsp.json()["data"].result_list


def search_profile(collection_name, query, query_users):
    path = "/api/memory/search"
    playload = {
        "collection_name": collection_name,
        "query": query,
        "limit": 2,
        "filter": {
            "user_id": query_users,
            "memory_type": ["sys_profile_v1"]
        }
    }

    rsp = internal_request('POST', path, playload)
    return rsp.json()["data"].result_list


async def eval_locomo(query_file_path):
    query_df = pd.read_csv(query_file_path)
    result_dict = {1: [], 2: [], 3: [], 4:[]}
    for index, row in query_df.iterrows():
        query = row["query"]
        query_usr = row["query_user"].split(',')
        answer = row["answer"]
        category = int(row["category"])
        memory_list = search_memory(collection_name, query, query_usr)
        profile = search_profile(collection_name, query, query_usr)
        predict_answer = await locomo_response(client, memory_list, profile, query)
        eval_res = await locomo_grader(client, query, answer, predict_answer)
        result_dict[category].append(eval_res)
    return result_dict


async def main():
    current_dir = "."
    dataset_dir = os.path.join(current_dir, "dataset")
    url_file_path = os.path.join(dataset_dir, "dataset_url.txt")
    get_dataset(url_file_path)
    json_file_path = os.path.join(dataset_dir, "locomo10.json")
    csv_file_path = os.path.join(dataset_dir, "all_data.csv")
    query_file_path = os.path.join(dataset_dir, "query.csv")
    process_json_to_csv(json_file_path, csv_file_path)
    generate_query_csv(json_file_path, query_file_path)
    collection_name = "locomo_eval"
    create_memory_base(collection_name)
    df = pd.read_csv(csv_file_path)
    for index, row in df.iterrows():
        session_id = "session_" + str(row['build_index'])
        messages = ast.literal_eval(row['messages'])
        add_memory(messages, session_id, collection_name)

    eval_res = await eval_locomo(query_file_path)
    print(eval_res)

if __name__ == '__main__':
    main()





