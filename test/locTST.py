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


def locOnGrid(a,tt,mag):
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
            'mag':mag,
            'note':'error '+str(m)
        }
        client.pushIntEv(ev)

def SARALoc(r,e,t,mag):

    a=loc(dst, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
    locOnGrid(a,t,mag)


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

def pick(tStart,tEnd,p,a,overLap=10,dec=10):

    client = drumPlot('/mnt/ide/seed/')

    tr = client.get_waveforms('LK', 'BRK?', '', 'EHZ', tStart - overLap, tEnd + overLap)
    tr.merge()
    nts=len(tr)
    tr.remove_response(client._inv)
    tr.filter('bandpass', freqmin=1, freqmax=8, corners=3, zerophase=True)
    ttr=tr.copy()
    ttrEnv=tr.copy()
    i=0
    for trace in tr:
        ttrEnv[i].data= obspy.signal.filter.envelope(trace.data)
        ttr[i].data=trace.data
        i+=1
    ttr.decimate(dec)
    sampling_frequency = ttr[0].stats['sampling_rate']
    # sampling_frequency = sampling_frequency / dec
    n_samples = ttr[0].stats['npts']
    total_duration = n_samples / sampling_frequency
    sample_times = np.linspace(0, total_duration, n_samples)
    ttr=tr.copy()
    ttrEnv=tr.copy()
    i=0
    for trace in tr:
        ttrEnv[i].data= obspy.signal.filter.envelope(trace.data)
        ttr[i].data=trace.data

        i+=1
    ttr.decimate(dec)
    sampling_frequency = ttr[0].stats['sampling_rate']
    # sampling_frequency = sampling_frequency / dec
    n_samples = ttr[0].stats['npts']
    total_duration = n_samples / sampling_frequency
    sample_times = np.linspace(0, total_duration, n_samples)
    ttrEnv.plot()

def cal(p,a):
    client = drumPlot('/mnt/ide/seed/')


    coord={
        'BRK0': client._inv.get_coordinates('LK.BRK0..EHZ'),
        'BRK1': client._inv.get_coordinates('LK.BRK1..EHZ'),
        'BRK2': client._inv.get_coordinates('LK.BRK2..EHZ'),
        'BRK3': client._inv.get_coordinates('LK.BRK3..EHZ'),
        'BRK4': client._inv.get_coordinates('LK.BRK4..EHZ'),
    }
    nts=len(coord)

    utmCoord=[utm.from_latlon(coord[c]['latitude'],coord[c]['longitude']) for c in coord]
    utmLats=[u[0] for u in utmCoord]
    utmLons=[u[1] for u in utmCoord]
    elev=[coord[c]['elevation'] for c in coord]

    d=[]
    c=[]
    for i in range(0,nts):
       d.append(np.sqrt((utmLats[i]-p['latitude'])**2+(utmLons[i]-p['longitude'])**2))

    u = np.zeros((nts))
    u[0]=1

    for i in range(1, nts):
        u[i]=d[0]*a[0]/(d[i]*a[i])
    return u,d

def run(c,tStart,tEnd,cth = 0.95,minDur = 0.5,overLap=10,dec=10):

    client = drumPlot('/mnt/ide/seed/')

    tr = client.get_waveforms('LK', 'BRK?', '', 'EHZ', tStart - overLap, tEnd + overLap)
    tr.merge()
    nts=len(tr)
    tr.remove_response(client._inv)
    tr.filter('bandpass', freqmin=1, freqmax=15, corners=3, zerophase=True)
    ttr=tr.copy()
    ttrEnv=tr.copy()
    i=0
    for trace in tr:
        ttr[i].data=trace.data*c[i]
        i+=1
    ttr.decimate(dec)
    sampling_frequency = ttr[0].stats['sampling_rate']
    # sampling_frequency = sampling_frequency / dec
    n_samples = ttr[0].stats['npts']
    total_duration = n_samples / sampling_frequency
    sample_times = np.linspace(0, total_duration, n_samples)
    tFlt = minDur * sampling_frequency
    ax1, ax2, ax3, ax4 = plottst(total_duration,sampling_frequency)
    mm=np.zeros((nts,nts),dtype=object)
    ch=mm.copy()
    coherence=mm.copy()
    s1=np.zeros((nts),dtype=object)
    s2 = np.zeros((nts), dtype=object)
    mmBool=mm.copy()

    nts2=((nts*nts)-nts)/2
    coupleTh=3 #nts2/2
    for i in range(0,nts):
        for j in range(i+1,nts):
            ax1.clear()
            ax2.clear()
            ax3.clear()
            ax4.clear()

            print(ttr[i])
            print(ttr[j])
            coherence[i,j], s1[i], s2[j], times, frequencies, coif = xwt.xwt_coherence(ttr[i].data, ttr[j].data, sampling_frequency, 12,
                                                                            True, False,'cmorl15.0-1.0')

            c=coherence[i,j].copy()
            # c[c > cth] = 1
            c[c <= cth] = np.nan
            c[frequencies < 2, :] = np.nan
            c[:,0:100]=np.nan
            c[:,len(times)-100:]=np.nan
            ch[i,j] = c

            s1[i][frequencies < 2, :] = np.nan
            s2[j][frequencies < 2, :] = np.nan

    a = [ch[i, j] for i in range(0, nts) for j in range(i + 1, nts)]
    a[0]=s1[0]
    a[1:]=s2[1:]
    a=np.asarray(a)
    # s=np.sum(ch)/nts2
    s=np.nanmax(a,axis=0)


    # s[s > cth] = 1
    # s[s <= cth] = 0
    s[s<1e-12]=0
    s[s >= 1e-12] = 1

    meas = measure.label(s, connectivity=2)
    rp = measure.regionprops(meas)
    c=[]
    for r in rp:
        if np.abs(r.bbox[2] - r.bbox[0]) < tFlt:
            meas[meas== r.label] = 0
        # else:
        #     c.append([np.int(x) for x in r.centroid])

    measF = measure.label(meas, connectivity=2)
    rpF = measure.regionprops(measF)
    # xwt.spectrogram_plot(meas, times, frequencies, coif, cth, cmap='jet', norm=LogNorm(), ax=ax4)

    ratios=[]
    eList=[]

    for region in rpF:
        r=np.zeros((nts,nts))
        e=np.zeros((nts,nts))
        p = np.zeros((nts))*np.nan
        cc=region.centroid
        # measTst=measF.copy()
        # measTst[measF!=region.label]=0
        # ax1.clear()
        # xwt.spectrogram_plot(measTst, times, frequencies, coif, 0, cmap='jet', norm=LogNorm(), ax=ax1)

        for i in range(0, nts):
            for j in range(i + 1, nts):
                siMean=np.nanmax([s1[i][co[0],co[1]] for co in region.coords])
                sjMean = np.nanmax([s2[j][co[0], co[1]] for co in region.coords])
                chMean=np.nanmax([ch[i,j][co[0],co[1]] for co in region.coords])
                r[i, j] = sjMean/siMean
                e[i,j]=(siMean>1e-12)and (sjMean>1e-12)#np.round(chMean)
                p[i]=siMean
                # r[i,j]=np.sqrt(s2[j][cc[0],cc[1]]/s1[i][cc[0],cc[1]])
                # e[i,j]=np.round(ch[i,j][cc[0],cc[1]])
        p[-1]=sjMean
        e1=np.nansum(e,axis=1)
        e2=np.nansum(e,axis=0)
        e3=e1+e2
        e3[e3<1]=np.nan
        e3[e3>=1]=1
        mag=np.nanmax(e3*p)
        if (np.nansum(e)>=coupleTh) and (mag>5*1e-13):
            print(str(frequencies[np.int(cc[0])])+' '+str(ts+times[np.int(cc[1])]))
            print(r)
            print(e)
            # input()
            e[e!=1]=0
            SARALoc(r, e, ts+times[np.int(cc[1])],mag)
        ratios.append(r)
        eList.append(e)
    plt.show()
    print('p')



            # for r in rp:
            #     if np.abs(r.bbox[2] - r.bbox[0]) < tFlt:
            #         mm[i,j][mm[i,j] == r.label] = 0
            #     else:
            #
            #         c.append(r.centroid)

    ax1.plot(sample_times, ttr[i], color='b');
    ax1.plot(sample_times, ttr[j], color='r');
    xwt.spectrogram_plot(coherence, times, frequencies, coif, cth, cmap='jet', norm=LogNorm(), ax=ax2)
    xwt.spectrogram_plot(mm[i, j], times, frequencies, coif, cth, cmap='jet', norm=LogNorm(), ax=ax3)



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

ts=UTCDateTime('2020-09-04 13:09:00')

ts=UTCDateTime('2020-10-13 23:59:00')

ts=UTCDateTime('2020-09-17 16:10:00')

ts=UTCDateTime('2020-10-05 13:42:00')

ts=UTCDateTime('2020-09-21 13:23:00')

ts=UTCDateTime('2020-09-25 16:09:00')#p3


ts=UTCDateTime('2020-09-19 15:00:00')#p1



ts=UTCDateTime('2020-09-21 16:28:00')#p2

#run(ts,ts+180,0.9,0.1,0,10)

p1={
    'longitude':8933494.93,
    'latitude':198419.039
}
p2={
    'longitude':8933115.00,
    'latitude':198629.00
}

p3={
    'longitude':8934119.40,
    'latitude':198330.86
}

ampl1=[5e-5,5e-5,0.00015,2.7e-5,2.7e-5]
ampl3=[1e-5,4e-5,1.2e-5,5.5e-5,0.000128]
u,d=cal(p1,ampl1)
u3,d3=cal(p3,ampl3)

#calibr result
c=[ 1.        ,  0.86008597,  1.1899558 ,  0.71319166,  1.48059081]

pick(ts,ts+240,p1,ampl1,0,10)
c=[1,1,1,1,1]

run(c,ts,ts+180,0.9,0.1,0,10)

print(d)