import os
import pickle
import pandas as pd
import numpy as np
from random import randrange
from statistics import mean
from sklearn.svm import OneClassSVM


DIR = 'ML/models/'

####################################################################
# GENERAL FUNCTIONS # improve
####################################################################
def splitDataSet(rawData, features, frac):
    trainX = rawData[features].sample(frac=frac)
    crossX = rawData[features].drop(trainX.index)
    return (trainX, crossX)


######################################################################
def errorPerc(model, dataSet, falseValue):
    '''
    It calculates percentual error of a model under a Dataset
    '''
    ypred   = model.predict(dataSet)
    nfalse  = ypred[ypred == falseValue].size
    errorPerc = nfalse*100/ypred.size
    return round(errorPerc,3)


######################################################################
def fit_predict(dTrain, dCV, nParams, gParams):
    '''
    Fit and predict OCSVM model
    Return training and CV errors for each pair of hyperparams
    '''
    results = []
    for nuP in nParams:
        for gP in gParams:
            model = OneClassSVM(kernel='rbf',nu=nuP,gamma=gP)
            model.fit(dTrain)
            errorT  = errorPerc(model, dTrain, -1)
            errorCV = errorPerc(model, dCV, -1)  
            results.append((nuP, gP, errorT, errorCV))
    return results


######################################################################
def findMinimum(array):
    '''
    Return idx where error is minimum
    '''
    minimum_error = np.sort(array)[0]
    idx = np.where(array == minimum_error)[0]
    return idx


######################################################################
def selectBestParams(results):
    '''
    Get a set of results for each pair of hyperparams
    Return hyperparams from minimum CV errors
    [Note: More than 1 minimum CV error can be found] 
    '''
    results     = np.array(results)
    errorCV     = results[:,3]
    idx         = findMinimum(errorCV)
    
    #pairOfParams (array(n1, n_m), array(g1, g_m))
    pairOfParams = (results[idx,0], results[idx,1])
    return pairOfParams


######################################################################
def createNewParams(pairOfParams):
    '''
    Create hyperparams to (optimization) intensive area search
    '''
    createP = lambda p:np.linspace(p-(p*0.5),p+(p*0.5),3)

    # Creating hyperparams to intensive area search
    nParams = createP(pairOfParams[0]).reshape(-1)
    gParams = createP(pairOfParams[1]).reshape(-1)

    # Removing repeated elements
    nParams  = list(np.sort(np.unique(nParams)))
    gParams  = list(np.sort(np.unique(gParams)))
    return(nParams, gParams)

####################################################################
####################################################################


class ModelHandler():

    def __init__(self):
        self.model = None
        self.dataSetSize = 0

    def incrementDataSetSize(self):
        self.dataSetSize += 1


    def clearDataSetSize(self):
        self.dataSetSize = 0


    def lookFor(self, modelName):
        if os.path.isfile(DIR + modelName + 'x'):
            self.model = modelName
            return True  
        else:
            return False


    def getModel(self, axis):
        # open binary model in specific axis
        filename = DIR + self.model + axis
        return pickle.load(open(filename, 'rb'))
        

    def train(self, modelName):
        self.model = modelName
        try:
            raw = pd.read_csv("query.csv")

            # ONE MODEL FOR EACH AXIS eg. MT01x, MT01y, MT01z
            for axis in ('x','y','z'):
                features = [f'{axis}rms', f'{axis}cf']
                bestnus     = []
                bestgammas  = []

                for n in range(5):  
                    # split 80/20
                    (trainX, crossX) = splitDataSet(raw,features,0.8)

                    # BROAD AREA SEARCH
                    # Initial hyperparams (nu cannot be 0)
                    nuParams    = [0.01, 0.1, 0.3, 0.5, 0.7, 0.9]
                    gammaParams = [1, 5, 10, 50, 100]

                    # Results saves Training and CV errors for each pair of hyperparams
                    results     = fit_predict(trainX, crossX, nuParams, gammaParams)
                    bestParams  = selectBestParams(results)

                    # INTENSIVE AREA SEARCH
                    (nuParams, gammaParams) = createNewParams(bestParams)
                    results     = fit_predict(trainX, crossX, nuParams, gammaParams)
                    bestParams  = selectBestParams(results)

                    # Random choice of one the best pair of params
                    i = randrange(len(bestParams[0]))
                    bestnus.append(round(float(bestParams[0][i]), 3))
                    bestgammas.append(round(float(bestParams[1][i]), 3))
                    print(".", end='')

                ###########################################################
                # TRAINING WITH 5 BEST HYPERPARAMS
                ###########################################################                        
                nu      = mean(bestnus)
                gamma   = mean(bestgammas)
                (trainX, crossX)    = splitDataSet(raw,features,0.8)
                model = OneClassSVM(kernel='rbf',nu=nu,gamma=gamma)
                model.fit(trainX)

                filename = f"{modelName}" + axis
                print(filename)
                pickle.dump(model, open(DIR + filename, 'wb'))
            
        except Exception as e: print(e)


    def predict(self, values):
        # xrms xcf | yrms ycf | zrms zcf
        outlierDetected = False
        dictData = {'x': pd.DataFrame(values[3:5]).transpose(),
                    'y': pd.DataFrame(values[7:9]).transpose(),
                    'z': pd.DataFrame(values[11:13]).transpose()}

        for axis in ['x','y','z']:
            model = self.getModel(axis)
            healthyAxis = model.predict(dictData[axis])[0]
            # System is considered healthy if at least one axis prediction is normal (1)
            outlierDetected = False if healthyAxis == True else True
        return outlierDetected
       