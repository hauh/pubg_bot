FROM python:slim
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
RUN apt-get -y update && apt-get -y upgrade
WORKDIR /opt/pubglik_bot
COPY requirements.txt .
RUN	python -m pip install --upgrade pip && \
	pip install -r requirements.txt
COPY pubglik ./pubglik
RUN mkdir data
CMD ["python", "-m", "pubglik"]
