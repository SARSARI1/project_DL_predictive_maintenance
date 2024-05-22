import os
from flask import Flask, redirect, url_for, render_template, request, session, make_response
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
import pickle
from matplotlib.offsetbox import DrawingArea
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import scipy.stats as st
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.platypus import Image,Spacer
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

#-----------------------------------------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key="hello"
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///feedbacks.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#------------------------------------------------------------load models--------------------------------------------------------------




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

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":
    app.run(debug=True)

   