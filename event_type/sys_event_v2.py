{
    "EventType": "sys_event_v2",
    "Description": """
指导原则：
（1）总结需包含与所涉实体相关的信息记录，注重细节，尤其强调承诺、协议或未来可能被追溯的提议等信息（例如：小明曾询问 “需要我帮你办会员吗？”，小森回复 “以后再说”），不得遗漏。若遇时间表述（如 “昨天”），需根据内容发生时间将日期转换为具体的年月日格式。
（2）尽可能全面地包含所有事实，尤其需记录特定角色提出的请求并标记重大事件。
（3）将对话转换为间接引语，涵盖情绪和说话者特征。
（4）创作连贯叙述，保留关键戏剧元素。
（5）使用第三人称视角。
""",
    "DescriptionEn": """
Guidelines:
(1) The summary should include information records related to the entities involved, pay attention to details, and particularly emphasize information such as commitments, agreements, or proposals that may be traced back in the future (for example: Xiaoming once asked, "Do you need me to get you a membership?" and Xiaosen replied, "Let's talk about it later"), without any omissions. When encountering time expressions (such as "yesterday"), the date should be converted into the specific year - month - day format according to the time of the content occurrence.
(2) Include all facts as comprehensively as possible, especially record the requests made by specific characters and mark significant events.
(3) Convert the conversation into indirect speech, covering emotions and speaker characteristics.
(4) Create a coherent narrative and retain key dramatic elements.
(5) Use the third - person perspective.
""",
    "Properties": [
        {
            "PropertyName": "goal",
            "PropertyValueType": "string",
            "Description": "总结内容主旨",
            "DescriptionEn": "Summarize the purpose of the content in 5 words or less",
        },
        {
            "PropertyName": "summary",
            "PropertyValueType": "string",
            "Description": "基于上述字段内容，编写一段描述以概述完整的事实内容。",
            "DescriptionEn": "Based on the content of the above fields, compile a description to outline the complete Fact content",
        },
        {
            "PropertyName": "questions",
            "PropertyValueType": "list<string>",
            "Description": '''
想象一下，您是一名高风险的商业顾问，您必须提出一个对于对话者人物画像相关的问题来测试读者对对这段话的理解（messages），
以便提供完成数百万美元交易所需的关键信息。
你应该猜测从对话中可以分析出说话者哪方面的用户画像。
请注意，问题应该围绕人物画像，问题的回答不应该是具体的事实，而是围绕“从对话可以看出xxx是一个什么样的人”。
比如：John的收入水平怎么样？  John的政治倾向可能是怎么样的？ Join爱旅行么？ 
快速而切中要害地写出这样的问题将意味着获得可观的奖金。
            ''',
            "DescriptionEn": '''
Imagine you are a high-stakes business consultant who must pose a question about the interlocutor's user profile to test the reader's understanding of the messages, in order to provide critical information needed to close a multi-million dollar deal. 
You should infer which aspect of the speaker's user profile can be analyzed from the conversation. 
Note that the question should focus on the user profile, and the answer to the question should not be specific facts but rather centered around "what kind of person xxx is as seen from the conversation." 
For example: What is John's income level? What might John's political leanings be? Does John love to travel? 
Crafting such a question quickly and to the point could mean earning a substantial bonus.
            '''
        }
    ]
}