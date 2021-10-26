# Dockerfile

FROM python:3.6

WORKDIR /app

ADD . /app

RUN pip3 install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org -r requirements.txt

EXPOSE 3000

# EXPOSE 5001

CMD ["python", "app/app.py"]