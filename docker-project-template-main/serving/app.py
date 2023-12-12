"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:
    
    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
from comet_ml import API
import json
import os
from pathlib import Path
import logging
import sys
from flask import Flask, jsonify, request, abort
import requests
import sklearn
import pandas as pd
import ift6758
import joblib
from joblib import  load

api = API()



LOG_FILE = os.environ.get("FLASK_LOG", "flask.log")


app = Flask(__name__)


# Initialize the models as None
app.model = None

@app.route("/", methods=["GET",'POST'])
def home():
    return "Hello, this is the home page!"


@app.before_first_request
def before_first_request():
    """
    Hook to handle any initialization before the first request (e.g., load model,
    setup logging handler, etc.)
    """
    # TODO: setup basic logging configuration
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)


@app.route("/logs", methods=["GET"])
def logs():
    """Reads data from the log file and returns them as the response"""
    # TODO: read the log file specified and return the data
    #raise NotImplementedError("TODO: implement this endpoint")
    try:
        with open(LOG_FILE, 'r') as log_file:
            logs_data = log_file.read()
        response = {'logs': logs_data}
    except FileNotFoundError:
        response = {'error': 'Log file not found'}
    except Exception as e:
        response = {'error': str(e)}
    #response = None
    return jsonify(response)  # response must be json serializable!


@app.route("/download_registry_model", methods=["POST"])
def download_registry_model():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

    The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

    Recommend (but not required) json with the schema:

        {
            workspace: (required),
            model: (required),
            version: (required),
            ... (other fields if needed) ...
        }
    
    """
    try:
        # Get POST json data
        json_data = request.get_json()
        app.logger.info(json_data)

        # Extract information from the JSON data
        workspace = json_data.get('workspace')
        model_name = json_data.get('model_name')
        version = json_data.get('version')

        # Retrieve the model by name
        # Retrieve the model by name
        model = api.get_model(workspace=workspace, model_name=model_name)

        # Specify the local path where the model file should be
        local_model_path = f"{model_name}.joblib"

        # Check if the model file exists locally
        exists_locally = os.path.isfile(local_model_path)
        # Check if the model is already downloaded
        if exists_locally:
            # If yes, load that model and write to the log about the model change
            try:
                app.model=load(local_model_path) 
                app.logger.info(f"Loaded model {model_name} version {version}")
            except Exception as e:
                app.logger.error(f"Error loading model {model_name} version {version}: {str(e)}")
        else:
            # If no, try downloading the model
            try:
                model.download("1.0.0",".", expand=True)
                app.model=load(local_model_path) 
            except Exception as e:
                app.logger.error(f"Error downloading model {model_name} version {version}: {str(e)}")

        response = {'status': 'success'}
    
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}

    app.logger.info(response)
    return jsonify(response)  # response must be json serializable!


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    # Get POST json data
    # TODO:
    #raise NotImplementedError("TODO: implement this enpdoint")
    try:
        # TODO: Implement logic to use your machine learning models for prediction
        # For example, assuming you have a model named `default_model_1`
        # Get POST json data
        json_data = request.get_json()
        app.logger.info(json_data)      
        # Convert the received JSON data back to a DataFrame
        input_df = pd.read_json(json_data, orient='records')
        predictions = app.model.predict(input_df)
        result = predictions.tolist() 
            # Format the response
        response = {'predictions': result, 'status': 'success'}
    except Exception as e:
        response = {'status': 'failure', 'error': str(e)}

    app.logger.info(response)
    return jsonify(response)  # response must be json serializable!

if __name__ == '__main__':
   app.run(port=8080)
   
