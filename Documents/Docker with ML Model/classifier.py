#We are using fastapi virutal environment which is present inside FastAPI folder. We shall use this venv for all the projects

import pickle
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app=FastAPI()

#Load iris dataset and train the model
iris=load_iris()
X_train,X_test,y_train,y_test=train_test_split(iris.data,iris.target,test_size=0.2,random_state=42)
#splitting the data into train and test. Test size is 20 percent of entire data

#define which model to use
model=RandomForestClassifier(n_estimators=100, random_state=42)

#fit the model with input and output
model.fit(X_train,y_train)


#save the model in ml_model.pkl file; wb is writing into a file as binary format
with open("ml_model.pkl","wb") as f:
    pickle.dump(model,f)

# 1. open("model.pkl", "wb")
#     Purpose: Opens a file named model.pkl in write-binary (wb) mode.
#     "model.pkl": The file where the serialized model will be stored. 
#     The .pkl extension indicates that it's a "pickled" file, a common format for saving Python objects.
#     "wb":
#         w: Write mode (creates a new file or overwrites an existing file).
#         b: Binary mode (necessary for handling non-text data like models).

# 2. pickle.dump(model, f)
#     pickle.dump: A function from Python's pickle module that serializes (converts an object into a byte stream) 
#     the model and writes it to the file f.
#     model: The machine learning model you want to save, which could be from any library like Scikit-learn, XGBoost, etc.
#     f: The file object returned by the open() function where the serialized data is written.

# What Happens Internally?

#     The pickle module takes the model's structure, parameters, and learned information (e.g., weights, hyperparameters) 
#     and converts it into a binary format.
#     This binary data is then saved into the file model.pkl.

with open("ml_model.pkl","rb") as f:
    model=pickle.load(f)

#define input data structure using Pydantic
class Features(BaseModel):
    features: List[float]

@app.post("/predict")
def predict(data:Features):
    #Load the model
    #return {"prediction": 0}
    #with open("ml_model.pkl","rb") as f:
    #    model=pickle.load(f) #Keeping this model outside because now everytime predict endpoint is called, model is opened and loaded

    prediction=model.predict([data.features])
    
    return {"prediction":iris.target_names[prediction][0]}


    