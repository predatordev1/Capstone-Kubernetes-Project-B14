FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN addgroup --system healer && \
    adduser --system --ingroup healer --no-create-home healer

RUN mkdir -p /var/log/healing && \
    chown healer:healer /var/log/healing

USER healer

CMD ["python", "main.py"]
