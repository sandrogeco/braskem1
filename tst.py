
# sudo /home/slarchive2.2/./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# /home/Documents/openVPNBraskem/openvpn --config clientBRASKEM__GEOAPP.conf

# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/

#da home/Dovuments/mSeedTest   /home/sandro/anaconda3/envs/mSeedTest/bin/python /home/sandro/Documents/mSeedTest/drumPlotHyst_1.4_utl.py

import time
import multiprocessing

from seisLib import drumPlot
import seisLib
import numpy as np

from obspy import  UTCDateTime

#stz=seisLib.stations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK')
sysStz=seisLib.sysStations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK','seismic.stationsTST')

print('pippo')
def rawProcess(sysStz):

    client = seisLib.drumPlot('/mnt/ide/seed/')

    client._alertTable='seismic.alerts'
    client._basePath = '/home/geoapp/'
    client._basePathRT = '/mnt/geoAppServer/'

    client._amplAn = {
        'lowFW': [1, 20],
        'highFW': [20, 50],
        'lowFTh': 0.00001,
        'highFTh': 0.00005

    }
    client._sysStations=sysStz
    #client.multiPr_run('LK', 'BRK?', 'E??' )
    #client.run('LK', 'BRK?', 'E??')
    while 1<2:
        time.sleep(10)
        print('rr')


def postProcess(sysStz):

    st=['LK_BRK0','LK_BRK1','LK_BRK2','LK_BRK3','LK_BRK4']
    cl=[('LK_BRK0','LK_BRK2'),('LK_BRK1','LK_BRK2'),('LK_BRK1','LK_BRK4'),('LK_BRK3','LK_BRK4')]


    al=seisLib.alert('seismic.alerts')


    al._th = {  # soglie su cui definire rate
        'AML': 0.00005,
        'AMH': 0.00005
    }
    al._rTh = {  # soglie rate
        'AML': 0,
        'AMH': 0,
        'wnd': 1,
        'sft': 0.25
    }
    al._clTh={
        'lag':3600
    }

    al._rateX=np.arange(0,100,1)
    al._amplY=np.arange(0.01,-0.0001,-0.0001)
    al._thMatrix=np.zeros([len(al._amplY),len(al._rateX)])
    al._thMatrix[0:np.where(al._amplY>0.0004)[0][-1],5:]=1
    al._thMatrix[0:np.where(al._amplY>0.0008)[0][-1],20:]=2
    al._thMatrix[0:np.where(al._amplY>0.002)[0][-1],40:]=3
    al._clusters=cl

    al._sysStations=sysStz
    #al.multiPr_HR_run(st)
    #al.HR_run(st)
    while 1<2:
        time.sleep(10)
        print('pp')


def t():
    while 1<2:
        time.sleep(10)


pr = multiprocessing.Process(target=rawProcess, name='RAW', args=(sysStz,))
pr.start()

pp = multiprocessing.Process(target=postProcess, name='PP', args=(sysStz,))
pp.start()

while 1<2:
    time.sleep(10)

pr.join()
pp.join()


