#Use a python base image
#make directory in the container
#copy all the files from the current directory to the container's directory
#Install dependencies in the container's directory
#Write the commands needed to run this project in that container
#build the image
#run the image to start the container

#Use python base image
FROM python:3.9-slim

#Set the working directory
WORKDIR /ml_docker

COPY . /ml_docker

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8083

CMD ["uvicorn", "classifier:app", "--host", "0.0.0.0" ,"--port", "8083"]

# CMD: This is a Dockerfile instruction that specifies the command to run when the container starts. 
# It is the default command that gets executed when you run the container.

# ["uvicorn", "classifier:app", "--host", "0.0.0.0", "--port", "8000"]:
#     uvicorn: This is a fast ASGI server for Python, often used to run FastAPI applications.
#     classifier:app: This part tells uvicorn to look for an app object in the classifier.py file. 
#     In FastAPI, app is usually the instance of the FastAPI application.
#     --host 0.0.0.0: This tells the server to accept connections from any network interface (not just localhost). 
#     So, it's making the FastAPI app accessible externally when running inside a container.
#     --port 8000: This specifies the port on which the application will run inside the container. In this case, it's set to port 8000.

# In simple terms:

# to listen on port 8000 and be accessible from any network (not just the local machine). 
# So, when you run the container, it will serve your app on http://0.0.0.0:8000.

# You can then access this app on your local machine (if you run the container with docker run -p 8000:8000) at http://localhost:8000.

#uvicorn classifier:app --host 0.0.0.0 --port 8083

# --host 0.0.0.0:

#     --host: This is an option for the server (in this case, uvicorn), 
            #specifying the network interface on which the server should listen for incoming connections.

#     0.0.0.0: This is a special address that tells the server to listen on all available network interfaces. 
#     In other words, it allows the server to accept connections from any IP address, not just from your local machine (localhost).

# Why this is important:

#     If you use localhost (or 127.0.0.1) as the host, the app will only be accessible from the same machine where it's running. 
#     So, if you're running the app in a Docker container, it will only be accessible from within the container itself, 
#     and not from your local computer or any other device.

#     By setting --host 0.0.0.0, you're making your FastAPI application accessible from outside the container, 
#     which means you can access it through localhost or 0.0.0.0 on your host machine, 
#     or even from other devices on the same network (depending on your Docker setup)


# docker run -d -p 8083:8083 <image_name_or_id>

#     -p 8083:8083 maps port 8083 on the host to port 8083 in the container.