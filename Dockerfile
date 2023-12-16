FROM python:3.9.3

RUN  mkdir -p  /slangtrap-model
WORKDIR  /slangtrap-model

EXPOSE 5000
ENV HOST 0.0.0.0

RUN pip3 install --no-cache-dir --upgrade pip

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

#RUN docker buildx build --platform linux/amd64 -t slangtrap-capstone

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY  . .

CMD ["python", "run.py"]

