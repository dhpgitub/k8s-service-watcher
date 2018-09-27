FROM dhpcontainreg.azurecr.io/core-image/python:3.6-alpine3.8
RUN apk add --no-cache --virtual .build-deps bash git openssh && \
    git clone https://github.com/dhpgitub/k8s-service-watcher.git && \
    apk del .build-deps
WORKDIR k8s-service-watcher
RUN ls -alFrt
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["py-k8s-service_watch.py"]
