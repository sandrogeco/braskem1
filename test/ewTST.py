
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

tForce=UTCDateTime('2020-07-17 00:00:00')
tForceRaw=UTCDateTime('2020-11-12 06:16:00')
tForceHourly=0
tForceCluster=0
tForceDrumPlot=UTCDateTime('2020-10-01 00:00:00')
tForceCASP=0
tForceHourlyCASP=0


try:
    with urllib.request.urlopen("http://worldtimeapi.org/api/timezone/America/Maceio") as url:
        data = json.loads(url.read().decode())
        localTimeOffset=np.int(data['dst_offset'])+np.int(data['raw_offset'])
except:
    pass

def rawCASP(sysStz):
    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'
    client._rTh={
        'CASP': 2,
        'wnd': 2/60,
        'sft': 1/60,
        'alON':10/60
    }
    client._sysStations=sysStz

    scheduler=sch(client._rTh['sft'],'',tForceCASP,UTCDateTime.now)
    scheduler.schRun(client.rawCASP,[])


def hourlyCASP(sysStz,network,station):
    al=seisLib.alert('seismic.alertstst')

    al._th = {  # soglie su cui definire rate
        'CASP': -100
    }
    al._rTh = {  # soglie rate
        'CASP':0,
        'wnd': 1,
        'sft': 0.25
    }

    al._rateX = np.arange(0, 60, 1)
    al._amplY = np.arange(3, -3, -0.1)
    al._thMatrix = np.zeros([len(al._amplY), len(al._rateX)])
    al._thMatrix[0:, 5:] = 1
    al._thMatrix[0:, 20:] = 2
    al._thMatrix[0:, 40:] = 3

    al._sysStations=sysStz
    l=log()
    scheduler=sch(al._rTh['sft'],'',tForceHourlyCASP,l.rdLog,("RAW_CASP",))
    scheduler.schRun(al.hourlyRateMag,(station,'CASP',))


def rawProcess(sysStz,network,station):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'
    client._amplAn = {
        'lowFW': [1, 20],
        'highFW': [20, 50],
        'lowFTh': 0.00003,
        'highFTh': 0.00003,
        'sft':1/60,
        'wnd':1/60
    }
    client._sysStations=sysStz

    scheduler=sch(client._amplAn['sft'],'',tForceRaw,client.getLastTime,(network,station))
    scheduler.schRun(client.amplitudeRawAn,(network,station))


def rtDrum(sysStz,network,station):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'

    client._band = {
        'low': [1, 20],
        'high': [20, 50]
    }

    client._rTWindow = 360
    client._rtSft = 2/60

    client._basePathRT ='/home/geoapp/RT'

    client._sysStations=sysStz
    client._localTimeOffset=localTimeOffset
    scheduler=sch(client._rtSft,'',UTCDateTime.now(),UTCDateTime.now)
    scheduler.schRun(client.singleStationRealTimeDrumPlot,(network,station))


def hyDrum(sysStz, network, station):
    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable = 'seismic.alertstst'

    client._band = {
        'low': [1, 20],
        'high': [20, 50]
    }

    client._hystType = [360, 180, 60]

    client._rTWindow = 360
    client._rtSft = 2

    client._basePath = '/home/geoapp/new'

    client._sysStations = sysStz
    client._localTimeOffset = localTimeOffset
    scheduler=sch(1,'',tForceDrumPlot,UTCDateTime.now)
    scheduler.schRun(client.singleStationHystDrumPlot,(network,station))



def hourlyProcess(sysStz,network,station,type):

    al=seisLib.alert('seismic.alertstst')

    al._th = {  # soglie su cui definire rate
        'AML': 0.00001,
        'AMH': 0.00001
    }
    al._rTh = {  # soglie rate
        'AML': 0,
        'AMH': 0,
        'wnd': 1,
        'sft': 0.25
    }
    #
    # al._rateX = np.arange(0, 3700, 1)
    # al._amplY = np.arange(0.01, -0.0001, -0.0001)
    # al._thMatrix = np.zeros([len(al._amplY), len(al._rateX)])
    # al._thMatrix[0:np.where(al._amplY > 0.0004)[0][-1], 5:] = 1
    # al._thMatrix[0:np.where(al._amplY > 0.0008)[0][-1], 20:] = 2
    # al._thMatrix[0:np.where(al._amplY > 0.002)[0][-1], 40:] = 3
    #
    #

    al._sysStations=sysStz
    l=log()
    scheduler=sch(al._rTh['sft'],'',tForceHourly,l.rdLog,("RAW_"+network+"_"+station,))
    scheduler.schRun(al.hourlyRateAmplitude,(network+'_'+station,type,))


def clusterProcess(sysStz,network,cl,type):



    al=seisLib.alert('seismic.alertstst')


    al._rateX = np.arange(0, 3700, 1)
    al._amplY = np.arange(0.00020, -0.0001, -0.00001)
    al._thMatrix = np.zeros([len(al._amplY), len(al._rateX)])
    al._thMatrix[0:np.where(al._amplY > 0.00003)[0][-1], 900:] = 1
    al._thMatrix[0:np.where(al._amplY > 0.00006)[0][-1], 1800:] = 2
    al._thMatrix[0:np.where(al._amplY > 0.00012)[0][-1], 2700:] = 3
    # al._thMatrix[0:np.where(al._amplY > 0.00001)[0][-1], 1:] = 1
    # al._thMatrix[0:np.where(al._amplY > 0.00004)[0][-1], 2:] = 2
    # al._thMatrix[0:np.where(al._amplY > 0.00005)[0][-1], 30:] = 3

    al._sysStations=sysStz
    l=log()
    clh=["HR_AML_"+c for c in cl]
    scheduler=sch(al._rTh['sft'],'',tForceCluster,l.rdLogCluster,clh)
    scheduler.schRun(al.clusterAn,(cl,type,))


def coiProcess(sysStz,network,stations,channel,wnd,sft,trigPar):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'

    client._sysStations=sysStz

    scheduler=sch(sft,'',tForceRaw,UTCDateTime.now)
    scheduler.schRun(client.coincedenceSTALTA,(network,stations,channel,wnd,trigPar))



p=[]
if __name__ == '__main__':


    trigPar={
        'thOn':2.5,
        'thOff':0.5,
        'nSt':3,
        'sta':1,
        'lta':30,
        'lowF':3,
        'highF':12}
    pp = multiprocessing.Process(target=coiProcess, name='STALTA1',
                                 args=(sysStz,'LK','BRK?','EHZ',150,120/3600,trigPar))
    pp.start()
    p.append(pp)



    sysStz.run('seismic.alarmstst')

    for pp in p:
        pp.join()


#casp h rate
#casp mag OK
#latency OK
#cluster alert
