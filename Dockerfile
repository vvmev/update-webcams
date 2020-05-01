FROM python:3

RUN apt-get update && apt-get install -y \
    graphicsmagick \
    ghostscript \
 && rm -rf /var/lib/apt/lists/*

COPY update-webcams.py /update-webcams

ENTRYPOINT [ "/update-webcams" ]
