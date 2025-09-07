import asyncio
import openai
from typing import Any, List
from pydantic import BaseModel, Field
import json


class Grade(BaseModel):
    is_correct: str = Field(description='CORRECT or WRONG')
    explanation: str = Field(description='Explain why the answer is correct or incorrect.')


async def locomo_response(llm_client, memories: List[str], user_profile: Any, question: str) -> str:
    system_prompt = """
        You are an intelligent memory assistant tasked with answering questions 
        based on the provided conversation memories and user profile.
        """

    prompt = f"""
    # CONTEXT:
    You have access to memories from a conversation. These memories contain
    timestamped information that may be relevant to answering the question.

    # INSTRUCTIONS:
    1. Carefully analyze all provided memories
    2. Pay special attention to the timestamps to determine the answer
    3. If the question asks about a specific event or fact, look for direct evidence in the memories
    4. If the memories contain contradictory information, prioritize the most recent memory
    5. If there is a question about time references (like "last year", "two months ago", etc.), 
       calculate the actual date based on the memory timestamp. For example, if a memory from 
       4 May 2022 mentions "went to India last year," then the trip occurred in 2021.
    6. Always convert relative time references to specific dates, months, or years. For example, 
       convert "last year" to "2022" or "two months ago" to "March 2023" based on the memory 
       timestamp. Ignore the reference while answering the question
    7. Be as specific as possible when talking about people, places, and events
    8. Focus only on the content of the memories from both speakers. Do not confuse character 
       names mentioned in memories with the actual users who created those memories.

    Clarification:
    When interpreting memories, use the timestamp to determine when the described event happened, not when someone talked about the event.

    Example:

    Memory: (2023-03-15T16:33:00Z) I went to the vet yesterday.
    Question: What day did I go to the vet?
    Correct Answer: March 15, 2023
    Explanation:
    Even though the phrase says "yesterday," the timestamp shows the event was recorded as happening on March 15th. Therefore, the actual vet visit happened on that date, regardless of the word "yesterday" in the text.

    # APPROACH (Think step by step):
    1. First, examine all memories that contain information related to the question
    2. Examine the timestamps and content of these memories carefully
    3. Look for explicit mentions of dates, times, locations, or events that answer the question
    4. If the answer requires calculation (e.g., converting relative time references), show your work
    5. Formulate a precise, concise answer based solely on the evidence in the memories
    6. Double-check that your answer directly addresses the question asked
    7. Ensure your final answer is specific and avoids vague time references

    Memories:

    {memories}

    User profile:

    {user_profile}

    Question: {question}
    Answer:
    """

    response = await llm_client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=4095
    )

    result = response.choices[0].message.content or ''

    return result


async def locomo_grader(llm_client, question: str, gold_answer: str, response: str) -> bool:
    system_prompt = """
        You are an expert grader that determines if answers to questions match a gold standard answer
        """

    ACCURACY_PROMPT = f"""
    Your task is to label an answer to a question as ’CORRECT’ or ’WRONG’. You will be given the following data:
        (1) a question (posed by one user to another user), 
        (2) a ’gold’ (ground truth) answer, 
        (3) a generated answer
    which you will score as CORRECT/WRONG.

    The point of the question is to ask about something one user should know about the other user based on their 
    prior conversations. The gold answer will usually be a concise and short answer that includes the referenced 
    topic, for example: Question: Do you remember what I got the last time I went to Hawaii? Gold answer: A shell 
    necklace The generated answer might be much longer, but you should be generous with your grading - as long as it 
    touches on the same topic as the gold answer, it should be counted as CORRECT.

    # IMPORTANT
    For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might 
    be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous 
    with your grading - as long as it refers to the same date or time period as the gold answer (e.g., "20 May 2023" vs. "The sunday before 25 May 2023"), it should be counted 
    as CORRECT. Even if the format differs (e.g., "May 7th" vs "7 May"),  consider it CORRECT if it's the same date.

    Now it’s time for the real question:
    Question: {question}
    Gold answer: {gold_answer}
    Generated answer: {response}

    First, provide a clear explanation of your reasoning, then finish with CORRECT or WRONG. 
    Do NOT include both CORRECT and WRONG in your response, or it will break the evaluation script.

    Just return the label CORRECT or WRONG in a json format with the key as "label".
    """

    response = await llm_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": ACCURACY_PROMPT}],
        response_format=Grade,
        temperature=0,
        max_tokens=4095
    )
    result = response.choices[0].message.parsed

    return result.is_correct.strip().lower() == 'correct'
