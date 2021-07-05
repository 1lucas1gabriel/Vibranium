import numpy as np

##################################################################
# MATH PROCESSING
##################################################################

def twos_complement(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits-1)):
        value -= 1 << bits
    return value


def extractData(rawData, scaleFactor):
    '''
    It extracts raw hexadecimal data and converts to G acceleration force.
    Default (sensitivity) scale factor: 16384 (2g).\n
    Scale factor options:
    16384 (2g), 8192 (4g), 4096 (8g), 2048 (16g)
    '''
    accels = dict()
    rawData = [line[:-4] for line in rawData]

    # divide each line into a list with samples
    rawData = [[line[0:12], line[12:24], line[24:36]] for line in rawData]
    flatRawData = [item for sublist in rawData for item in sublist]

    # delete empty spaces from list
    rawData = list(filter(None, flatRawData))
    
    # splits and convert each sample line to the respective acceleration axis
    accels["x"] = [twos_complement(value[0:4], 16) / scaleFactor for value in rawData]
    accels["y"] = [twos_complement(value[4:8], 16) / scaleFactor for value in rawData]
    accels["z"] = [twos_complement(value[8:12], 16)/ scaleFactor for value in rawData]
    return accels


def convertToNumpy(accelAxis):
  return np.array(accelAxis)


def mean(values):
  return np.mean(values)


def removeMean(accelAxis):
    return (accelAxis - np.mean(accelAxis))


def FFT(accelAxis, fa = 1000, N = 1024):
    '''
    fa: Sampling frequency [Hz]
    N:  Number of samples
    '''
    dt = 1/fa
    T = N*dt
    df = fa/N

    # time and frequency series
    f = np.arange(0,fa,df)

    # Fast Fourier Transform (abs term)
    FFTaxis = np.abs(np.fft.fft(accelAxis))
    return (FFTaxis, f)  


##################################################################
# FEATURES EXTRACTION
##################################################################

def rms(accelAxis):
  return np.sqrt(np.mean(accelAxis**2))


def crestFactor(accelAxis, rmsAxis):
  return np.max(np.abs(accelAxis))/rmsAxis


def topN_HighestAmps(FFT, f, N, Nsamples = 1024):
  '''
  Return a list of freqs and amps of TOP N Highest Amplitudes
  '''
  # Sort spectrum from max to min
  halfSpectrum = Nsamples//2
  sortedFFT = np.sort(FFT[:halfSpectrum])[::-1]

  freqs = []
  Amps  = []

  # Top N max
  for i in range(0,N):
    x = np.where(FFT[:halfSpectrum] == sortedFFT[i])
    freqs.append(float(f[x]))
    Amps.append(float(sortedFFT[i]))
  return freqs, Amps
