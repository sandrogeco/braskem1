import time
from seisLib import drumPlot
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
plt.switch_backend('tKagg')

client = drumPlot('/mnt/ide/seed/')

wnd=15/3600
sft=5/3600



st=['BRK0','BRK1','BRK2','BRK3','BRK4']
ns=len(st)
# data=np.load('metadata/dst.npz')
# dst=data['dst']
# dsts=data['dsts']
# grid=data['grid']

def loc(dstM,r,dec,e,lx,ly,lz):
    dst=np.zeros(dstM.shape,object)
    dst[:,:,:]=dstM[:,:,:]
    result = np.ones(dst.shape)*np.Inf
    for i in np.arange(lx[0], lx[1], dec):
        for j in np.arange(ly[0], ly[1], dec):
            for k in np.arange(lz[0], lz[1], dec):
                p = r - dst[i, j, k]
                p[e, :] = 0
                p[:, e] = 0
                pp=p[0,:]
                result[i, j, k] = np.sqrt(np.dot(pp,pp))/(ns*ns/2-ns-len(e))

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

def run(st):

        # l=log()
        # te=l.rdLog()
    te=UTCDateTime(2020,8,1,16,30)
    tre={}
    while 1<2:
        if te<UTCDateTime.now():
            # l.wrLog(te)
            te=te+sft*3600
            tr=client.get_waveforms('LK', 'BRK?', '', 'EHZ', te-120,te)
            tr.remove_response(client._inv)
            tr.filter('bandpass', freqmin=4, freqmax=12, corners=3, zerophase=True)

            for s in range(0,len(st)):
                trs=tr.select('LK',st[s],'','EHZ')
                tre[s]=obspy.signal.filter.envelope(trs[0].data)
                cc=[]
            for s in range(0,len(st)):
                for s1 in range(s,len(st)):
                    c=obspy.signal.cross_correlation.correlate(tre[s],tre[s1],len(tre[s]))
                    cc[s, s1] =np.max(c)
            print('pp')
        else:
            time.sleep(10)

run(st)


#
#
#
#
# lta=10
# sta=1
# sl=1.2
# ttL=tt
# readLta=True
# traces=np.zeros(ns,object)
# trf=np.zeros(ns,object)
# tr=np.zeros(ns,object)
# th=0.00001
#
# #
# # pp=['BRK0','BRK1','BRK2','BRK3','BRK4']
# # p=client.get_waveforms('LK', 'BRK0', '', 'EH?', UTCDateTime(2020,7,30,20,0,0),UTCDateTime(2020,7,30,20,10,0))
# # p.remove_response(client._inv)
# # tr=p.copy()
# # tr.filter('bandpass', freqmin=4, freqmax=12, corners=3, zerophase=True)
# # u = obspy.signal.polarization.polarization_analysis(tr, 5, .1, 4, 12,
# #                                                     tr[0].stats['starttime'], tr[0].stats['endtime'], False,
# #                                                     'pm')
# # plt.figure()
# # plt.plot(tr[0].times('timestamp'),tr[0].data*100000)
# # plt.plot(u['timestamp'],u['azimuth'],'o',markersize=1)
# # plt.plot(u['timestamp'],u['azimuth_error']*500,'o',markersize=1)
# # plt.plot(u['timestamp'],u['incidence_error']*500,'o',markersize=1)
# while 1<2:
#     # print('sta from ' + UTCDateTime(tt - sta * wnd).strftime("%Y%m%d_%H%M%S") + ' to ' + UTCDateTime(
#     #     tt + sta * wnd).strftime("%Y%m%d_%H%M%S"))
#     # if tt > ttL + lta * wnd-sta*wnd:
#     #     ttL = tt
#     #     readLta=True
#     # if readLta:
#     for s in np.arange(0, ns):
#         traces[s] = client.get_waveforms('LK', st[s], '', 'EHZ', tt - lta * wnd, tt + lta * wnd)
#         traces[s].remove_response(client._inv)
#         #traces[s].filter('bandpass', freqmin=3, freqmax=20, corners=2, zerophase=True)
#
#     band=[(3,8),(8,13),(13,18),(18,23),(23,28)]
#
#     for s in np.arange(0, ns):
#
#         vpp[s]=[]
#         step=1
#         ovr=1
#         for b in np.arange(3,10,step):
#             tr[s] = traces[s].copy()
#             tr[s].filter('bandpass', freqmin=b-ovr, freqmax=b+step, corners=2, zerophase=True)
#             tr[s].trim(tt - sta * wnd, tt + sta * wnd)
#             vpp[s].append(np.max(obspy.signal.filter.envelope(tr[s][0].data)))#np.max(trAmpl(tr[s])) #np.max(np.abs(tr[s].data))
#
#
#
#
#     readLta = False
#     e=[]
#     #vCh=(vppOffsetShort/vppOffset)>sl
#
#     vCh=np.asarray([np.max(v) for v in vpp ])>th
#     #vCh[3]=False
#
#     print(tt)
#     print(vpp)
#     print(vCh)
#
#
#     if (np.sum(vCh))>=3:
#         # print('vpp')
#         # print(vpp)
#         # print('vOffset')
#         # print(vppOffset)
#         # print('vOffsetShort')
#         # print(vppOffsetShort)
#         # print('vCh')
#         # print(vCh)
#         # print('vo')
#         # print(vOffset)
#         #vpp = vpp - vOffset
#         for i in np.arange(0,ns):
#             for j in np.arange(i+1,ns):
#                 r[i,j]=vpp[j][0]/vpp[i][0]
#         #[plt.plot(v) for v in vpp]
#
#         e=np.where(vCh == False)
#         #e=[3]
#         #aVol1 = locDsp(dst, r, 1, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
#
#         aVol = loc(dst, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
#
#         mm = aVol['mPos']
#         m = aVol['min']
#         x = grid[0, mm[0], mm[1], mm[2]]
#         y = grid[1, mm[0], mm[1], mm[2]]
#         z = grid[2, mm[0], mm[1], mm[2]]
#         lat, lon = utm.to_latlon(x, y, 25, 'L')
#         # lat=lat+(np.random.rand()*2-1)/10000
#         # lon=lon+(np.random.rand()*2-1)/10000
#         ttt=UTCDateTime(tt)
#
#         ev = {
#             'id': UTCDateTime(ttt).strftime("%m%d%H%M%S"),
#             'time': UTCDateTime(ttt),
#            # 'text': 'SWARM ev. mag' + str(pp[5]),
#             'lat': lat,
#             'lon': lon,
#             'dpt': z,
#             'mag':1,#np.log(np.max(np.asarray(vpp))/th),
#             'note':'error '+str(m)
#         }
#         # client.pushIntEv(ev)
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
