import os
from flask import Flask, redirect, url_for, render_template, request, session, make_response
from datetime import timedelta
import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler

#-----------------------------------------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedbacks.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#------------------------------------------------------------load models--------------------------------------------------------------

loaded_model = pickle.load(open('model_np.pkl', 'rb'))

#------------------------------------------------------------------------------------Sessions-------------------------------------------------------: 

app.permanent_session_lifetime = timedelta(minutes=5)

#----------------------------------------------------------------------------------------------------functions----------------------------------------------------------------:

# Predict machine failure
def predict_fail(productID, type_pd, airTemperature, processTemperature, rotationalSpeed, torque, toolWear):
    # Arguments
    productID = int(productID)
    type_pd = int(type_pd)
    airTemperature = float(airTemperature)
    processTemperature = float(processTemperature)
    rotationalSpeed = int(rotationalSpeed)
    torque = float(torque)
    toolWear = int(toolWear)

    input_test = pd.DataFrame({
        'Product ID': [productID],
        'Type': [type_pd],
        'Air temperature [K]': [airTemperature],
        'Process temperature [K]': [processTemperature],
        'Rotational speed [rpm]': [rotationalSpeed],
        'Torque [Nm]': [torque],
        'Tool wear [min]': [toolWear]
    })

    pred_np = loaded_model.predict(input_test)
    result = pred_np[0]

    return result

# -------------------------------------------------------Routes----------------------------------------------------------------------------------------- :

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/index")
def logo():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/entryData")
def entryData():
    return render_template('entryData.html')

@app.route("/resultData")
def resultData():
    return render_template('resultData.html')

@app.route("/make_predictions", methods=["POST"])
def make_predictions():
    if request.method == "POST":
        session.permanent = True
        # Get the user input
        productID = request.form["productID"]
        type_pd = request.form["type_pd"]
        airTemperature = request.form["airTemperature"]
        processTemperature = request.form["processTemperature"]
        rotationalSpeed = request.form["rotationalSpeed"]
        torque = request.form["torque"]
        toolWear = request.form["toolWear"]

        # Perform prediction
        predicted_value = predict_fail(productID, type_pd, airTemperature, processTemperature, rotationalSpeed, torque, toolWear)

        # Storing the values on session (converting to standard Python types)
        session["productID"] = str(productID)
        session["type_pd"] = str(type_pd)
        session["airTemperature"] = str(airTemperature)
        session["processTemperature"] = str(processTemperature)
        session["rotationalSpeed"] = str(rotationalSpeed)
        session["torque"] = str(torque)
        session["toolWear"] = str(toolWear)
        session["predicted_value"] = int(predicted_value)

    return redirect(url_for('resultData'))

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
