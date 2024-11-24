FROM python:3.11-slim

# Instalacija neophodnih paketa i Microsoft ODBC drajvera
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    libodbc1 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Postavljanje radne fascikle
WORKDIR /app

# Kopiranje requirements.txt
COPY requirements.txt /app

# Instalacija zavisnosti
RUN pip install --no-cache-dir -r requirements.txt

# Instalacija eventlet-a (ako već nije u requirements.txt)
RUN pip install eventlet

# Kopiranje ostatka aplikacije
COPY . /app

# Pokretanje aplikacije koristeći eventlet kao radni režim
CMD ["gunicorn", "-k", "eventlet", "--worker-connections", "1000", "app:app"]