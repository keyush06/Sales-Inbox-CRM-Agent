FROM python:3.10-slim

WORKDIR /app
RUN pip install --no-cache-dir streamlit requests
COPY frontend /app/frontend
ENV STREAMLIT_PORT=8501
EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
