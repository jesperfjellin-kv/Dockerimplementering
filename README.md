# Dockerimplementering

Forslag til hvordan Docker kan implementeres i FKB-miljøet. run_docker.py er en standardisert Docker launcher som starter Docker containere fra lokale .TAR-filer. Skriptet er avhengig av at Dockerfilen i TAR-filen har to 'ekstra' variabler: 'Labels' som beskriver sysargs som skal sendes inn i containeren, og 'Env' som beskriver mappestrukturen inni containeren ved hjelp av CONTAINER_DIR. Eks:

"Labels": {
                "required_args": "FKB_Area,Sti_til_SOSI-filer"
            }


"Env": [
                  "CONTAINER_DIR=/app/sos_files"
            ]

Hvis python-skriptet i containeren ikke trenger sysargs, sjekker ikke run_docker.py 'Labels'. 

Eksempel på god Dockerfile mal:

```Dockerfile

# Bruk ønsket versjon av Python. 3.12 er betydelig raskere enn tidligere utgaver.
FROM python:3.12

# Sett working directory inni containeren
WORKDIR /app

# Legg til LABEL for sysargs
LABEL required_args="FKB_Area,Sti_til_SOSI-filer"

# Sett ENV variabel for struktur i containeren
ENV CONTAINER_DIR="/app/sos_files"

# Kopierer requirements.txt inn i containeren
COPY requirements.txt .

# Oppgrader pip og installer dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Kopier resten av filene inn i containeren
COPY . .

# Starter Python-skriptet i containeren og tar imot sysargs
CMD ["python", "stikkproveomrade.py"]```

