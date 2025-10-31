# Usamos Python 3.12 estable
FROM python:3.12-slim

# Establecemos directorio de trabajo
WORKDIR /app

# Copiamos todo el código
COPY . /app

# Instalamos dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Start command del bot
CMD ["python", "src/samuelitofutbot2.py"]
