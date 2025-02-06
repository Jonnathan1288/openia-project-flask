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

app = FastAPI(servers=[{"url": "https://6a2e-190-110-216-245.ngrok-free.app"}])

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
    """
    Dado una pregunta del usuario y la respuesta SQL de la base de datos, genera una respuesta en HTML bien estructurada y visualmente atractiva.
    La respuesta debe estar estilizada con elementos HTML para mejorar la legibilidad y solo incluir registros activos.
    """

    active_results = [item for item in result if item.get("active")]

    system_message = f"""
    Basado en la siguiente respuesta de la base de datos y la consulta del usuario, genera una respuesta en HTML visualmente atractiva y clara.
    - Formatea la respuesta usando `<div>` para secciones, `<h2>` para títulos y `<p>` para descripciones.
    - Si la consulta involucra productos o servicios, usa `<ul>` o `<ol>` con un estilo atractivo.
    - Aplica estilos CSS para mejorar la presentación.
    - Usa iconos (✅, 💰, 📞, ⭐) para mejorar la experiencia visual.
    - Incluye un encabezado llamativo con fondo destacado.
    - Presenta la información en una lista elegante con separación clara entre elementos.
    - Finaliza con un mensaje amigable y una llamada a la acción, como "📞 Contáctanos para más información o asesoría personalizada".
    <user_question>{human_query}</user_question>
    <sql_response>{active_results}</sql_response>
    Genera una estructura HTML válida en una sola línea sin saltos de línea ni espacios innecesarios, asegurando que luzca profesional y sea fácil de visualizar.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
        ],
    )

    return response.choices[0].message.content.replace("\n", "").replace("  ", "").replace("> <", "><").replace("\t", "").replace("{\"html\":\"", "").rstrip("\"}")


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
