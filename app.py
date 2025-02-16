import json
import logging
import os
from typing import Any

import openai
# from dotenv import load_dotenv
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from flask import Flask, jsonify
from openai import BaseModel

import database

load_dotenv(find_dotenv()) 
# load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(servers=[{"url": "http://134.122.114.162:8000"}])

openai.api_key = os.environ["OPEN_AI_API_KEY"]

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

# async def build_answer(result: list[dict[str, Any]], human_query: str) -> str | None:
#     """
#     Dado una pregunta del usuario y la respuesta SQL de la base de datos, genera una respuesta en HTML bien estructurada y visualmente atractiva.
#     La respuesta debe estar estilizada con elementos HTML para mejorar la legibilidad y solo incluir registros activos.
#     """

#     active_results = [item for item in result if item.get("active")]

#     system_message = f"""
#     Basado en la siguiente respuesta de la base de datos y la consulta del usuario, genera una respuesta en HTML visualmente atractiva y clara.
#     - Formatea la respuesta usando `<div>` para secciones, `<h2>` para títulos y `<p>` para descripciones.
#     - Si la consulta involucra productos o servicios, usa `<ul>` o `<ol>` con un estilo atractivo.
#     - Aplica estilos CSS para mejorar la presentación.
#     - Usa iconos (✅, 💰, 📞, ⭐) para mejorar la experiencia visual.
#     - Incluye un encabezado llamativo con fondo destacado.
#     - Presenta la información en una lista elegante con separación clara entre elementos.
#     - Finaliza con un mensaje amigable y una llamada a la acción, como "📞 Contáctanos para más información o asesoría personalizada".
#     <user_question>{human_query}</user_question>
#     <sql_response>{active_results}</sql_response>
#     Genera una estructura HTML válida en una sola línea sin saltos de línea ni espacios innecesarios, asegurando que luzca profesional y sea fácil de visualizar.
#     """

#     response = openai.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": system_message},
#         ],
#     )

#     return response.choices[0].message.content.replace("\n", "").replace("  ", "").replace("> <", "><").replace("\t", "").replace("{\"html\":\"", "").rstrip("\"}")

import html
from typing import Any

import openai

# async def build_answer(result: list[dict[str, Any]], human_query: str) -> str:
#     """
#     Genera una respuesta en HTML bien estructurada y visualmente atractiva basada en la consulta del usuario y los datos de la base de datos.
#     """

#     active_results = [item for item in result if item.get("active")]

#     system_message = f"""
#     Genera una respuesta **solo en HTML puro**, sin JSON, sin etiquetas innecesarias.  
#     Formatea la respuesta de manera visualmente atractiva, usando:
#     - `<div>` para secciones
#     - `<h2>` para títulos, `<p>` para descripciones
#     - `<ul>` o `<ol>` para listas de productos/servicios.
#     - Usa `<img>` con `src="..."` sin caracteres escapados.

#     🔹 **Ejemplo de salida esperada (debes seguir este formato y solo devolver HTML)**:
#     ```html
#     <div style="background-color: #f0f0f0; padding: 20px;">
#         <h2 style="text-align: center; color: #333;">Nuestros Servicios</h2>
#         <ul style="list-style-type: none; padding: 0;">
#             <li>
#                 <h3>CAMBIO DE ACEITE Y FILTROS</h3>
#                 <p>Sustitución del aceite del motor y cambio de filtros.</p>
#                 <p>💰 Precio: $100</p>
#                 <img src="https://example.com/image.jpg" alt="Cambio de Aceite" style="max-width: 200px;">
#             </li>
#         </ul>
#         <p style="text-align: center; color: #666;">📞 Contáctanos para más información.</p>
#     </div>
#     ```
#     🔹 **Tu respuesta debe seguir este formato exacto. No devuelvas JSON ni caracteres escapados.**
    
#     <user_question>{human_query}</user_question>
#     <sql_response>{active_results}</sql_response>
#     """

#     response = openai.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[{"role": "system", "content": system_message}],
#     )

#     print(response.choices[0].message.content)
 
#     return response.choices[0].message.content


async def build_answer(result: list[dict[str, Any]], human_query: str) -> str:
    """
    Genera una respuesta en HTML bien estructurada basada en la consulta del usuario y los datos de la base de datos.
    """

    active_results = [item for item in result if item.get("active")]

    system_message = f"""
    Genera una respuesta **solo en HTML puro**, sin JSON, sin etiquetas innecesarias.  
    Formatea la respuesta de manera visualmente atractiva, usando:
    - `<div>` para secciones
    - `<h2>` para títulos, `<p>` para descripciones
    - `<ul>` o `<ol>` para listas de productos/servicios.
    - Usa `<img>` con `src="..."` sin caracteres escapados.

    **Ejemplo de salida esperada (solo HTML, sin JSON ni comillas escapadas):**
    ```html
    <div style="background-color: #f0f0f0; padding: 20px;">
        <h2 style="text-align: center; color: #333;">Nuestros Servicios</h2>
        <ul style="list-style-type: none; padding: 0;">
            <li>
                <h3>CAMBIO DE ACEITE Y FILTROS</h3>
                <p>Sustitución del aceite del motor y cambio de filtros.</p>
                <p>💰 Precio: $100</p>
                <img src="https://example.com/image.jpg" alt="Cambio de Aceite" style="max-width: 200px;">
            </li>
        </ul>
        <p style="text-align: center; color: #666;">📞 Contáctanos para más información.</p>
    </div>
    ```
    **No devuelvas JSON ni datos adicionales, solo HTML limpio.**
    
    <user_question>{human_query}</user_question>
    <sql_response>{active_results}</sql_response>
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_message}],
    )

    # 🔹 SOLO IMPRIMIR PARA VERIFICACIÓN
    # print(response.choices[0].message.content)  

    # 🔹 DEVOLVER DIRECTAMENTE SIN MODIFICAR
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
        return {"statusCode": 400, "data": answer}

    return {"statusCode": 200, "data": answer_clean}

@app.post(
    "/api/v1/user-query-html",
    name="User  Query",
    operation_id="post_human_query",
    description="Gets a natural language query, internally transforms it to a SQL query, queries the database, and returns the result.",
)
async def human_query(payload: PostHumanQueryPayload):
    error_html = """
        <html>
        <head>
            <title>Error al Procesar</title>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f8d7da; text-align: center; padding: 50px; }
                .container { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px #ccc; display: inline-block; }
                h2 { color: #721c24; }
                p { color: #721c24; font-size: 18px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>❌ Error al Procesar la Información</h2>
                <p>Lo sentimos, hubo un problema al procesar la solicitud.</p>
                <p>Inténtalo nuevamente más tarde.</p>
            </div>
        </body>
        </html>
        """

    sql_query = await human_query_to_sql(payload.human_query)

    if not sql_query:
        return HTMLResponse(content=error_html)

    print('-----------------------------sql response ------------------------');    
    print(sql_query);    
    print('-----------------------------sql response ------------------------');    
    result_dict = json.loads(sql_query)

    result = await database.query(result_dict["sql_query"])

    answer = await build_answer(result, payload.human_query)
    if not answer:
        
        return HTMLResponse(content=error_html)

    return HTMLResponse(content=answer)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
