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

import database, smtp

from models.email import Email


load_dotenv(find_dotenv()) 
# load_dotenv()

logger = logging.getLogger(__name__)

# app = FastAPI(servers=[{"url": "http://134.122.114.162:8000"}])
app = FastAPI()

openai.api_key = os.environ["OPEN_AI_API_KEY"]

async def human_query_to_sql(human_query: str):
    """
    Identifica si la consulta del usuario es un saludo o pregunta general.
    Si no es una consulta SQL válida, responde con HTML.
    Si es una consulta SQL, la devuelve en JSON.
    """
    
    # Get schema
    database_schema = database.get_schema()

    classify_prompt = """
    Eres un asistente que clasifica consultas del usuario en dos categorías:
    - Si la consulta es un saludo o despedida (por ejemplo, "Hola", "Adiós", "Nos vemos", "Buenos días", "Buenas tardes"), responde **exactamente** con "NO".
    - Para cualquier otra consulta, responde **exactamente** con "YES".

    Solo responde con "YES" o "NO", sin texto adicional.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": classify_prompt},
            {"role": "user", "content": human_query},
        ],
        max_tokens=5,
    )

    classification = response.choices[0].message.content.strip().upper()

    print(f" GPT: {classification}") 

    if classification == "NO":
        chat_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Responde de manera amigable al usuario."},
                {"role": "user", "content": human_query},
            ],
        )

        message = chat_response.choices[0].message.content

        response_html = f"""
        <html>
        <head>
            <style>
                h2 {{ color: #0c5460; }}
                p {{ color: #0c5460; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🤖 Motobot</h2>
                <p>{message}</p>
            </div>
        </body>
        </html>
        """

        return (True, response_html); 

    # Generate the SQL query
    system_message = f"""
    Dado el siguiente esquema de base de datos, genera una consulta SQL precisa y optimizada que recupere la información solicitada.

    **Reglas para generar una consulta SQL eficiente:**
    - Usa **LIKE** o **UPPER** para búsquedas que no diferencien entre mayúsculas y minúsculas en campos de texto.
    - Usa **to_tsvector** para búsquedas de texto completo en descripciones o campos largos.
    - Usa **LIKE '%X%'** si el usuario busca palabras clave sin requerir coincidencia exacta.
    - Usa **BETWEEN** en lugar de `>=` y `<=` cuando se filtren fechas o rangos numéricos.
    - Evita el uso de `=` a menos que el usuario haya solicitado una coincidencia exacta.
    - Combina **AND/OR** de manera lógica si hay múltiples filtros en la consulta.
    - Si en el esquema existe un campo `active`, asegúrate de incluir `WHERE active = TRUE`.

    **Ejemplo de respuesta JSON esperada:**
    <example>{{
        "sql_query": "SELECT * FROM productos WHERE nombre LIKE '%camiseta%' AND active = TRUE;",
        "original_query": "Muéstrame productos que contengan 'camiseta'"
    }}</example>
    **Esquema de la base de datos:**
    <schema>
    {database_schema}
    </schema>
    """


    print('---------------------USER MESSAGE---------------------')
    print(human_query)
    print('---------------------END MESSAGE---------------------')

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": human_query},
        ],
    )

    print('API RESPONSE GPT-> ' + response.choices[0].message.content)

    return (False, response.choices[0].message.content)

async def build_answer(result: list[dict[str, Any]], human_query: str) -> str:
    """
    Genera una respuesta en HTML bien estructurada basada en la consulta del usuario y los datos obtenidos de la base de datos.
    """

    columns = list(result[0].keys())

    system_message = f"""
    Eres un asistente que genera respuestas en HTML bien estructurado basado en la información obtenida de la base de datos.

    **Reglas**:
    - Analiza automáticamente las columnas de la base de datos y organiza la información sin tablas ni tarjetas.
    - Presenta la información de manera fluida usando `<h2>`, `<h3>`, `<p>`, `<ul>`, y `<ol>`.
    - Si los datos contienen nombres (`name`, `title`, `brand`), muéstralos con `<h3>`.
    - Si los datos contienen descripciones (`description`, `info`, etc.), inclúyelos en `<p>`.
    - Si los datos contienen imágenes (`image_url`, `photo`, etc.), inclúyelas en `<img>` con un diseño elegante.
    - Si los datos contienen fechas (`date`, `created_at`, etc.), preséntalas en un formato claro dentro de `<p>`.
    - Si hay información financiera (`price`, `cost`, `amount`, etc.), preséntala de forma elegante con `$`.
    - Si alguna columna tiene una lista de elementos trata de resaltar con más información.
    - Si alguna columna tiene una lista de elementos trata de resaltar con más información.
    - No muestres códigos como activo, id, fecha de creación, fecha de actualización.
    - No muestres códigos como activo, id, fecha de creación, fecha de actualización.
    - Si tiene nivel agrega estilos para marcar el inconveniente.
    - Todas las respuestas deben ser en español.

        
    **Ejemplo de salida esperada cuando hay productos:**
    ```html
    <html>
        <head>
            <style>
                h2 {{ color: #0c5460; }}
                p {{ color: #0c5460; font-size: 18px; }}
            </style>
        </head>
        <body>
            <h2>🤖 Motobot</h2>
            <div style="padding:20px; background-color:#f9f9f9;">
            
                <h2>Agrega titulo bonito con información de tu parte agregando </h2>
                <h3>Da una descripción bonita</h3>
                <p>Aceite sintético para motos. 💰 Precio: $25.00</p>
                <img src="https://example.com/aceite.jpg" alt="Aceite Premium" style="max-width:200px; border-radius:10px;">
                <h2>Agrega recomendaciones de uso, etc.  </h2>
                <p style="text-align: center; color: #666;">📞 Contáctanos para más información.</p>
            </div>
        </body>
    </html>
    ```

    🔹 **IMPORTANTE**:
    - No devuelvas JSON ni otros formatos, **solo HTML válido y estructurado dinámicamente**.
    - Usa estilos CSS mínimos para mejorar la presentación sin sobrecargar la respuesta.

    <user_question>{human_query}</user_question>
    <sql_response>{result}</sql_response>
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_message}],
    )

    return response.choices[0].message.content.strip()


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

    try :
        is_invalid, sql_query = await human_query_to_sql(payload.human_query)

        if (is_invalid):
            return HTMLResponse(content=sql_query)

        if not sql_query:
            return HTMLResponse(content=error_html)

        print('-----------------------------sql response ------------------------');    
        print(sql_query);    
        print('-----------------------------sql response ------------------------');    
        result_dict = json.loads(sql_query)

        result = await database.query(result_dict["sql_query"])


        print('-----------------------------SQL ROW ------------------------');    
        print(result);    
        print('-----------------------------SQL ROW ------------------------');  

        answer = await build_answer(result, payload.human_query)
        if not answer:
            return HTMLResponse(content=error_html)

        return HTMLResponse(content=answer)

    except Exception as e:
        return HTMLResponse(content=error_html)    


class EmailRequest(BaseModel):
    mensaje: str 
    subject: str 
    to: str

@app.post(
    "/api/v1/send-email",
    name="Send Email",
    operation_id="post_send_email",
    description="Send Email"
)
def send_email_endpoint(
    email_request: EmailRequest
):
    print('-----------------------------------------------------------')
    print(email_request)
    email = Email(
        mensaje=email_request.mensaje,
        subject=email_request.subject,
        to=email_request.to
    )

    if smtp.send_email(email):
        return {"status": "success", "message": "Correo enviado correctamente"}
    else:
        return {"status": "success", "message": "Correo enviado correctamente"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
