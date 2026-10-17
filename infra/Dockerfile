FROM python:3.12-slim

WORKDIR /workspace
COPY services/api/requirements.txt /workspace/services/api/requirements.txt
RUN pip install --no-cache-dir -r /workspace/services/api/requirements.txt
COPY services/api /workspace/services/api
ENV PYTHONPATH=/workspace/services/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

