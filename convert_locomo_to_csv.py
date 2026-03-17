#!/usr/bin/env python3
import json
import csv
import argparse
import re
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_datetime(date_str: str) -> int:
    """
    Parse datetime string like "1:56 pm on 8 May, 2023" to milliseconds timestamp.
    Assumes UTC+8 timezone (East 8 zone).
    """
    date_str = date_str.strip()
    
    pattern = r'(\d{1,2}):(\d{2})\s*(am|pm)\s+on\s+(\d{1,2})\s+(\w+),?\s+(\d{4})'
    match = re.match(pattern, date_str, re.IGNORECASE)
    
    if not match:
        raise ValueError(f"Cannot parse datetime: {date_str}")
    
    hour = int(match.group(1))
    minute = int(match.group(2))
    am_pm = match.group(3).lower()
    day = int(match.group(4))
    month_str = match.group(5)
    year = int(match.group(6))
    
    if am_pm == 'pm' and hour != 12:
        hour += 12
    elif am_pm == 'am' and hour == 12:
        hour = 0
    
    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    month = month_map.get(month_str)
    if month is None:
        raise ValueError(f"Unknown month: {month_str}")
    
    tz = ZoneInfo("Asia/Shanghai")
    dt = datetime(year, month, day, hour, minute, 0, tzinfo=tz)
    
    timestamp_ms = int(dt.timestamp() * 1000)
    
    return timestamp_ms


def build_content(message: dict) -> str:
    """
    Build content from message.
    If blip_caption exists, append "(description of attached image: blip_caption)".
    """
    text = message.get('text', '')
    blip_caption = message.get('blip_caption')
    
    if blip_caption:
        content = f"{text}(description of attached image: {blip_caption})"
    else:
        content = text
    
    return content


def convert_session_to_messages(session_data: list, timestamp_ms: int) -> list:
    """
    Convert a session's message list to the target format.
    """
    messages = []
    
    for msg in session_data:
        message = {
            'role': 'user',
            'role_name': msg['speaker'],
            'role_id': msg['speaker'],
            'content': build_content(msg),
            'time': timestamp_ms
        }
        messages.append(message)
    
    return messages


def extract_sessions(conversation: dict) -> list:
    """
    Extract all sessions from a conversation dict.
    Returns list of (session_number, session_data, timestamp_ms) tuples.
    """
    sessions = []
    
    session_num = 1
    while True:
        session_key = f'session_{session_num}'
        datetime_key = f'session_{session_num}_date_time'
        
        if session_key not in conversation:
            break
        
        session_data = conversation[session_key]
        date_time_str = conversation.get(datetime_key, '')
        
        if date_time_str:
            timestamp_ms = parse_datetime(date_time_str)
        else:
            timestamp_ms = 0
        
        sessions.append((session_num, session_data, timestamp_ms))
        session_num += 1
    
    return sessions


def convert_locomo_to_csv(input_path: str, output_path: str):
    """
    Main conversion function.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    csv_rows = []
    build_index = 0
    
    for item in data:
        conversation = item.get('conversation', {})
        
        sessions = extract_sessions(conversation)
        
        for session_num, session_data, timestamp_ms in sessions:
            messages = convert_session_to_messages(session_data, timestamp_ms)
            
            if messages:
                csv_rows.append({
                    'messages': json.dumps(messages, ensure_ascii=False),
                    'build_index': build_index
                })
                build_index += 1
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['messages', 'build_index'])
        writer.writeheader()
        writer.writerows(csv_rows)
    
    print(f"Converted {len(csv_rows)} sessions to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Convert Locomo JSON to CSV format')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file path')
    parser.add_argument('--output', '-o', required=True, help='Output CSV file path')
    
    args = parser.parse_args()
    
    convert_locomo_to_csv(args.input, args.output)


if __name__ == '__main__':
    main()
