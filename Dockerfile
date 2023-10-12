FROM python:3.9
WORKDIR /app
COPY . /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt
EXPOSE 80
ENV NAME DATABASE_URL
ENV NAME SECRET_EN_KEY
ENV NAME SECRET_PASSWORD_KEY
ENV NAME ALGORITHM
CMD ["python", "app.py"]