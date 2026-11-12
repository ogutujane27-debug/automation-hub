# 1. Tumia Python rasmi ya Linux (Inafaa sana kwa processor ya AMD64)
FROM python:3.11-slim

# 2. Weka folda kuu la kazi ndani ya Linux
WORKDIR /app

# 3. Copy faili la requirements kwanza ili kusakinisha maktaba
COPY requirements.txt /app/

# 4. Sakinisha maktaba zote tulizozitaja kwenye requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy mafaili mengine yote ya mradi wako (ikiwemo tasks.py na app ya Kubo)
COPY . /app/
