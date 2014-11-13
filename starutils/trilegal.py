from __future__ import print_function,division

import logging
import numpy as np
import subprocess as sp
import pandas as pd
import os

from astropy.units import UnitsError
from astropy.coordinates import SkyCoord
from .extinction import get_AV_infinity

NONMAG_COLS = ['Gc','logAge', '[M/H]', 'm_ini', 'logL', 'logTe', 'logg',
               'm-M0', 'Av', 'm2/m1', 'mbol', 'Mact'] #all the rest are mags

def get_trilegal(filename,ra,dec,folder='.',
                 filterset='kepler_2mass',area=1,maglim=27,binaries=False,
                 trilegal_version='1.6',sigma_AV=0.1,convert_h5=True):
    """Runs get_trilegal perl script; optionally saves output into .h5 file
    """
    try:
        c = SkyCoord(ra,dec)
    except UnitsError:
        c = SkyCoord(ra,dec,unit='deg')
    l,b = (c.galactic.l.value,c.galactic.b.value)
    outfile = '{}/{}.dat'.format(folder,filename)
    AV = get_AV_infinity(l,b,frame='galactic')
    cmd = 'get_trilegal %s %f %f %f %i %.3f %.2f %s 1 %.1f %s' % (trilegal_version,l,b,
                                                                  area,binaries,AV,sigma_AV,
                                                                  filterset,maglim,outfile)
    sp.Popen(cmd,shell=True).wait()
    if convert_h5:
        sp.Popen("sed -i 's/#Gc/Gc/' {}".format(outfile),shell=True).wait() #uncomments first line
        df = pd.read_table(outfile,delim_whitespace=True,comment='#')
        for col in df.columns:
            if col not in NONMAG_COLS:
                df.rename(columns={col:'{}_mag'.format(col)},inplace=True)
        h5file = '{}/{}.h5'.format(folder,filename)
        df.to_hdf(h5file,'df')
        store = pd.HDFStore(h5file)
        attrs = store.get_storer('df').attrs
        attrs.trilegal_args = {'version':trilegal_version,
                               'l':l,'b':b,'area':area,
                               'AV':AV, 'sigma_AV':sigma_AV,
                               'filterset':filterset,
                               'maglim':maglim,
                               'binaries':binaries}
        store.close()
        os.remove(outfile)
    
    