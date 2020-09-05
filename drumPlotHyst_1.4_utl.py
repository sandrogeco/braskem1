
# sudo /home/slarchive2.2/./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# /home/Documents/openVPNBraskem/openvpn --config clientBRASKEM__GEOAPP.conf

# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/

#da home/Dovuments/mSeedTest   /home/sandro/anaconda3/envs/mSeedTest/bin/python /home/sandro/Documents/mSeedTest/drumPlotHyst_1.4_utl.py



# Current thread 0x00007f743ef01700 (most recent call first):
#   File "/usr/local/lib/python3.6/dist-packages/obspy/io/mseed/headers.py", line 825 in _wrapper
#   File "/usr/local/lib/python3.6/dist-packages/obspy/io/mseed/core.py", line 403 in _read_mseed
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/util/base.py", line 469 in _read_from_plugin
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/stream.py", line 257 in _read
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/util/decorator.py", line 210 in uncompress_file
#   File "</usr/local/lib/python3.6/dist-packages/decorator.py:decorator-gen-32>", line 2 in _read
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/util/base.py", line 701 in _generic_reader
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/stream.py", line 212 in read
#   File "/usr/local/lib/python3.6/dist-packages/obspy/core/util/decorator.py", line 300 in _map_example_filename
#   File "</usr/local/lib/python3.6/dist-packages/decorator.py:decorator-gen-31>", line 2 in read
#   File "/usr/local/lib/python3.6/dist-packages/obspy/clients/filesystem/sds.py", line 176 in get_waveforms
#   File "/home/sandro/Documents/mSeedTest/seisLib.py", line 587 in run
#   File "drumPlotHyst_1.4_utl.py", line 21 in <module>
# Segmentation fault (core dumped)

import multiprocessing

from seisLib import drumPlot
import seisLib
import numpy as np

from obspy import  UTCDateTime

stz=seisLib.stations(['BRK0','BRK1','BRK2','BRK3','BRK4'],'LK')


client = seisLib.drumPlot('/mnt/ide/seed/')

client._alertTable='seismic.alerts'
client._basePath = '/home/geoapp/'
client._basePathRT = '/mnt/geoAppServer/'
client._stations=stz
client._amplAn = {
    'lowFW': [1, 20],
    'highFW': [20, 50],
    'lowFTh': 0.00001,
    'highFTh': 0.00005

}

#client.multiPr_run('LK', 'BRK?', 'E??' )



st=['LK_BRK0','LK_BRK1','LK_BRK2','LK_BRK3','LK_BRK4']
cl=[('LK_BRK0','LK_BRK2'),('LK_BRK1','LK_BRK2'),('LK_BRK1','LK_BRK4'),('LK_BRK3','LK_BRK4')]


al=seisLib.alert('seismic.alerts')
al._stations=stz

al._th = {  # soglie su cui definire rate
    'AML': 0.00005,
    'AMH': 0.00005
}
al._rTh = {  # soglie rate
    'AML': 0,
    'AMH': 0,
    'wnd': 1,
    'sft': 0.25
}
al._clTh={
    'lag':36000
}

al._rateX=np.arange(0,100,1)
al._amplY=np.arange(0.01,-0.0001,-0.0001)
al._thMatrix=np.zeros([len(al._amplY),len(al._rateX)])
al._thMatrix[0:np.where(al._amplY>0.00004)[0][-1],5:]=1
al._thMatrix[0:np.where(al._amplY>0.0008)[0][-1],20:]=2
al._thMatrix[0:np.where(al._amplY>0.002)[0][-1],40:]=3
al._clusters=cl

#al.HR_run(st)
#al.multiPr_HR_run(st)
