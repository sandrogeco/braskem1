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

    return WCT,S1,S2, times, frequencies, coif


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

