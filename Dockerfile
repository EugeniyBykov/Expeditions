FROM python:3.12-slim

ARG USER=user
ARG UID=1000

ENV PYTHONUNBUFFERED=1
ENV PATH="${PATH}:/home/$USER/.local/bin"

RUN adduser --uid $UID --disabled-password --gecos '' $USER
USER $USER
WORKDIR /home/$USER

COPY requirements.txt /tmp/requirements.txt
RUN pip install --user --no-cache-dir -r /tmp/requirements.txt

COPY ./app ./app

EXPOSE 8000

HEALTHCHECK --interval=1m --timeout=10s --retries=3 --start-period=30s CMD python app/tools/scripts/healthcheck.py
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]