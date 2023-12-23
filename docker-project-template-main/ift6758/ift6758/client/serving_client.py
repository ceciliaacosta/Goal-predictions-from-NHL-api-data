import json
import requests
import pandas as pd
import logging
import os


logger = logging.getLogger(__name__)

class ServingClient:
    def __init__(self, ip: str = "0.0.0.0", port: int = 5050, features=None):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")

        if features is None:
            features = ["distance"]
        self.features = features

        # any other potential initialization

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the inputs into an appropriate payload for a POST request, and queries the
        prediction service. Retrieves the response from the server, and processes it back into a
        dataframe that corresponds index-wise to the input dataframe.
        
        Args:
            X (Dataframe): Input dataframe to submit to the prediction service.
        """
        #data = json.dumps([X])
        url = f"{self.base_url}/predict"
        payload = X.to_json(orient='records')
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(url, json=payload)
            #response_data = response.json()
            #response.raise_for_status()
            response_data = response.json()

            # Vérifiez d'abord si la réponse est un succès et contient des prédictions
            if response_data['status'] == 'success' and 'predictions' in response_data:
            # Créez un DataFrame à partir de la liste de prédictions
                predictions = pd.DataFrame(response_data['predictions'], columns=['prediction'])
                
            else:
                 # Gérez le cas où la réponse n'est pas ce que vous attendiez
                 raise ValueError(f"Unexpected response format or failure status: {response_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            raise
        return predictions

    def logs(self) -> dict:
        """Get server logs"""
        url = f"{self.base_url}/logs"
        response = requests.get(url)
        return response.json()
        #raise NotImplementedError("TODO: implement this function")

    def download_registry_model(self, workspace: str, model: str, version: str) -> dict:
        """
        Triggers a "model swap" in the service; the workspace, model, and model version are
        specified and the service looks for this model in the model registry and tries to
        download it. 

        See more here:

            https://www.comet.ml/docs/python-sdk/API/#apidownload_registry_model
        
        Args:
            workspace (str): The Comet ML workspace
            model (str): The model in the Comet ML registry to download
            version (str): The model version to download
        """
        url = f"{self.base_url}/download_registry_model"
        data = {
            "workspace": workspace,
            "model_name": model,
            "version": version
        }

        response = requests.post(url, json=data)
        return response.json()
        #raise NotImplementedError("TODO: implement this function")


# if __name__ == '__main__':

#     # Create an instance of ServingClient
#     client = ServingClient(ip="127.0.0.1", port=8080, features=["distance_to_target_goal","angle_to_target_goal"])

#     # Example DataFrame for prediction
#     data = pd.DataFrame({
#     "distance_to_target_goal": [44.6430285711],
#     "angle_to_target_goal": [74.4071890607]})

#     # Download a model from the registry
#     model_download_response = client.download_registry_model  ( workspace="francis75",
#         model="Regression3",
#         version="1",)
#     print("Model Download Response:")
#     print(model_download_response)


#     # Predict using the model
#     predictions = client.predict(data)
#     print("Predictions:")
#     print(predictions)


    # Get server logs
    # logs = client.logs()
    # print("Server Logs:")
    # print(logs)


