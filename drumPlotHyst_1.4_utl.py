
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



from seisLib import drumPlot


from obspy import  UTCDateTime

client = drumPlot('/mnt/ide/seed/')

client._alertTable='seismic.alerts'
client._basePath = '/home/geoapp/'
client._basePathRT = '/mnt/geoAppServer/' # '/home/sandro/Documents/mSeedTest/'#'#
client.run('LK', 'BRK?', 'E??',False )