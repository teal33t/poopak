FROM python:3.8

# Set the working directory
ENV HOME=/application
WORKDIR /application

# Install dependencies
COPY requirements.txt /application
RUN pip install -r requirements.txt
RUN pip install flask

# Copy the application
COPY . /application

ADD docker_wait /wait
RUN chmod +x /wait
CMD /wait
