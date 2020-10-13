
# sudo /home/slarchive2.2/./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# /home/Documents/openVPNBraskem/openvpn --config clientBRASKEM__GEOAPP.conf

# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/

#da home/Dovuments/mSeedTest   /home/sandro/anaconda3/envs/mSeedTest/bin/python /home/sandro/Documents/mSeedTest/drumPlotHyst_1.4_utl.py

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
cl = [['LK_BRK0', 'LK_BRK2'], ['LK_BRK1', 'LK_BRK2'], ['LK_BRK1', 'LK_BRK4'], ['LK_BRK3', 'LK_BRK4']]

tForce=UTCDateTime('2020-07-17 00:00:00')
tForceRaw=0
tForceHourly=0
tForceCluster=0
tForceDrumPlot=UTCDateTime('2020-10-01 00:00:00')
tForceCASP=0
tForceHourlyCASP=0
tForceSara=0


def rawProcess(sysStz,network,station):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'
    client._amplAn = {
        'lowFW': [1, 20],
        'highFW': [20, 50],
        'lowFTh': 0.00001,
        'highFTh': 0.00001,
        'sft':1/60,
        'wnd':2/60
    }
    client._sysStations=sysStz

    # scheduler=sch(client._amplAn['sft'],'',tForceRaw,client.getLastTime,(network,station))
    # scheduler.schRun(client.amplitudeRawAn,(network,station))


p=[]
if __name__ == '__main__':


    # lancia raw amplitude analisys su tutte le stazioni

    pp=multiprocessing.Process(target=rawProcess, name='SARA',
                            args=(sysStz,sysStz._network, '*'))
    pp.start()
    p.append(pp)


    sysStz.run('seismic.alarmstst')

    for pp in p:
        pp.join()