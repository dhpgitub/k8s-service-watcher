FROM dhpcontainreg.azurecr.io/core-image/python:3.7-alpine3.7
RUN git clone https://github.com/dhpgitub/k8s-service-watcher.git
WORKDIR k8s-service-watcher
RUN ls -alFrt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["py-k8s-service_watch.py"]