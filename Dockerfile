FROM python:3.9-alpine

ARG EMAIL
ARG PASS
ARG SECRET

ENV EMAIL=$EMAIL
ENV PASS=$PASS
ENV SECRET=$SECRET

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
