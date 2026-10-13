FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh
RUN DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput -v0 \
 && useradd -u 10001 -m app && mkdir -p /data && chown -R app /data
USER 10001
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["web"]
