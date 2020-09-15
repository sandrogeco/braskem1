
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

# stz=seisLib.stations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK')
sysStz=seisLib.sysStations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK','seismic.stationsTST')
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
    client.run('LK', 'BRK?', 'E??')

def rawProcessCASP(sysStz):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alerts'
    client._sysStations=sysStz
    client._rTh = {
        'AML': 0,
        'AMH': 0,
        'CASP':0,
        'wnd': 1,
        'sft': 2/60
    }
    client.rtCASP()


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

    al.HR_run(st,['AML','AMH','CL'])


def postProcessCASP(sysStz):

    st=['LK_BRK0','LK_BRK1','LK_BRK2','LK_BRK3','LK_BRK4']

    al=seisLib.alert('seismic.alerts')

    al._th = {  # soglie su cui definire rate
        'AML': 0.00005,
        'AMH': 0.00005,
        'CASP':-100
    }
    al._rTh = {  # soglie rate
        'AML': 0,
        'AMH': 0,
        'CASP': 0,
        'wnd': 1,
        'sft': 0.25
    }

    al._rateX=np.arange(0,60,1)
    al._amplY=np.arange(3,-3,-0.1)

    al._thMatrix=np.zeros([len(al._amplY),len(al._rateX)])
    al._thMatrix[0:,5:]=1
    al._thMatrix[0:,20:]=2
    al._thMatrix[0:,40:]=3

    al._sysStations=sysStz
    al.HR_run(st,['CASP'])


if __name__ == '__main__':

    pr = multiprocessing.Process(target=rawProcess, name='RAW', args=(sysStz,))
    pr.start()

    prCASP = multiprocessing.Process(target=rawProcessCASP, name='RAWCASP', args=(sysStz,))
    prCASP.start()


    pp = multiprocessing.Process(target=postProcess, name='PP', args=(sysStz,))
    pp.start()

    pc = multiprocessing.Process(target=postProcessCASP, name='PC', args=(sysStz,))
    pc.start()

    sysStz.run()

    pr.join()
    prCASP.join()
    pp.join()
    pc.join()