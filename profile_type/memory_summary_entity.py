{
    "ProfileType": "memory_summary_entity",
    "Description": """
你的任务是发现新的topic，这些topic要么是：
重要的（例如，marriage, job promotion等），要么是
重复的、周期性的或常规的（例如，going to gym, attending specific events等）。
说明：
（1）你应为发现的每个主题创建一个事件名称。
（2）主题名称应简短明了。最好是一个单词（例如，“marriage”、“hiking”）。名称绝不能超过 3 个单词。
（3）主题名称只能包含字母或空格。不要使用任何其他字符，包括连字符、下划线等。
（4）如果一个事件被认为足够重要（例如，marriage），无论它被提及多少次，你都应该记录下来。
（5）对于内容相近的事件（例如，hiking and backpacking），你可以将它们合并为一个事件，并累加计数。
（6）考虑对话流程，一起讨论的事件可能表明相关的主题或模式。
    """,
    "DescriptionEn":"""
Your task is to discover new topics. These topics are either:
Important (e.g., marriage, job promotion), or
Recurring, periodic, or routine (e.g., going to the gym, attending specific events).
Instructions:
(1) You must create a name for each discovered topic.
(2) The topic name MUST be short and clear. A single word is preferred (e.g., "marriage," "hiking"). The name must never exceed 3 words.
(3) The topic name can ONLY contain letters or spaces. Do not use any other characters, including hyphens, underscores, etc.
(4) If an event is considered sufficiently important (e.g., marriage), you must record it regardless of how many times it is mentioned.
(5) For events with similar content (e.g., hiking and backpacking), you can merge them into a single event and aggregate their counts.
(6) Consider the conversational flow. Events discussed together may indicate related themes or patterns.
""",
    "Properties": [
        {
            "PropertyName": "topic_name",
            "PropertyValueType": "string",
            "Description": '''
            （1）话题名称应简短明了。最好是一个单词（例如，“婚姻”、“徒步旅行”）。名称绝不能超过 2 个单词。
            （2）话题名称只能包含字母或空格。不要使用任何其他字符，包括连字符、下划线等。     
            ''',
            "DescriptionEn": """
            (1) The topic name MUST be short and clear. A single word is preferred (e.g., "marriage," "hiking"). The name must never exceed 2 words.
            (2) The topic name can ONLY contain letters or spaces. Do not use any other characters, including hyphens, underscores, etc.
            """,
            "IsPrimaryKey": True,
        },
        {
            "PropertyName": "event_history",
            "PropertyValueType": "list<string>",
            "Description": "话题下的事件记忆的历史信息",
            "DescriptionEn": "historical information of event memory under the topic",
            "AggregateExpression": {
                "Op":'TIME_COMPRESS',
                "EventType": "sys_event_v2",
                "EventPropertyName": "summary"
            },
        },
    ]
}