FROM python:slim
ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1
WORKDIR /opt/app
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
	pip install --no-cache-dir -r requirements.txt
COPY pubglik ./pubglik
CMD ["python", "-m", "pubglik"]
