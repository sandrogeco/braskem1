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





import numpy as np
from scipy import signal, ndimage
from scipy.interpolate import interp1d

import pywt

import matplotlib.pyplot as plt

from matplotlib.colors import Normalize, LogNorm, NoNorm
from matplotlib.cm import get_cmap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import time
plt.switch_backend('tKagg')


def xwt_spectrogram(x1, x2, fs, nNotes=12, detrend=True, normalize=True):
    N1 = len(x1)
    N2 = len(x2)
    assert (N1 == N2), "error: arrays not same size"

    N = N1
    dt = 1.0 / fs
    times = np.arange(N) * dt

    ###########################################################################
    # detrend and normalize
    if detrend:
        x1 = signal.detrend(x1, type='linear')
        x2 = signal.detrend(x2, type='linear')
    if normalize:
        stddev1 = x1.std()
        x1 = x1 / stddev1
        stddev2 = x2.std()
        x2 = x2 / stddev2

    ###########################################################################
    # Define some parameters of our wavelet analysis.

    # maximum range of scales that makes sense
    # min = 2 ... Nyquist frequency
    # max = np.floor(N/2)

    nOctaves = np.int(np.log2(2 * np.floor(N / 2.0)))
    scales = 2 ** np.arange(1, nOctaves, 1.0 / nNotes)

    ###########################################################################
    # cwt and the frequencies used.
    # Use the complex morelet with bw=1.5 and center frequency of 1.0
    coef1, freqs1 = pywt.cwt(x1, scales, 'cmor1.5-1.0')
    coef2, freqs2 = pywt.cwt(x2, scales, 'cmor1.5-1.0')
    frequencies = pywt.scale2frequency('cmor1.5-1.0', scales) / dt

    ###########################################################################
    # Calculates the cross CWT of xs1 and xs2.
    coef12 = coef1 * np.conj(coef2)

    ###########################################################################
    # power
    power = np.abs(coef12)

    # smooth a bit
    power = ndimage.gaussian_filter(power, sigma=2)

    ###########################################################################
    # cone of influence in frequency for cmorxx-1.0 wavelet
    f0 = 2 * np.pi
    cmor_coi = 1.0 / np.sqrt(2)
    cmor_flambda = 4 * np.pi / (f0 + np.sqrt(2 + f0 ** 2))
    # cone of influence in terms of wavelength
    coi = (N / 2 - np.abs(np.arange(0, N) - (N - 1) / 2))
    coi = cmor_flambda * cmor_coi * dt * coi
    # cone of influence in terms of frequency
    coif = 1.0 / coi

    return power, times, frequencies, coif

def xwt_coherence(x1, x2, fs, nNotes=12, detrend=True, normalize=True):
    N1 = len(x1)
    N2 = len(x2)
    assert (N1 == N2), "error: arrays not same size"

    N = N1
    dt = 1.0 / fs
    times = np.arange(N) * dt

    ###########################################################################
    # detrend and normalize
    if detrend:
        x1 = signal.detrend(x1, type='linear')
        x2 = signal.detrend(x2, type='linear')
    if normalize:
        stddev1 = x1.std()
        x1 = x1 / stddev1
        stddev2 = x2.std()
        x2 = x2 / stddev2

    ###########################################################################
    # Define some parameters of our wavelet analysis.

    # maximum range of scales that makes sense
    # min = 2 ... Nyquist frequency
    # max = np.floor(N/2)

    nOctaves = np.int(np.log2(2 * np.floor(N / 2.0)))
    scales = 2 ** np.arange(1, nOctaves, 1.0 / nNotes)

    ###########################################################################
    # cwt and the frequencies used.
    # Use the complex morelet with bw=1.5 and center frequency of 1.0
    coef1, freqs1 = pywt.cwt(x1, scales, 'cmor1.5-1.0')
    coef2, freqs2 = pywt.cwt(x2, scales, 'cmor1.5-1.0')
    frequencies = pywt.scale2frequency('cmor1.5-1.0', scales) / dt

    ###########################################################################
    # Calculates the cross transform of xs1 and xs2.
    coef12 = coef1 * np.conj(coef2)

    ###########################################################################
    # coherence
    scaleMatrix = np.ones([1, N]) * scales[:, None]
    S1 = ndimage.gaussian_filter((np.abs(coef1) ** 2 / scaleMatrix), sigma=2)
    S2 = ndimage.gaussian_filter((np.abs(coef2) ** 2 / scaleMatrix), sigma=2)
    S12 = ndimage.gaussian_filter((np.abs(coef12 / scaleMatrix)), sigma=2)
    WCT = S12 ** 2 / (S1 * S2)

    ###########################################################################
    # cone of influence in frequency for cmorxx-1.0 wavelet
    f0 = 2 * np.pi
    cmor_coi = 1.0 / np.sqrt(2)
    cmor_flambda = 4 * np.pi / (f0 + np.sqrt(2 + f0 ** 2))
    # cone of influence in terms of wavelength
    coi = (N / 2 - np.abs(np.arange(0, N) - (N - 1) / 2))
    coi = cmor_flambda * cmor_coi * dt * coi
    # cone of influence in terms of frequency
    coif = 1.0 / coi

    return WCT, times, frequencies, coif


