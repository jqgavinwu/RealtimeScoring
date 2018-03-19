# Project name
Flask API prototype for deploying model-as-a-service
## Code purpose
These files allow my team to stand up a web service to take input from secure http calls for a prediction model we package up (see my other repository ModelPackTestProf) in order to produce a score based on a ML model. I'm using the Flask framework. The enviroment in which this web service will run is packaged up in a Docker image, which is also used during model development to ensure consistency. My Docker image can be found by following the link below.

[Model Development Docker Image](https://hub.docker.com/r/jgavinwu/zen-env-beta/)