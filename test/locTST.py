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
from matplotlib.colors import Normalize, LogNorm, NoNorm
#import signal
from scipy import signal
import xwt

from skimage import  data, filters, measure, morphology

def rmsEnvelope(data,wnd):
    t=0
    ld=len(data)
    r=np.zeros(ld)
    data1=np.zeros((np.int(ld/wnd)+1)*wnd)
    data1[0:len(data)]=data[0:]
    while t<=len(data)-wnd:
        r[t]=np.sqrt(np.sum(data1[t:t+wnd]**2))/wnd
        t+=1
    return r




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


def plottst(total_duration, sampling_frequency):
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1)
    ax1.set_xlim(0, total_duration)
    ax1.set_xlabel('time (s)')
    ax1.grid(True)
    ax2.set_xlim(0, total_duration)
    ax2.set_ylim(2.0 / total_duration, 0.5 * sampling_frequency)
    ax2.set_xlabel('time (s)')
    ax2.set_ylabel('frequency (Hz)');
    ax2.grid(True)

    # xwt.spectrogram_plot(mm, times, frequencies, coif, 0.0, cmap='jet', norm=LogNorm(), ax=ax3)
    ax3.set_xlim(0, total_duration)
    ax3.set_ylim(2.0 / total_duration, 0.5 * sampling_frequency)
    ax3.set_xlabel('time (s)')
    ax3.set_ylabel('frequency (Hz)');
    ax3.grid(True)
    ax4.set_xlim(0, total_duration)
    ax4.set_ylim(2.0 / total_duration, 0.5 * sampling_frequency)
    ax4.set_xlabel('time (s)')
    ax4.set_ylabel('frequency (Hz)');
    ax4.grid(True)
    return ax1, ax2, ax3, ax4


def run(tStart,tEnd,cth = 0.95,minDur = 1,overLap=10,dec=10):

    client = drumPlot('/mnt/ide/seed/')

    tr = client.get_waveforms('LK', 'BRK?', '', 'EHZ', tStart - overLap, tEnd + overLap)
    tr.merge()
    nts=len(tr)
    tr.remove_response(client._inv)
    tr.filter('bandpass', freqmin=0.5, freqmax=20, corners=3, zerophase=True)
    ttr=tr.copy()
    i=0
    for trace in tr:
        ttr[i].data= obspy.signal.filter.envelope(trace.data)
        i+=1
    ttr.decimate(dec)
    sampling_frequency = ttr[0].stats['sampling_rate']
    # sampling_frequency = sampling_frequency / dec
    n_samples = ttr[0].stats['npts']
    total_duration = n_samples / sampling_frequency
    sample_times = np.linspace(0, total_duration, n_samples)
    tFlt = minDur * sampling_frequency
    ax1, ax2, ax3, ax4 = plottst(total_duration,sampling_frequency)
    for i in range(0,nts):
        for j in range(i+1,nts):
            print(ttr[i])
            print(ttr[j])
            coherence, s1, s2, times, frequencies, coif = xwt.xwt_coherence(ttr[i].data, ttr[j].data, sampling_frequency, 12,
                                                                            True, False)

            ch = coherence.copy()
            ch[ch > cth] = 1
            ch[ch <= cth] = 0
            ch[frequencies < 0.5, :]=0
            mm = measure.label(ch, connectivity=2)
            rp = measure.regionprops(mm)
            c = []

            for r in rp:
                if np.abs(r.bbox[2] - r.bbox[0]) < tFlt:
                    mm[mm == r.label] = 0
                else:
                    c.append(r.centroid)

            ax1.plot(sample_times, ttr[i], color='b');
            ax1.plot(sample_times, ttr[j], color='r');
            xwt.spectrogram_plot(coherence, times, frequencies, coif, cth, cmap='jet', norm=LogNorm(), ax=ax2)
            plt.show()
            print(i)

    #
    # cc = np.zeros([len(sysStz._stations), len(sysStz._stations)])
    # ee=np.zeros([len(sysStz._stations), len(sysStz._stations)])
    # rr= np.zeros([len(sysStz._stations), len(sysStz._stations)])
    #
    # while True:
    #     try:
    #         tr = sysStz._raw[0].copy()
    #         safeZoneL=np.max([tt.stats['starttime'] for tt in tr])+safetyTime
    #         safeZoneH=np.min([tt.stats['endtime'] for tt in tr]) - safetyTime
    #     except:
    #         time.sleep(1)
    #         continue
    #
    #     if te < safeZoneL:
    #         te=safeZoneL
    #     if safeZoneH> te:
    #         sList =[sysStz._stations[s]._name for s  in sysStz._stations]
    #         tprv=tr.copy()
    #         tprv.filter('bandpass', freqmin=3, freqmax=10, corners=3, zerophase=True)
    #         print('XXXX')
    #         print(te)
    #         print(np.min([tt.stats['endtime'] for tt in tr]))
    #         print('****')
    #         for sName in sList:
    #             a=tr.select('*',sName,'','EHZ')[0].copy()
    #             b = tr.select('*', sName, '', 'EHZ')[0].copy()
    #             b.filter('bandpass', freqmin=3, freqmax=12, corners=3, zerophase=True)
    #             ttr[sName]=a
    #             #ttr[sName].data= obspy.signal.filter.envelope(b.data)
    #             ttr[sName].data=rmsEnvelope(b.data,50)
    #
    #         [ttr[n].trim(te-wnd,te) for n in ttr.keys()]
    #
    #         for s in range(0,len(sName)):
    #             for s1 in range(s+1,len(sName)):
    #                 ss=sList[s]
    #                 ss1=sList[s1]
    #                 c=obspy.signal.cross_correlation.correlate(ttr[ss],ttr[ss1],2*len(ttr[ss]))
    #                 cc[s, s1] =np.max(c)
    #                 ee[s,s1]=cc[s,s1]
    #                 rr[s,s1]=np.max(ttr[ss1].data)/np.max(ttr[ss].data)
    #
    #         m=np.max(cc)
    #         print(m)
    #         if(m>0.75):
    #             ee[ee<0.75]=0
    #             ee[ee>=0.75]=1
    #
    #             SARALoc(rr,ee,te)
    #         te=te+sft;
    #     else:
    #         time.sleep(1)
    #


data=np.load('metadata/dst.npz',allow_pickle=True)
dst=data['dst']
dsts=data['dsts']
grid=data['grid']
ts=UTCDateTime('2020-09-19 15:00:30')


run(ts,ts+120,0.95,1,0)


