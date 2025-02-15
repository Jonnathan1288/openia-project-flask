# Usa una imagen base de Python (versión 3.12-slim, por ejemplo)
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y establece salida sin búfer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias (ej. para psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia el archivo de requerimientos (requirements.txt) al contenedor
COPY requirements.txt .

# Actualiza pip e instala las dependencias del proyecto
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el resto del código del proyecto al contenedor
COPY . .

COPY .env /app/.env

# Expone el puerto que utilizará la aplicación (por defecto uvicorn escucha en el 8000)
EXPOSE 8000

# Comando para iniciar la aplicación con uvicorn.
# Se asume que tu aplicación principal está en "app.py" y la instancia de FastAPI se llama "app"
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
