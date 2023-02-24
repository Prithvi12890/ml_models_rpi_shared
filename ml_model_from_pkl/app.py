from flask import Flask, request, render_template
import time
import datetime

app = Flask(__name__)
app.debug = True # Make this False if you are no longer debugging

moisture_level = ""
water_pump = ""

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/temp_hum")
def temp_hum():
	import sys
	import Adafruit_DHT
	humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
	if humidity is not None and temperature is not None:
		return render_template("temp_hum.html",temp=temperature,hum=humidity)
	else:
		return render_template("no_sensor.html")

@app.route("/temp_hum_db", methods=['GET'])
def temp_hum_db():
    from_date_str = request.args.get('from', time.strftime("%Y-%m-%d 00:00"))
    to_date_str = request.args.get('to', time.strftime("%Y-%m-%d %H:%M"))
    if not validate_date(from_date_str):
        from_date_str = time.strftime("%Y-%m-%d 00:00")
    if not validate_date(to_date_str):
        to_date_str = time.strftime("%Y-%m-%d %H:%M")
    import sqlite3
    conn=sqlite3.connect('/var/www/major_project/app.db')
    curs=conn.cursor()
	# curs.execute("SELECT * FROM temperatures")
	# temperatures = curs.fetchall()
	# curs.execute("SELECT * FROM humidities")
	# humidities = curs.fetchall()
	# conn.close()

    curs.execute("SELECT * FROM temperatures WHERE rDatetime BETWEEN ? AND ? ORDER BY rDatetime DESC", (from_date_str, to_date_str))
    temperatures = curs.fetchall()
    curs.execute("SELECT * FROM humidities WHERE rDatetime BETWEEN ? AND ? ORDER BY rDatetime DESC", (from_date_str, to_date_str))
    humidities = curs.fetchall()
    conn.close()

    return render_template("temp_hum_db.html",temp=temperatures,hum=humidities)

def validate_date(d):
    try:
        datetime.datetime.strptime(d, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

@app.route("/home")
def temp_hum_ui_home():
    import sys
    import Adafruit_DHT
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    if humidity is not None and temperature is not None:
        return render_template("dashboard.html",temp=temperature,hum=humidity,moisture=moisture_level,pump=water_pump)
    else:
        return render_template("no_sensor.html")

@app.route("/home/dashboard")
def temp_hum_ui_home_dashboard():
    import sys
    import Adafruit_DHT
    import sqlite3
    conn=sqlite3.connect('/var/www/major_project/app.db')
    curs=conn.cursor()
    curs.execute("SELECT * FROM temperatures")
    temperatures = curs.fetchall()
    curs.execute("SELECT * FROM humidities")
    humidities = curs.fetchall()
    conn.close()
    x_ticks = [record[0] for record in temperatures]
    y_ticks1 = [record[2] for record in temperatures]
    y_ticks2 = [record[2] for record in humidities]
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
    if humidity is not None and temperature is not None:
        print(x_ticks)
        return render_template("dashboard.html",temp=temperature,hum=humidity,moisture=moisture_level,pump=water_pump,labels=x_ticks,values1=y_ticks1,values2=y_ticks2)
    else:
        return render_template("no_sensor.html")

@app.route("/home/crop_recommendation")
def crop_recommendation():
    return render_template("crop_recommendation.html")

import numpy as np
import pickle

crop_recommendation_model_path = 'models/RandomForest.pkl'
crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))

@ app.route('/home/crop-prediction', methods=['POST'])
def crop_prediction():
    title = 'Crop Recommendation'

    if request.method == 'POST':
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorous'])
        K = int(request.form['pottasium'])
        ph = float(request.form['ph'])
        data = np.array([[N, P, K, ph]])
        my_prediction = crop_recommendation_model.predict(data)
        final_prediction = my_prediction[0]

        return render_template('crop_prediction.html', prediction=final_prediction, title=title)
    else:
        return render_template("crop_recommendation.html")

@app.route("/home/tables")
def tables():
    import sqlite3
    conn=sqlite3.connect('/var/www/major_project/app.db')
    curs=conn.cursor()
    curs.execute("SELECT * FROM temperatures ORDER BY rDatetime DESC LIMIT 5")
    temperatures = curs.fetchall()
    curs.execute("SELECT * FROM humidities ORDER BY rDatetime DESC LIMIT 5")
    humidities = curs.fetchall()
    conn.close()
    return render_template("tables.html",temp=temperatures,hum=humidities)

import RPi.GPIO as GPIO

#GPIO SETUP
channel = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)
GPIO.setup(26, GPIO.OUT)
GPIO.setup(16,GPIO.IN)
GPIO.setup(19,GPIO.OUT)

# un-comment only before use or else, by default the system will shutdown soon as you start it as 16 is high if nothing is connected to it
# if (GPIO.input(16)):
    # import os
    # GPIO.output(19,GPIO.HIGH)
    # time.sleep(1)
    # # GPIO.cleanup()
    # print("shutdown requested")
    # # os.system("sudo shutdown -h now")

def callback(channel):
        global moisture_level, water_pump
        if GPIO.input(channel):
                # print("no Water Detected!")
                moisture_level = "Not Adequate"
                GPIO.output(26, GPIO.HIGH)
                water_pump = "ON"
        else:
                # print("Water Detected!")
                moisture_level = "Adequate"
                GPIO.output(26, GPIO.LOW)
                water_pump = "OFF"

GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=300)  # let us know when the pin goes HIGH or LOW
GPIO.add_event_callback(channel, callback)  # assign function to GPIO PIN, Run function on change

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
