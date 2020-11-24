import time
import multiprocessing

from seisLib import drumPlot
import seisLib
import numpy as np
from sch import log
from sch import sch
from obspy import UTCDateTime
import urllib
import json



sysStz=seisLib.sysStations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK','seismic.stationstst')#,'BRK0','BRK2','BRK3','BRK4'
cl = [['LK_BRK3', 'LK_BRK4'],['LK_BRK0', 'LK_BRK2'], ['LK_BRK1', 'LK_BRK2'], ['LK_BRK1', 'LK_BRK4']]

client = seisLib.drumPlot('/mnt/ide/seed/')
client._alertTable = 'seismic.alertstst'
client._amplAn = {
    'lowFW': [1, 20],
    'highFW': [20, 50],
    'lowFTh': 0.00003,
    'highFTh': 0.00003,
    'sft': 1 / 60,
    'wnd': 1 / 60
}
client._sysStations = sysStz
data = np.load('../metadata/dst.npz', allow_pickle=True)
dst = data['dst']
dsts = data['dsts']
grid = data['grid']



t=['2020-11-20 10:00:00',
   '2020-11-20 10:30:00']

p=[[0.21,2.82,0.83,0.79,1.5],
   [0.53,1.75,0.79,0.79,1.24]]


aa=np.zeros((5,5))
g=np.ones((5,5))
k=0
for pp in p:
    for i in range(0,5):
        for j in range(i+1,5):
            aa[i,j]=pp[j]/pp[i]

    client.SARALoc(aa,g,t[k],1,dst)
    k+=1


