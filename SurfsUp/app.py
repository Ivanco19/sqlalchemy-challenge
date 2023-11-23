# Import the dependencies.
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)
print(Base.classes.keys())

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def welcome():
    #List available API Routes
    return (
        f"<b>Available Routes:</b><br/>"
        f"To get precipitation data for the last year -----> /api/v1.0/precipitation<br/>"
        f"To get the stations id -----> /api/v1.0/stations<br/>"
        f"To get temperature for the last year for the most active station -----> /api/v1.0/tobs<br/>"
        f"To get min, max and average temperature from a start date. <b>Example: /api/v1.0/2017-05-23</b> -----> /api/v1.0/<start><br/>"
        f"To get min, max and average temperature from a start to an end date. <b>Example: /api/v1.0/2016-08-23/2017-08-23</b> -----> /api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():

    # Calculate the most recent date in the db
    recent_date = session.query(func.max(measurement.date)).scalar()
    recent_date = dt.datetime.fromisoformat(str(recent_date))
    # Calculate the last 12 months from previous date
    last_year = recent_date - dt.timedelta(days=366)

    # Query to get the date and precipitation data
    data_query = session.query(measurement.date, measurement.prcp).\
    filter(measurement.date >= last_year).all()
    session.close()

    # Build a dictionary with the information previously retrieved
    precipitation_data = []
    for x in data_query:
        precipitation_dict = {}
        precipitation_dict["Date"] = x[0]
        precipitation_dict["Prcp (in)"] = x[1]
        precipitation_data.append(precipitation_dict)
    
    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():

    # Query to get all stations
    stations_query = session.query(measurement).group_by(measurement.station)
    session.close()

    stations = []
    for x in stations_query:  
        stations.append(x.station)

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    
    # Query the dates and temperature observations of the most-active station for the previous year of data.
    most_active_stations = session.query(measurement.station, func.count()).group_by(measurement.station).order_by(func.count().desc()).all()
    most_active_station = most_active_stations[0]
    station_name = most_active_station[0]

    # Using the most active station id. Query the last 12 months of temperature observation data for this station
    recent_station_date = session.query(func.max(measurement.date)).filter_by(station=station_name).scalar()
    recent_station_date = dt.datetime.fromisoformat(str(recent_station_date))
    last_station_year = recent_station_date - dt.timedelta(days=366)

    temperature_query = session.query(measurement.tobs).filter_by(station=station_name).filter(measurement.date >= last_station_year).all()
    session.close()

    temperature_data = []
    for x in temperature_query:
        temperature_data.append(x.tobs)

    return jsonify(temperature_data)

@app.route("/api/v1.0/<start>")
def metrics(start):

    # Minimum temperature, the average temperature, and the maximum temperature for a specified start
    min_temp = session.query(func.min(measurement.tobs)).filter(measurement.date >= start).scalar()
    max_temp = session.query(func.max(measurement.tobs)).filter(measurement.date >= start).scalar()
    avg_temp = session.query(func.avg(measurement.tobs)).filter(measurement.date >= start).scalar()
    session.close()

    metrics = {
        'Minimum temperature': min_temp,
        'Maximum temperature': max_temp,
        'Average temperature': round(avg_temp,4)
    }

    return jsonify(metrics)

@app.route("/api/v1.0/<start>/<end>")
def start_end_metrics(start, end):

    # Minimum temperature, the average temperature, and the maximum temperature for a specified start and end date
    min_temp = session.query(func.min(measurement.tobs)).filter(measurement.date >= start).filter(measurement.date <= end).scalar()
    max_temp = session.query(func.max(measurement.tobs)).filter(measurement.date >= start).filter(measurement.date <= end).scalar()
    avg_temp = session.query(func.avg(measurement.tobs)).filter(measurement.date >= start).filter(measurement.date <= end).scalar()
    session.close()

    metrics = {
        'Minimum temperature': min_temp,
        'Maximum temperature': max_temp,
        'Average temperature': round(avg_temp,4)
    }

    return jsonify(metrics)

if __name__ == '__main__':
    app.run(debug=True)