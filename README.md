### Google_PaLM2_EnterpriseSearch

### 1. Overview
The purpose of this demo is to test Google's PaLM2 API with Enterprise Search.
The architecture used in this demo is to implement RAG(Retrieval-Augmented Generation) with Enterprise search as a repository to store domain knowledge.
Most users have their own domain context for their purpose of using LLM. RAG architecture could be inevitable at the moment even though fine tuning provides better quality of outcome as time goes by.

### 2. Application architecture

#### 2.1 Request flow.

The architecture for application is to implement RAG(Retrieval Augmented Generation). 
We can add a “Adapter layer in Vertex AI” for fine tuning(PEFT: Parameter Efficient Fine Tuning) if users want to improve quality of response by adding additional weight from PEFT.
 
![alt text](https://github.com/shins777/PaLM2-with-Enterprise-Search/blob/main/img/architecture.png)

The flows of request are as follows
+ After receiving a user query, the application retrieves the context corresponding to the query from Enterprise Search. The Enterprise Search can be replaced by “Matching engine in Vertex AI” that is a vector database in Google. 
+ Build a prompt using the result of retrieval to provide more domain specific context for PaLM2.
+ Receive the response for the requests containing the context. 

#### 2.2 Application configuration.

To configure the demo, create a variables.py as follows and put the file into utils directory.

You need to set up three ways to get service accounts for credentials in the demo as follows. 
But, If you want to use one service account for those. You may set the same service account for three different purposes. 
+ Service account for PaLM2 API
+ Service account for Enterprise Search
+ Service account for integrated logging.

````
from pathlib import Path

# 1. GCP information for PaLM2 API
PROJECT_ID="<Project ID>"
REGION="<Region name>"   
SVC_ACCT_FILE="<Service Account JSON File>"

# 2. GCP Service account file for Enterprise Search API.
ES_SVC_ACCT_FILE= "<Service Account JSON File>"

# 3. GCP Search account file for Cloud Logging.
LOG_PROJECT_ID="<Project ID>"
LOG_REGION="<Region name>"
LOG_SVC_ACCT_FILE= "<Service Account JSON File>"

# 4. PaLM2 Model parameter
MODEL="google/text-bison@001"
MAX_OUTPUT_TOKENS=1024
TEMPERATURE=0.2
TOP_P=0.8
TOP_K=40

# 5. Default prompt information.
default_prompt_value = "< Add default prompt >"

# 6. Default endpoint for Enterprise Search
end_point = "<EndPoint URL in 'GenApp Builder > Enterprise Search > Intergration > API'>"

````

To add "Default endpoint(# 6 ) in the variables.py. Copy the Endpoint URL in Enterprise Search as follows.

![alt text](https://github.com/shins777/PaLM2-with-Enterprise-Search/blob/main/img/es_api.png)

#### 2.3 Run the application in local environment.

To authenticate GCP using ADC, create a file ( auth.sh )
````
GOOGLE_APPLICATION_CREDENTIALS="<path of the service account file>"
gcloud auth application-default login
````

To run the UI using streamlit library, create a file ( run.sh )
````
streamlit run <full path>/Google_PaLM2_EnterpriseSearch/src/front/palm2_ui.py
````

### 3. System architecture

The demo has a user interface based on Streamlit that provides a web server. 
It needs to build a docker image to use Cloud Run in GCP to be able to access the web server publicly.  

The following image shows the system architecture and deployment flow. 
+ The developer needs to build a docker image with the source code 
+ Conduct unit tests in the local environment.
+ Push the image to the artifact registry. 
+ Run Cloud Run with the docker image in the artifact repository.
+ After launching the Cloud run, users can see the Test UI in their browsers. Use the url of Cloud Run after deploying to access the UI.

![alt text](https://github.com/shins777/PaLM2-with-Enterprise-Search/blob/main/img/system_arch.png)

#### 3.1 Build Docker

Create a Dockerfile containing configuration corresponding to your demo environment.

````
FROM python:latest

WORKDIR /genai

COPY . .

RUN pip install -I -r ./requirements.txt

EXPOSE 8501

CMD streamlit run /genai/src/front/palm2_ui.py
````

Build a Docker image and unit test to the demo on local environment.
````
docker build -t <IMAGE:TAG> .

docker run -d -p 80:8501 <IMAGE:TAG>

docker exec -it <container id> /bin/bash

docker stop <container id>

````
````
> ~/Google_PaLM2_EnterpriseSearch$ . ./auth.sh
> ~/Google_PaLM2_EnterpriseSearch$ docker build -t palm2_test:1.1 .
> ~/Google_PaLM2_EnterpriseSearch$ docker images
> ~/Google_PaLM2_EnterpriseSearch$ docker run -d -p 80:8501 palm2_test:1.1
> ~/Google_PaLM2_EnterpriseSearch$ docker ps
> ~/Google_PaLM2_EnterpriseSearch$ docker stop <container id>

````

#### 3.2 Register and push the Docker image to Artifact registry

Refer to the following url to push and imanges. 

https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling

````
gcloud artifacts repositories create gen-ai-repo  --repository-format=docker \
--location=us-central1 --description="Docker repository"

gcloud artifacts repositories list

gcloud auth configure-docker us-east1-docker.pkg.dev

docker tag SOURCE-IMAGE LOCATION-docker.pkg.dev/PROJECT-ID/REPOSITORY/IMAGE:TAG

gcloud artifacts repositories describe REPOSITORY --project=PROJECT-ID --location=LOCATION
````

````
> ~/Google_PaLM2_EnterpriseSearch$ gcloud artifacts repositories create palm2-test-repo  --repository-format=docker \
--location=us-central1 --description="Docker repository"
> ~/Google_PaLM2_EnterpriseSearch$ gcloud artifacts repositories list
> ~/Google_PaLM2_EnterpriseSearch$ gcloud auth configure-docker us-central1-docker.pkg.dev
> ~/Google_PaLM2_EnterpriseSearch$ docker tag palm2_test:1.1 us-central1-docker.pkg.dev/gen-ai-project-hangsik/palm2-test-repo/palm2_test:1.1
> ~/Google_PaLM2_EnterpriseSearch$ docker push us-central1-docker.pkg.dev/gen-ai-project-hangsik/palm2-test-repo/palm2_test:1.1
````

#### 3.3 Deploy the Docker image on the Cloud run.

To deploy the images in Artifact registry in GCP, refer to the following url. 

https://cloud.google.com/run/docs/deploying#command-line

````
gcloud run deploy SERVICE --image IMAGE_URL

> ~/Google_PaLM2_EnterpriseSearch$ gcloud run deploy palm2-test --image=us-central1-docker.pkg.dev/gen-ai-project-hangsik/palm2-test-repo/palm2_test:1.1 --region=us-central1 --port=8501 --platform managed --allow-unauthenticated --min-instances=1 --max-instances=5

````
