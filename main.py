import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from flask import Flask, redirect, url_for, render_template, request, session, make_response
from datetime import datetime, timedelta
import pickle
import pandas as pd

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

def generate_pdf(session_values):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Add logo
    logo_path = r'static\img\logo.png'
    logo = Image(logo_path, width=300, height=300)
    elements.append(logo)
    elements.append(Spacer(1, 20))
    
    # Add title
    title = "Prediction Report"
    elements.append(Paragraph(title, getSampleStyleSheet()['Title']))
    elements.append(PageBreak())  # Move to the next page
    
    # Add the date and time
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"Date: {current_datetime}", getSampleStyleSheet()['Normal']))
    elements.append(Spacer(1, 20))
    
    # Add input values
    input_values = [
        f"Product ID: {session_values['productID']}",
        f"Type: {session_values['type_pd']}",
        f"Air Temperature [K]: {session_values['airTemperature']}",
        f"Process Temperature [K]: {session_values['processTemperature']}",
        f"Rotational Speed [rpm]: {session_values['rotationalSpeed']}",
        f"Torque [Nm]: {session_values['torque']}",
        f"Tool Wear [min]: {session_values['toolWear']}"
    ]
    for value in input_values:
        elements.append(Paragraph(value, getSampleStyleSheet()['Normal']))
        elements.append(Spacer(1, 12))
    
    # Add prediction result
    elements.append(Paragraph(f"Predicted Value: {session_values['predicted_value']}", getSampleStyleSheet()['Normal']))
    elements.append(Spacer(1, 20))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

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

@app.route("/generate_report")
def generate_report():
    if not all(key in session for key in ("productID", "type_pd", "airTemperature", "processTemperature", "rotationalSpeed", "torque", "toolWear", "predicted_value")):
        return "Session values are missing", 400
    
    session_values = {
        "productID": session.get("productID"),
        "type_pd": session.get("type_pd"),
        "airTemperature": session.get("airTemperature"),
        "processTemperature": session.get("processTemperature"),
        "rotationalSpeed": session.get("rotationalSpeed"),
        "torque": session.get("torque"),
        "toolWear": session.get("toolWear"),
        "predicted_value": session.get("predicted_value")
    }
    
    pdf_buffer = generate_pdf(session_values)
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
    
    return response

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
