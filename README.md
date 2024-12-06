# Dockerimplementering

Forslag til hvordan Docker kan implementeres i FKB-miljøet. run_docker.py er en standardisert Docker launcher som starter Docker containere fra lokale .TAR-filer. Skriptet er avhengig av at Dockerfilen i TAR-filen har to 'ekstra' variabler: 'Labels' som beskriver sysargs som skal sendes inn i containeren, og 'Env' som beskriver mappestrukturen inni containeren ved hjelp av CONTAINER_DIR. Eks:

"Labels": {
                "required_args": "FKB_Area,Sti_til_SOSI-filer"
            }


"Env": [
                  "CONTAINER_DIR=/app/sos_files"
            ]

Hvis python-skriptet i containeren ikke trenger sysargs, sjekker ikke run_docker.py 'Labels'. 
