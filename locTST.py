import time
from seisLib import drumPlot
from seisLib import log
import utm
import numpy as np
from obspy import UTCDateTime
import obspy.signal.polarization
import  matplotlib.pyplot as plt
import scipy.signal as sgn
from scipy.signal import hanning
from scipy.optimize import curve_fit
#import simplekml
import obspy.signal
import obspy.signal.cross_correlation
import obspy.signal.filter
import seisLib
import multiprocessing
plt.switch_backend('tKagg')







def loc(dstM,r,dec,e,lx,ly,lz):
    dst=np.zeros(dstM.shape,object)
    dst[:,:,:]=dstM[:,:,:]
    result = np.ones(dst.shape)*np.Inf
    le=np.sum(e)
    for i in np.arange(lx[0], lx[1], dec):
        for j in np.arange(ly[0], ly[1], dec):
            for k in np.arange(lz[0], lz[1], dec):
                p = r - dst[i, j, k]
                # p[e, :] = 0
                # p[:, e] = 0
                p=p*e
                # pp=p[0,:]
                result[i, j, k] = np.sqrt(np.trace(np.dot(p,p.T)))/le

    mm = np.unravel_index(np.argmin (result), result.shape)
    m = np.min(result)
    if dec==1:

        rr={
            'min':m,
            'mPos':mm

        }
        return rr
    else:
        sx=(lx[1]-lx[0])/4
        sy= (ly[1] - ly[0])/4
        sz = (lz[1] - lz[0])/4
        lx=[np.int(np.maximum(mm[0]-sx,0)),np.int(np.minimum(mm[0]+sx,dst.shape[0]))]
        ly = [np.int(np.maximum(mm[1] -sy, 0)), np.int(np.minimum(mm[1] +sy, dst.shape[1]))]
        lz = [np.int(np.maximum(mm[2] - sz, 0)), np.int(np.minimum(mm[2] + sz, dst.shape[2]))]
        dec=np.int(dec/2)
        return loc(dst,r,dec,e,lx,ly,lz)


def locOnGrid(a,tt):
        # aVol = loc(dst, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
        client = drumPlot('/mnt/ide/seed/')
        mm = a['mPos']
        m = a['min']
        x = grid[0, mm[0], mm[1], mm[2]]
        y = grid[1, mm[0], mm[1], mm[2]]
        z = grid[2, mm[0], mm[1], mm[2]]
        lat, lon = utm.to_latlon(x, y, 25, 'L')
        ttt=UTCDateTime(tt)

        ev = {
            'id': UTCDateTime(ttt).strftime("%m%d%H%M%S"),
            'time': UTCDateTime(ttt),

            'lat': lat,
            'lon': lon,
            'dpt': z/1000,
            'mag':1,
            'note':'error '+str(m)
        }
        client.pushIntEv(ev)

def SARALoc(r,e,t):
    if np.sum(e)>1:
        a=loc(dst, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
        locOnGrid(a,t)


def run(st):
    wnd=10
    sft=2
    l = log()
    te= l.rdLog('RUNACQ')
    tre={}
    ttr={}
    safetyTime=30
    cc = np.zeros([len(sysStz._stations), len(sysStz._stations)])
    ee=np.zeros([len(sysStz._stations), len(sysStz._stations)])
    rr= np.zeros([len(sysStz._stations), len(sysStz._stations)])

    while True:
        try:
            tr = sysStz._raw[0].copy()
            safeZoneL=np.max([tt.stats['starttime'] for tt in tr])+safetyTime
            safeZoneH=np.min([tt.stats['endtime'] for tt in tr]) - safetyTime
        except:
            time.sleep(1)
            continue

        if te < safeZoneL:
            te=safeZoneL
        if safeZoneH> te:
            sList =[sysStz._stations[s]._name for s  in sysStz._stations]
            tprv=tr.copy()
            tprv.filter('bandpass', freqmin=3, freqmax=10, corners=3, zerophase=True)
            print('XXXX')
            print(te)
            print(np.min([tt.stats['endtime'] for tt in tr]))
            print('****')
            for sName in sList:
                a=tr.select('*',sName,'','EHZ')[0].copy()
                b = tr.select('*', sName, '', 'EHZ')[0].copy()
                ttr[sName]=a
                ttr[sName].data= obspy.signal.filter.envelope(b.data)
                ttr[sName].filter('bandpass', freqmin=1, freqmax=10, corners=3, zerophase=True)
                # ttr[sName].trim(te-wnd,te)

            for s in range(0,len(sName)):
                for s1 in range(s+1,len(sName)):
                    ss=sList[s]
                    ss1=sList[s1]
                    c=obspy.signal.cross_correlation.correlate(ttr[ss],ttr[ss1],2*len(ttr[ss]))
                    cc[s, s1] =np.max(c)
                    ee[s,s1]=cc[s,s1]
                    rr[s,s1]=np.max(ttr[ss1].data)/np.max(ttr[ss].data)

            m=np.max(cc)
            print(m)
            if(m>0.75):
                ee[ee<0.75]=0
                ee[ee>=0.75]=1

                SARALoc(rr,ee,te)
            te=te+sft;
        else:
            time.sleep(1)



sysStz = seisLib.sysStations(['BRK0', 'BRK1', 'BRK2', 'BRK3', 'BRK4'], 'LK', 'seismic.stationsTST')


def clientAcq(sysStz):
    client = drumPlot('/mnt/ide/seed/')
    client._sysStations = sysStz
    client.runAcq(120,720*60)

pp = multiprocessing.Process(target=clientAcq, name='RUNACQ',args=(sysStz,))
pp.start()


data=np.load('metadata/dst.npz',allow_pickle=True)
dst=data['dst']
dsts=data['dsts']
grid=data['grid']
run(['BRK0', 'BRK1', 'BRK2', 'BRK3', 'BRK4'])


pp.join()

#
#         aVol = loc(dsts, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
#
#         mm = aVol['mPos']
#         ml = aVol['min']
#         x = grid[0, mm[0], mm[1], mm[2]]
#         y = grid[1, mm[0], mm[1], mm[2]]
#         z = grid[2, mm[0], mm[1], mm[2]]
#         lat, lon = utm.to_latlon(x, y, 25, 'L')
#         lat = lat + (np.random.rand() * 2 - 1) / 10000
#         lon = lon + (np.random.rand() * 2 - 1) / 10000
#         ttt = UTCDateTime(tt)
#
#         evl = {
#             'id': 'sup'+UTCDateTime(ttt).strftime("%m%d%H%M%S"),
#             'time': UTCDateTime(ttt),
#             # 'text': 'SWARM ev. mag' + str(pp[5]),
#             'lat': lat,
#             'lon': lon,
#             'dpt': z,
#             'mag':1,# np.log(np.max(np.asarray(vpp)) /th),
#             'note': 'SUPerror ' + str(ml)
#         }
#         if(ml<m):
#             client.pushIntEv(evl)
#         else:
#             client.pushIntEv(ev)
#     tt = tt + sft
#
#
