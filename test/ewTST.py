
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

sysStz=seisLib.sysStations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK','seismic.stationstst')#,'BRK0','BRK2','BRK3','BRK4'
cl = [('LK_BRK0', 'LK_BRK2'), ('LK_BRK1', 'LK_BRK2'), ('LK_BRK1', 'LK_BRK4'), ('LK_BRK3', 'LK_BRK4')]

tForce=UTCDateTime('2020-07-17 00:00:00')
tForceRaw=0
tForceHourly=0
tForceCluster=UTCDateTime('2020-07-17 00:00:00')
def rawProcess(sysStz,network,station):

    client = seisLib.drumPlot('/mnt/ide/seed/')
    client._alertTable='seismic.alertstst'
    client._amplAn = {
        'lowFW': [1, 20],
        'highFW': [20, 50],
        'lowFTh': 0.00001,
        'highFTh': 0.00001,
        'sft':1/60,
        'wnd':1/60
    }
    client._sysStations=sysStz

    scheduler=sch(client._amplAn['sft'],'',tForceRaw,client.getLastTime,(network,station))
    scheduler.schRun(client.amplitudeRawAn,(network,station))



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

    al._rateX = np.arange(0, 3700, 1)
    al._amplY = np.arange(0.01, -0.0001, -0.0001)
    al._thMatrix = np.zeros([len(al._amplY), len(al._rateX)])
    al._thMatrix[0:np.where(al._amplY > 0.0004)[0][-1], 5:] = 1
    al._thMatrix[0:np.where(al._amplY > 0.0008)[0][-1], 20:] = 2
    al._thMatrix[0:np.where(al._amplY > 0.002)[0][-1], 40:] = 3

    al._sysStations=sysStz
    l=log()
    scheduler=sch(al._rTh['sft'],'',tForceHourly,l.rdLog,("RAW_"+network+"_"+station,))
    scheduler.schRun(al.hourlyRateAmplitude,(network+'_'+station,type,))


def clusterProcess(sysStz,network,cl,type):



    al=seisLib.alert('seismic.alertstst')


    al._rateX = np.arange(0, 3700, 1)
    al._amplY = np.arange(0.01, -0.0001, -0.0001)
    al._thMatrix = np.zeros([len(al._amplY), len(al._rateX)])
    al._thMatrix[0:np.where(al._amplY > 0.0004)[0][-1], 5:] = 1
    al._thMatrix[0:np.where(al._amplY > 0.0008)[0][-1], 20:] = 2
    al._thMatrix[0:np.where(al._amplY > 0.002)[0][-1], 40:] = 3

    al._sysStations=sysStz
    l=log()
    scheduler=sch(al._rTh['sft'],'',tForceCluster,l.rdLogCluster,cl)
    scheduler.schRun(al.clusterAn,(cl,type,))


if __name__ == '__main__':

    #lancia raw amplitude analisys su tutte le stazioni
    # for st in sysStz._stations.keys():
    #     stName =sysStz._stations[st]._name
    #     multiprocessing.Process(target=rawProcess, name='RAW_'+st,
    #                             args=(sysStz,sysStz._network, stName)).start()
    # # lancia HR AML AMH amplitude analisys su tutte le stazioni
    # for st in sysStz._stations.keys():
    #     stName =sysStz._stations[st]._name
    #     multiprocessing.Process(target=hourlyProcess, name='HR_AML_'+st,
    #                             args=(sysStz,sysStz._network, stName,"AML")).start()
    for cls in cl:
        clName="__".join(cls)
        multiprocessing.Process(target=clusterProcess, name='CL_'+clName,
                                args=(sysStz,sysStz._network, cls,"HR_AML")).start()


    # pr1 = multiprocessing.Process(target=rawProcess, name='RAW_BRK1', args=(sysStz,))
    # pr1.start()

    # prCASP = multiprocessing.Process(target=rawProcessCASP, name='RAWCASP', args=(sysStz,))
    # prCASP.start()
    #
    #
    # pp = multiprocessing.Process(target=postProcess, name='PP', args=(sysStz,))
    # # pp.start()
    #
    # pc = multiprocessing.Process(target=postProcessCASP, name='PC', args=(sysStz,))
    # pc.start()

    sysStz.run('seismic.alarmstst')


    pr.join()
    # prCASP.join()
    # pp.join()
    # pc.join()