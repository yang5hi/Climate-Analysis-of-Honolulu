import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import calendar
from flask import Flask, jsonify
#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# Save reference to the table
Measurement = Base.classes.measurement
Station=Base.classes.station
#################################################
# Flask Setup
#################################################
app = Flask(__name__)
#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all the available routes."""
    return (
        f"Welcome to the Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation <br/>"
        f"/api/v1.0/stations <br/>"
        f"/api/v1.0/tobs <br/>"
        f"/api/v1.0/startdate <br/>"
        f"/api/v1.0/startdate/enddate<br/>"
    )

@app.route("/api/v1.0/precipitation")
def prcp():
    """Convert the query results to a dictionary using date as the key and prcp as the value."""
    """Return the JSON representation of your dictionary"""
    # Create the session (link) from Python to the DB
    session = Session(engine)
    # Query all date and precipitation values
    results = session.query(Measurement.date,Measurement.prcp).all()
    session.close()

    # Convert list of tuples into normal dictionary
    prcp_dict=dict(results)
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset"""
    # Create the session (link) from Python to the DB
    session = Session(engine)
    # Query all date and precipitation values
    results = session.query(Station.station).group_by(Station.station).all()
    session.close()

    # Convert list of tuples into normal list
    station_list=list(np.ravel(results))
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most active station for the last year of data."""
    """Return a JSON list of temperature observations (TOBS) for the previous year."""
     # Create the session (link) from Python to the DB
    session = Session(engine)

    # Design a query to find the most active stations 
    active_station=session.query(Measurement.station,func.count(Measurement.station)).\
            group_by (Measurement.station). order_by (func.count(Measurement.station).desc()).all()
    most_active_station=active_station[0][0]

    # Using the most active station id, Query the last 12 months of temperature observation data for this station 
    last_date=session.query(Measurement.date).\
            filter(Measurement.station==most_active_station).\
            order_by(Measurement.date.desc()).first()

    # Calculate the date one year from the last date in data set.
    year_no=int(last_date[0][0:4])
    month_no=int(last_date[0][5:7])
    date_no=int(last_date[0][8:])

    # check for leap year
    if calendar.isleap(year_no) and month_no==2 and date_no==29:
        year_ago=dt.datetime.strptime(last_date[0],'%Y-%m-%d').date()- dt.timedelta(days=366)
    else:
        year_ago=dt.datetime.strptime(f'{year_no-1}-{month_no}-{date_no}','%Y-%m-%d').date()
   
    # Query all date and temperature values
    temp_date=session.query(Measurement.date,Measurement.tobs).\
            filter((Measurement.station==most_active_station),(Measurement.date > year_ago)).all()
    session.close()

    # Convert list of tuples into normal list
    tobs_dict={most_active_station:dict(temp_date)}
    return jsonify(tobs_dict)

@app.route("/api/v1.0/<start_dt>/<end_dt>", strict_slashes=False)
@app.route("/api/v1.0/<start_dt>", defaults={'end_dt':''},strict_slashes=False)
def vacation(start_dt,end_dt):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    """When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date."""
    """When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."""
    # Create the session (link) from Python to the DB
    session = Session(engine)
    # Format the start date
    start_date=dt.datetime.strptime(start_dt,'%Y-%m-%d')

    # define end date based on route
    if end_dt=='':
        last_date=session.query(Measurement.date).order_by(Measurement.date.desc()).first()
        end_date=dt.datetime.strptime(last_date[0],'%Y-%m-%d').date()
    else:
        end_date=dt.datetime.strptime(end_dt,'%Y-%m-%d')

    # Query the result
    calc_temps=session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    session.close()
    
    # put result into dictionary
    temp_dict = {}
    temp_dict["TMIN"] = calc_temps[0][0]
    temp_dict["TAVG"] = calc_temps[0][1]
    temp_dict["TMAX"] = calc_temps[0][2]
  
    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run(debug=True)

