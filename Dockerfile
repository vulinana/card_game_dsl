# Koristite Python bazni image
FROM python:3.11-slim

# Ažurirajte sistem i instalirajte potrebne pakete
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

# Postavite radni direktorijum
WORKDIR /app

# Kopirajte zavisnosti
COPY requirements.txt /app

# Instalirajte Python zavisnosti
RUN pip install --no-cache-dir -r requirements.txt

# Kopirajte aplikaciju
COPY . /app

# Pokrenite aplikaciju
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]