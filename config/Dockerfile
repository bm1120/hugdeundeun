FROM python:3.10
LABEL description = "Analytics Environment python 3.10 for crawling & dashboard"

RUN mkdir -p /analysis/data

WORKDIR /analysis

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt

RUN pip install jupyter -U && pip install jupyterlab
RUN pip3 install -r requirements.txt

EXPOSE 8888

ENTRYPOINT  ["jupyter", "lab", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root", "--NotebookApp.token=''"]