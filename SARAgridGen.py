from seisLib import drumPlot
import utm
import numpy as np

client = drumPlot('/mnt/ide/seed/')
import  matplotlib.pyplot as plt
import scipy.signal as sgn
from scipy.signal import hanning
from scipy.optimize import curve_fit
plt.switch_backend('tKagg')

gridExt=1000

gridStep=25

gridDepth=2000
minGridDep=0

coord={
    'BRK0': client._inv.get_coordinates('LK.BRK0..EHZ'),
    'BRK1': client._inv.get_coordinates('LK.BRK1..EHZ'),
    'BRK2': client._inv.get_coordinates('LK.BRK2..EHZ'),
    'BRK3': client._inv.get_coordinates('LK.BRK3..EHZ'),
    'BRK4': client._inv.get_coordinates('LK.BRK4..EHZ'),
}

ns=len(coord)

utmCoord=[utm.from_latlon(coord[c]['latitude'],coord[c]['longitude']) for c in coord]
utmLats=[u[0] for u in utmCoord]
utmLons=[u[1] for u in utmCoord]
elev=[coord[c]['elevation'] for c in coord]

netBoundary={
    'latMin' : np.min(utmLats),
    'latMax' : np.max(utmLats),
    'lonMin' : np.min(utmLons),
    'lonMax' : np.min(utmLons)
}

gridBoundary={
    'latMin' : np.min(utmLats)-gridExt,
    'latMax' : np.max(utmLats)+gridExt,
    'lonMin' : np.min(utmLons)-gridExt,
    'lonMax' : np.max(utmLons)+gridExt
}

grid=np.mgrid[gridBoundary['latMin']:gridBoundary['latMax']:gridStep,
            gridBoundary['lonMin']:gridBoundary['lonMax']:gridStep,
            minGridDep:gridDepth:gridStep]


dst=np.zeros(grid.shape[1:],dtype=object)
dsts=np.zeros(grid.shape[1:],dtype=object)
dp=np.zeros(grid.shape[1:])


for i in np.arange(0, grid.shape[1]):
    for j in np.arange(0, grid.shape[2]):
        for k in np.arange(0, grid.shape[3]):
            print(str(i) + ' ' + str(j) + ' ' + str(k))
            r = np.zeros((ns, ns))
            rs = np.zeros((ns, ns))
            rs1 = np.zeros((ns, ns))
            for s in np.arange(0, ns):
                for s1 in np.arange(s + 1, ns):
                    d = np.sqrt((grid[0, i, j, k] - utmLats[s]) ** 2 + (grid[1, i, j, k] - utmLons[s]) ** 2 + (
                                grid[2, i, j, k] - elev[s]) ** 2)
                    d1 = np.sqrt((grid[0, i, j, k] - utmLats[s1]) ** 2 + (grid[1, i, j, k] - utmLons[s1]) ** 2 + (
                            grid[2, i, j, k] - elev[s1]) ** 2)
                    r[s, s1] = (d / d1)
                    rs[s, s1] = np.sqrt(d / d1)
            dst[i, j, k] = r
            dsts[i, j, k] = rs
np.savez('metadata/dst',dst=dst,dsts=dsts,grid=grid)
print ('p')
