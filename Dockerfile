FROM dhpcontainreg.azurecr.io/core-image/python:3.6-alpine3.8
RUN apk add --no-cache bash git openssh
RUN git clone https://github.com/dhpgitub/k8s-service-watcher.git
RUN del bash git openssh
WORKDIR k8s-service-watcher
RUN ls -alFrt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["py-k8s-service_watch.py"]