def spectrogram_plot(z, times, frequencies, coif, zth=0.75,cmap=None, norm=Normalize(), ax=None, colorbar=True):
    ###########################################################################
    # plot

    # set default colormap, if none specified
    if cmap is None:
        cmap = get_cmap('Greys')
    # or if cmap is a string, get the actual object
    elif isinstance(cmap, str):
        cmap = get_cmap(cmap)

    # create the figure if needed
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = plt.gcf()

    xx, yy = np.meshgrid(times, frequencies)
    z[z<zth]=0
    ZZ = z

    im = ax.pcolor(xx, yy, ZZ, norm=norm, cmap=cmap)
    ax.plot(times, coif)
    ax.fill_between(times, coif, step="mid", alpha=0.4)

    if colorbar:
        cbaxes = inset_axes(ax, width="2%", height="90%", loc=4)
        fig.colorbar(im, cax=cbaxes, orientation='vertical')

    ax.set_xlim(times.min(), times.max())
    ax.set_ylim(frequencies.min(), frequencies.max())

    return ax


plt.rcParams['figure.figsize'] = (16, 6)
plt.rcParams['pcolor.shading']='nearest'
wav_data = np.loadtxt('benchmark_signals/tohoku.txt')

client = drumPlot('/mnt/ide/seed/')
ts=UTCDateTime('2020-09-19 15:00:30')
ts1=UTCDateTime('2020-09-19 15:00:30')
tr1=client.get_waveforms('LK','BRK2','','EHZ',ts-10,ts+300)
tr2=client.get_waveforms('LK','BRK1','','EHZ',ts1-10,ts1+300)
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
dec = 15
wav_data = signal.decimate(ttr1,dec)
bad_data = signal.decimate(ttr2,dec)
sampling_frequency = sampling_frequency/dec

# sampling_frequency = 20
#
#
# # downsample, so the examples don't take too long to compute
# dec = 50
# wav_data = signal.decimate(wav_data,dec)
# sampling_frequency = sampling_frequency/dec
#
n_samples = len(wav_data)
total_duration = n_samples / sampling_frequency
sample_times = np.linspace(0, total_duration, n_samples)


# # make some bad data to compre to
#
# noise = np.random.randn(len(wav_data))*wav_data.max()/100
# bad_data = np.copy(wav_data)
# # bad_data = np.roll(bad_data,0)
# #bad_data[500:700] = np.roll(bad_data[500:700],100)
#
# bad_data[200:300] = bad_data[200:300]+noise[200:300]/5
# bad_data[900:] = bad_data[900:]+noise[900:]
#
###########################################################################
# calculate spectrogram

t0 = time.time()
coherence, times, frequencies, coif = xwt_coherence(wav_data, bad_data, sampling_frequency, 12,True,False)
print (time.time()-t0)


################################################################
fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

################################################################
ax1.plot(sample_times, wav_data, color='b');

ax1.set_xlim(0, total_duration)
ax1.set_xlabel('time (s)')

ax1.grid(True)
################################################################
ax2.plot(sample_times, bad_data, color='b');

ax2.set_xlim(0, total_duration)
ax2.set_xlabel('time (s)')

ax2.grid(True)
################################################################

spectrogram_plot(coherence, times, frequencies, coif,0.98, cmap='jet', norm=LogNorm(), ax=ax3)
ax3.set_xlim(0, total_duration)
# ax.set_ylim(0, 0.5*sampling_frequency)
ax3.set_ylim(2.0/total_duration, 0.5*sampling_frequency)
ax3.set_xlabel('time (s)')
ax3.set_ylabel('frequency (Hz)');

ax3.grid(True)
# ax3.set_yscale('log')
plt.pause(1)
print('f')