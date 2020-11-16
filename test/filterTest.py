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
import  matplotlib.pyplot as plt

plt.switch_backend('tKagg')

from obspy import read


ref = read('ref.mseed')
meas_geco = read('meas_geco.mseed')
meas_lun = read('meas_lun.mseed')


ts=UTCDateTime(2020,11,9,15,47,15)
te=UTCDateTime(2020,11,9,15,48,10)

ref.trim(ts,te)
meas_geco.trim(ts,te)
meas_lun.trim(ts,te)


fft_geco=np.fft.fft(meas_geco[0].data)
fft_lun=np.fft.fft(meas_lun[0].data)
fft_ref=np.fft.fft(ref[0].data)


from scipy import signal


Ggm=fft_geco/fft_ref
Glm=fft_lun/fft_ref

freq = np.fft.fftfreq(fft_ref.shape[-1],1/100)


plt.figure()
plt.plot(freq, np.abs(Ggm),'go')    # Bode magnitude plot
plt.plot(freq, np.angle(Ggm),'yo')    # Bode magnitude plot
plt.show()
plt.figure()

plt.plot(freq, np.abs(Glm),'gv')    # Bode magnitude plot
plt.plot(freq, np.angle(Glm),'yv')    # Bode magnitude plot
plt.show()
print('ppippo')
#
#
# w, h = signal.freqs(meas_geco[0].data,ref[0].data,worN=np.logspace(-1, 4, 1000))
# w1, h1 = signal.freqs(meas_lun[0].data,ref[0].data,worN=np.logspace(-1, 4, 1000))
# fig, ax1 = plt.subplots()
# ax1.set_title('lunitek camera filter frequency response')
# ax1.semilogx(w, 20 * np.log10(abs(h)), 'bv')
# ax1.semilogx(w1, 20 * np.log10(abs(h1)), 'bo')
# ax1.set_ylabel('Amplitude [dB]', color='b')
# ax1.set_xlabel('Frequency [Hz]')
# ax2 = ax1.twinx()
# angles = np.unwrap(np.angle(h))
# ax2.semilogx(w, angles, 'gv')
# angles = np.unwrap(np.angle(h1))
# ax2.semilogx(w1, angles, 'go')
# ax2.set_ylabel('Angle (radians)', color='g')
# ax2.grid()
# ax2.axis('tight')
# plt.show()
# #
# # ref.plot()
# # meas.plot()
#
# print('x')