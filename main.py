import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from flask import Flask, redirect, url_for, render_template, request, session, make_response
from datetime import datetime, timedelta
import pickle
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt

from reportlab.lib.units import inch
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
# Load dataset
df = pd.read_csv('data.csv')  # Replace 'your_dataset.csv' with your actual dataset filename

# Function to generate Pareto chart for a given product ID
# Function to generate Pareto chart for a given product ID and dataset
def generate_pareto(product_id, dataset):
    # Filter dataframe for the selected product ID
    product_data = dataset[dataset['Product ID'] == product_id]
    
    # Count occurrences of machine failure types
    failure_counts = product_data.iloc[:, 9:].sum().sort_values(ascending=False)
    
    # Calculate cumulative sum
    cumsum = failure_counts.cumsum()
    
    # Calculate percentage
    percentage = cumsum / failure_counts.sum() * 100
    
    # Plot Pareto chart
    fig, ax1 = plt.subplots(figsize=(6, 6))
    ax2 = ax1.twinx()
    
    ax1.bar(failure_counts.index, failure_counts, color='tab:blue')
    ax2.plot(failure_counts.index, percentage, color='tab:red', marker='o')
    
    ax1.set_xlabel('Failure Type')
    ax1.set_ylabel('Count', color='tab:blue')
    ax2.set_ylabel('Cumulative Percentage', color='tab:red')
    
    plt.title(f'Pareto Chart for Product ID: {product_id}')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save plot to BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    
    return buffer


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

# Generate PDF report
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
        ("Product ID", session_values['productID']),
        ("Type", session_values['type_pd']),
        ("Air Temperature [K]", session_values['airTemperature']),
        ("Process Temperature [K]", session_values['processTemperature']),
        ("Rotational Speed [rpm]", session_values['rotationalSpeed']),
        ("Torque [Nm]", session_values['torque']),
        ("Tool Wear [min]", session_values['toolWear'])
    ]
    bold_style = getSampleStyleSheet()['Normal']
    bold_style.fontName = 'Helvetica-Bold'
    bold_style.fontSize = 14

    value_style = ParagraphStyle(name='ValueStyle', textColor=colors.orange, fontSize=14)
    line_spacing = 18
    column_spacing = 10  # Adjust column spacing as needed

    for column, value in input_values:
        column_paragraph = Paragraph(f"<b>{column}:</b>", bold_style)
        if column != "Product ID" and int(value) == 0:
            value_paragraph = Paragraph("Doesn't need repair", value_style)
        else:
            value_paragraph = Paragraph(str(value), value_style)
        elements.extend([column_paragraph, Spacer(1, column_spacing), value_paragraph])
        elements.append(Spacer(1, line_spacing))

    # Add prediction result
    predicted_value = session_values['predicted_value']
    if predicted_value == 0:
        result_message = "---> The machine doesn't need repair."
    else:
        result_message = "---> The machine needs repair."
    result_style = ParagraphStyle(name='ResultStyle', textColor=colors.red, fontSize=14)
    result_paragraph = Paragraph(result_message, result_style)
    elements.extend([result_paragraph, Spacer(1, 20)])

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
@app.route("/pareto")
def pareto():
    # Load your dataset here or replace it with the appropriate method to fetch the data
    dataset = pd.read_csv("data.csv")  # Adjust the file path as needed
    
    # Extract unique product IDs from the dataset
    product_ids = dataset['Product ID'].unique().tolist()
    
    return render_template('select_product.html', product_ids=product_ids)


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



# Route for generating Pareto chart
@app.route("/generate_report", methods=['GET', 'POST'])
def generate_pareto_chart():
    # Get selected product ID from form
    product_id = request.form['productID']
    
    # Load your dataset here or replace it with the appropriate method to fetch the data
    dataset = pd.read_csv("data.csv")  # Adjust the file path as needed
    
    # Generate Pareto chart for the selected product
    pareto_chart_buffer = generate_pareto(product_id, dataset)
    
    # Create PDF document
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    
    # Add Pareto chart to PDF
    pareto_img = Image(pareto_chart_buffer)
    elements.append(pareto_img)
    
    # Build PDF document
    doc.build(elements)
    
    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=pareto_{product_id}.pdf'
    
    return response

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
