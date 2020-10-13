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


from skimage import  data, filters, measure, morphology


import numpy as np
from scipy import signal, ndimage
from scipy.interpolate import interp1d

import pywt

import matplotlib.pyplot as plt

from matplotlib.colors import Normalize, LogNorm, NoNorm
from matplotlib.cm import get_cmap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import time
import xwt
plt.switch_backend('tKagg')



plt.rcParams['figure.figsize'] = (16, 6)
plt.rcParams['pcolor.shading']='nearest'
wav_data = np.loadtxt('benchmark_signals/tohoku.txt')

client = drumPlot('/mnt/ide/seed/')
ts=UTCDateTime('2020-09-19 15:00:30')
ts1=UTCDateTime('2020-09-19 15:00:30')
tr1=client.get_waveforms('LK','BRK0','','EHZ',ts,ts+120)
tr2=client.get_waveforms('LK','BRK1','','EHZ',ts1,ts1+120)
#tr1.detrend()
#tr2.detrend()
tr1.merge()
tr2.merge()
tr1.remove_response(client._inv)
tr2.remove_response(client._inv)
tr1.filter('bandpass', freqmin=0.5, freqmax=20, corners=3, zerophase=True)
tr2.filter('bandpass', freqmin=0.5, freqmax=20, corners=3, zerophase=True)

ttr1=obspy.signal.filter.envelope(tr1[0].data)[100:-100]
ttr2=obspy.signal.filter.envelope(tr2[0].data)[100:-100]
sampling_frequency=250
dec = 10
wav_data = signal.decimate(ttr1,dec)
bad_data = signal.decimate(ttr2,dec)
sampling_frequency = sampling_frequency/dec
n_samples = len(wav_data)
total_duration = n_samples / sampling_frequency
sample_times = np.linspace(0, total_duration, n_samples)

t0 = time.time()
coherence, s1,s2,times, frequencies, coif = xwt.xwt_coherence(wav_data, bad_data, sampling_frequency, 12,True,False)

print (time.time()-t0)


################################################################
fig, (ax1, ax2, ax3,ax4) = plt.subplots(4, 1)

################################################################
ax1.plot(sample_times, wav_data, color='b');

ax1.set_xlim(0, total_duration)
ax1.set_xlabel('time (s)')

ax1.grid(True)
################################################################
ax1.plot(sample_times, bad_data, color='r');

ax1.set_xlim(0, total_duration)
ax1.set_xlabel('time (s)')

ax1.grid(True)
################################################################

# xwt.spectrogram_plot(s1, times, frequencies, coif,0.0, cmap='jet', norm=LogNorm(), ax=ax2)
# ax2.set_xlim(0, total_duration)
# # ax.set_ylim(0, 0.5*sampling_frequency)
# ax2.set_ylim(2.0/total_duration, 0.5*sampling_frequency)
# ax2.set_xlabel('time (s)')
# ax2.set_ylabel('frequency (Hz)');
#
# ax2.grid(True)

xwt.spectrogram_plot(coherence, times, frequencies, coif,0.95, cmap='jet', norm=LogNorm(), ax=ax2)
ax2.set_xlim(0, total_duration)
# ax.set_ylim(0, 0.5*sampling_frequency)
ax2.set_ylim(2.0/total_duration, 0.5*sampling_frequency)
ax2.set_xlabel('time (s)')
ax2.set_ylabel('frequency (Hz)');

ax2.grid(True)


selemV=np.zeros((15,15))
selemH=np.zeros((15,15))
selemV[:,4]=1
selemH[4,:]=1
cth=0.95
ch=coherence.copy()
ch[ch>cth]=1
ch[ch<=cth]=0
ch[frequencies<0,:]
erodeH=morphology.erosion(ch, selemH)
erodeV=morphology.erosion(ch, selemV)


minDur=1
tFlt=minDur*sampling_frequency

mm=measure.label(ch, connectivity=2)
rp=measure.regionprops(mm)
c=[]
for r in rp:
    if np.abs(r.bbox[2]-r.bbox[0])<tFlt:
        mm[mm==r.label]=0
    else:
        c.append(r.centroid)

xwt.spectrogram_plot(mm, times, frequencies, coif,0.0, cmap='jet', norm=LogNorm(), ax=ax3)
ax3.set_xlim(0, total_duration)
# ax.set_ylim(0, 0.5*sampling_frequency)
ax3.set_ylim(2.0/total_duration, 0.5*sampling_frequency)
ax3.set_xlabel('time (s)')
ax3.set_ylabel('frequency (Hz)');

ax3.grid(True)
xwt.spectrogram_plot(erodeV, times, frequencies, coif,0.0, cmap='jet', norm=LogNorm(), ax=ax4)
ax4.set_xlim(0, total_duration)
# ax.set_ylim(0, 0.5*sampling_frequency)
ax4.set_ylim(2.0/total_duration, 0.5*sampling_frequency)
ax4.set_xlabel('time (s)')
ax4.set_ylabel('frequency (Hz)');
# ax3.set_yscale('log')
ax4.grid(True)
plt.pause(1)
print('f')