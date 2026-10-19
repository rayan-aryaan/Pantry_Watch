# ---- build stage: install dependencies into an isolated prefix ----
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: small image, non-root user ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
WORKDIR /home/appuser
COPY --from=build /install /usr/local
COPY app ./app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health')"
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app.main:app"]
