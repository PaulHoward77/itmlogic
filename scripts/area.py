"""
Area prediction mode runner.

Written by Ed Oughton

November 2019

Original Matlab code implemented by Johnson and Yardim at OSU.

"""
import configparser
import os
import csv
import math
import numpy as np
from functools import partial

from itmlogic.qerfi import qerfi
from itmlogic.qlra import qlra
from itmlogic.lrprop import lrprop
from itmlogic.avar import avar
from terrain_module import terrain_area

# #set up file paths
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')


def itmlogic_area(tip):
    """
    Run itmlogic in area prediction mode.

    Parameters
    ----------
    tip : float
        Terrain irregularity parameter.

    Returns
    -------
    output : list of dicts
        Contains model output results.

    """
    prop = {}

    #Antenna height 1 (m), Antenna height 2 (m)
    prop['hg'] = [3.3, 1.3]

    #Frequency (MHz)
    prop['fmhz'] = 20

    #Terrain irregularity parameter dh (m)
    prop['dh'] = tip

    #Surface refractivity (N-units)
    prop['ens0'] = 301

    #Relative permittivity of ground
    prop['eps'] = 15

    #Conductivity (S/m) of ground
    prop['sgm'] = 0.001

    # Climate selection (1=equatorial, 2=continental subtropical, 3=maritime subtropical,
    # 4=desert, 5=continental temperate, 6=maritime temperate overland,
    # 7=maritime temperate, oversea (5 is the default)
    prop['klimx'] = 5

    #0 = horizontal polarization, 1 = vertical
    prop['ipol'] = 1

    #Mode of variability: Single Message=0, Accidental=1, Mobile=2, Broadcast=3
    prop['mdvarx'] = 3

    #Percent of time requested for computation
    QT = [50]

    #Percent of locations requested for computation
    QL = [50]

    #Confidence levels of computation
    QC = [50, 90, 10]

    #Initial distance (km) for loop over range
    D0 = 10

    #Max distance 1 (km) for loop over range
    D1 = 150

    #Increment 1 (km) for loop over range
    DS1 = 10

    #Max distance 2 (km) for coarser loop over range (starts beyond D1)
    D2 = 500

    #Increment 2 (km) for coarser loop over range
    DS2 = 50

    #Siting criterion for antenna 1, 0=random, 1= careful, 2= very careful
    KST = [2, 2]

    #Refractivity scaling ens=ens0*exp(-zsys/9460.);
    #(Average system elev above sea level)
    zsys = 0

    ZT = qerfi([x / 100 for x in QT])[0]
    ZL = qerfi([x / 100 for x in QL])[0]
    ZC = qerfi([x / 100 for x in QC])

    NC = len(QC)

    if (D0 <= 0):
        D0 = DS1
    if (D0 <= 0):
        D0= 2
    if (D1 <= D0) or (DS1 <= 0):
        ND = 1
        D1 = D0
    else:
        DS = DS1
        ND = math.floor((D1 - D0) / DS + 1.75)
        D1 = D0 + (ND - 1) * DS

    if (D2 <= D1 ) or ( DS2 <= 0):
        NDC = 0
    else:
        NDC = ND
        ND = math.floor((D2 - D1) / DS2 + 0.75)
        D2 = D1 + ND * DS2
        ND = NDC + ND

    prop['gma'] = 157E-9
    DB = 8.685890
    AKM = 1000

    prop['kwx'] = 0
    prop['wn'] = prop['fmhz'] / 47.7
    prop['ens']  = prop['ens0']

    if (zsys != 0):
        prop['ens'] = prop['ens'] * math.exp(-zsys / 9460)

    prop['gme']  = prop['gma'] * (1 - 0.04665 * math.exp(prop['ens'] / 179.3))

    # Initial value
    prop['lvar'] = 0

    zq = complex(prop['eps'], 376.62 * prop['sgm'] / prop['wn'])

    prop['zgnd'] = math.sqrt(zq.real - 1)

    if (prop['ipol'] != 0):
        prop['zgnd'] = prop['zgnd'] / zq

    prop = qlra(KST, prop)

    D = D0
    DT = DS
    FS = []
    DD = []

    output = []

    for JD in range(0, ND): #0-22

        prop['lvar'] = max(1, prop['lvar'])

        prop = lrprop(D * AKM, prop)

        FS.append(DB * np.log(2 * prop['wn'] * prop['dist']))
        DD.append(D)

        for JC in range(0, NC): #0-3
            confidence_level = QC[JC]

            avar1, prop = avar(ZT, ZL, ZC[JC], prop)

            output.append({
                'distance_km': D,
                'confidence_level_%': confidence_level,
                'propagation_loss_dB': FS[JD] + avar1
                })

        if JD + 1 == NDC:
            DT = DS2

        D = D + DT

    return output


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path.

    Parameters
    ----------
    data : list of dicts
        Data to be written.
    directory : string
        Folder to write the results to.
    filename : string
        Name of the file to write.

    """
    # Create path
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':

    dem_path = BASE_PATH
    directory = DATA_PROCESSED
    directory_shapes = os.path.join(DATA_PROCESSED, 'shapes')
    cell_range = 20000

    print('Getting Terrain Irregularity Parameter (delta h) (in meters)')
    #Terrain Irregularity Parameter delta h (in meters)
    tip = terrain_area(
        os.path.join(dem_path, 'ASTGTM2_N51W001_dem.tif'),
        -0.074916,
        51.424134,
        cell_range)
    print('TIP for AST DEM', tip)

    print('Running itmlogic')
    output = itmlogic_area(tip)

    print('Writing results to ', os.path.join(directory, 'uarea_output.csv'))
    csv_writer(output, directory, 'uarea_output.csv')

    tip = terrain_area(os.path.join(dem_path, 'S_AVE_DSM.vrt'), 26.9976, -3.5409, cell_range)
    print('TIP for ALOS DEM', tip)
    output = itmlogic_area(tip)
