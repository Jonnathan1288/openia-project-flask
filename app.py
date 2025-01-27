import json
import logging
import os
from typing import Any

import openai
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import BaseModel

import database

load_dotenv()

logger = logging.getLogger(__name__)

BACKEND_SERVER = os.getenv("SERVER_URL")

app = FastAPI(servers=[{"url": "https://c4cd-45-164-64-132.ngrok-free.app"}])

print('----------------------------------------------------');
print(BACKEND_SERVER)
print('----------------------------------------------------');
openai.api_key = "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"
#openai.api_key = os.getenv(BACKEND_SERVER)

async def human_query_to_sql(human_query: str):

    # We get the database schema
    database_schema = database.get_schema()

    system_message = f"""
    Given the following schema, write a SQL query that retrieves the requested information. 
    Return the SQL query inside a JSON structure with the key "sql_query".
    <example>{{
        "sql_query": "SELECT * FROM services WHERE active;"
        "original_query": "Show me all the services available."
    }}
    </example>
    <schema>
    {database_schema}
    </schema>
    """
    user_message = human_query

    # We send the complete scheme with the query to the LLM
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content


async def build_answer(result: list[dict[str, Any]], human_query: str) -> str | None:

    system_message = f"""
    Given a users question and the SQL rows response from the database from which the user wants to get the answer,
    write a response to the user's question.
    <user_question> 
    {human_query}
    </user_question>
    <sql_response>
    ${result} 
    </sql_response>
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
        ],
    )

    return response.choices[0].message.content


class PostHumanQueryPayload(BaseModel):
    human_query: str


class PostHumanQueryResponse(BaseModel):
    result: list

@app.post(
    "/api/v1/user-query",
    name="User  Query",
    operation_id="post_human_query",
    description="Gets a natural language query, internally transforms it to a SQL query, queries the database, and returns the result.",
)
async def human_query(payload: PostHumanQueryPayload):

    # Transforms the question into a SQL statement
    sql_query = await human_query_to_sql(payload.human_query)

    if not sql_query:
        return {"err": "SQL query generation failed"}

    print('-----------------------------sql response ------------------------');    
    print(sql_query);    
    print('-----------------------------sql response ------------------------');    
    result_dict = json.loads(sql_query)

    # Makes the query to the database
    result = await database.query(result_dict["sql_query"])

    # Transforms the SQL response into a more human format
    answer = await build_answer(result, payload.human_query)
    if not answer:
        return {"err": "Response generation failed"}

    return {"statusCode": 200, "data": answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
