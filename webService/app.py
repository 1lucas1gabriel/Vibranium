'''
@1lucas1gabriel - JUN/21

WebService para disponibilizar recursos de monitoramento e 
Machine Learning para detecao de vibracao anomala de motores eletricos.
'''

from flask import Flask, request, abort, jsonify, make_response
from flask_cors import CORS
from database import db
from ML import ML

MH = ML.ModelHandler()
app = Flask(__name__)
CORS(app)


#######################################################################
# EQUIPMENTS
#######################################################################
# ID: MT01
@app.route("/v1/equipments/<ID>", methods=["GET", "PUT", "POST", "OPTIONS"])
def handleEQP(ID):

    results = db.querySelectAllFrom("equipment", "equipID", ID)
    if not results:
        abort(404)

    if request.method == "GET":
        return jsonify(results)

    # DEAL WITH CORS PRE-FLIGHT REQUEST -> REQUIRED FOR THE GRAFANA BUTTON PLUGIN
    ##################################################################
    elif request.method == "OPTIONS":
        return _corsify(make_response())
      
    elif request.method == "PUT" or request.method == "POST":
        if not request.json:
            abort(400)

        # template for each key in request.json | results is a list of dicts
        for field in results[0]:
            if field in request.json:
                newValue = request.json[field]
                OKstatus = db.queryUpdate("equipment", field, newValue, "equipID", ID)
                if not OKstatus: 
                    abort(400)

        response = jsonify({"OK": 200})         
        return _corsify(response)
    ##################################################################


#######################################################################
# STATIONS
#######################################################################
# ID: 24F5AA66106E 
@app.route("/v1/stations/<ID>", methods=["GET", "PUT"])
def handleGAT(ID):

    results = db.querySelectAllFrom("station", "macStationID", ID)
    if not results:
        abort(404)

    if request.method == "GET":
        return jsonify(results)
        
    else:
        if not request.json:
            abort(400)

        # template for each key in request.json | results is a list of dicts
        for field in results[0]:
            if field in request.json:
                newValue = request.json[field]
                OKstatus = db.queryUpdate("station", field, newValue, "macStationID", ID)
                if not OKstatus: 
                    abort(400) 
        return {"OK": 200}


#######################################################################
# ENDPOINTS
#######################################################################
# ID: C8DF8434ADC0
@app.route("/v1/endpoints/<ID>", methods=["GET", "PUT"])
def handleEND(ID):

    results = db.querySelectAllFrom("endpoint", "macID", ID)
    if not results:
        abort(404)

    if request.method == "GET":
        return jsonify(results)
        
    else:
        if not request.json:
            abort(400)

        # template for each key in request.json | results is a list of dicts
        for field in results[0]:
            if field in request.json:
                newValue = request.json[field]
                OKstatus = db.queryUpdate("endpoint", field, newValue, "macID", ID)
                if not OKstatus: 
                    abort(400) 
        return {"OK": 200}


@app.route("/v1/endpoints/<ID>/acquisition", methods = ["GET", "POST"])
def handleACQ(ID):

    results = db.querySelectAllFrom("endpoint", "macID", ID)
    if not results:
        abort(404)
    
    # POST REQUEST
    if (request.method == "POST"):        
        if not request.json:
            abort(400)

        (acqFields, acqValues) = db.extractJsonAcq(request.json)
        equipID = request.json['equipID']
        equip = db.querySelectAllFrom("equipment", "equipID", equipID)
        print(acqValues)

        ##################################################################
        # CREATING A DATASET - EQUIPMENT IN TRAINING
        ##################################################################
        if (equip[0]['InTraining'] == True):
            db.queryInsertInto("acquisition", acqFields, acqValues)
            MH.incrementDataSetSize()

            if(MH.dataSetSize == 400):            #CHANGE DATASETSIZE HERE !!!!
                # create a csvfile to train the model
                db.makeCSVfile("acquisition", "endpointID", ID, MH.dataSetSize)
                MH.train(f"{equipID}")
                MH.clearDataSetSize()

                # After trained: InTraining is false
                db.queryUpdate("equipment", "InTraining", False, "equipID", equipID)
            return {"OK": 200}

        else:
            equipModeled = MH.lookFor(f"{equipID}")
            ##################################################################
            # PREDICT ANOMALY
            ##################################################################
            if(equipModeled):
                prediction = MH.predict(acqValues)

                # SET ANOMALY prediction
                acqValues[1] = prediction
                print(prediction)
                db.queryInsertInto("acquisition", acqFields, acqValues)
                return {"OK": 200}  

            ##################################################################
            # IF THE TRAINING WAS NEVER ACTIVATED - MONITORING ONLY
            ##################################################################
            else:
                db.queryInsertInto("acquisition", acqFields, acqValues)
                return {"OK": 200} 
                 
    # GET REQUEST
    else:
        # return the last acquisition from an endpoint
        lastAcq = db.querySelectLastFrom("acquisition", "acqID", "endpointID", ID)
        return jsonify(lastAcq)


#######################################################################
# ENDPOINTS
#######################################################################
@app.route("/")
def index():
    return "<h1>Welcome to VibraniumSystem!</h1>"


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


def _corsify(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


if __name__ == "__main__":
    app.run()
