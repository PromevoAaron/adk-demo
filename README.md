# ADK Demo

Quick simple ADK demonstration with two agents.

python3 -m venv .venv

source .venv/bin/activate

which python (to be sure venv activated properly)

pip install -r requirements.txt

# Deploying the Agent to Agent Engine

Run this from the agent directory: adk deploy agent_engine --project=YOUR_PROJECT_ID --region=us-central1 --staging_bucket=gs://YOUR_BUCKET_NAME --display_name="YOUR_AGENT_NAME" .

Warning: It will upload everthing in the directory, even the .env file. However, they are working on a .ae_ignore process which is not ready yet it seems. The process is new :)

This deploys the agent to Agent Engine. 

# Adding to Agentspace
Clone this repo into it's own folder. It doesn't need to integrate with your agent, you just need this to register your agent to Agentspace
https://github.com/VeerMuchandi/agent_registration_tool

The instructions are on this video: https://www.youtube.com/watch?v=yxRyVxjKURI

Make a new .venv for this temporary repo folder. You should only need to install the google-adk on this .venv you create for this step.

Alter the config.json file to use your information.

Then run this: python as_registry_client.py --config config.json

# Other Things

To allow agents to work with BigQuery, you need to give permissions to the AI Platform Reasoning Engine Service Agent. You can find that specific service account in the IAM table. 
To read data, the typical roles needed are BigQuery Data Viewer and BigQuery Job User. 

The Discovery Engine Service Agent service account also needs AI Platform permissions to AI Platform to see the agent's code.