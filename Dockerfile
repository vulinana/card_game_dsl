FROM python:3.11-slim

# Instaliraj sistemske pakete
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    libodbc1 \
    && rm -rf /var/lib/apt/lists/*

# Postavi radni direktorijum
WORKDIR /app

# Kopiraj aplikaciju i instaliraj Python zavisnosti
COPY . .
RUN pip install -r requirements.txt

# Pokreni aplikaciju
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]