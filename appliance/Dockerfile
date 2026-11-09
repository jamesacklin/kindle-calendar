FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY calendar_server.py render_calendar.py render_six_day.py ./
COPY assets/inter/ assets/inter/

USER 65532:65532
EXPOSE 8765
ENTRYPOINT ["python", "calendar_server.py"]
