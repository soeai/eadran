#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import pandas as pd
import soundfile as sf
"""
class for reading RAW acoustic reads, whihc returns a time series as two 
datetime and value arrays.
"""
class RAWSource(object):
    def __init__(self, **kwargs):
        super(RAWSource, self).__init__(**kwargs)
    def raw_to_time_series(self, raw_file_path, channels=1, samplerate=8000, 
                           subtype='PCM_32', endian='LITTLE'):
        signal_raw = sf.read(raw_file_path, channels=channels, 
                             samplerate=samplerate, subtype=subtype, 
                             endian=endian)
        signal = signal_raw[0]
        return signal
"""
Function to convert the RAWSource outputs to a pandas Dataframe.
""" 
def read_raw_to_signals(directory):
    raw_reader = RAWSource()
    d = {}
    with os.scandir(directory) as entries:
        ID = []
        S = []
        for entry in entries:
            s = raw_reader.raw_to_time_series(entry)
            id = entry.name.split('.')[0]
            ID.append(id)
            S.append(s)
    #print("S: ", S)
    #print("ID: ", ID)
    for i, item in enumerate(ID):
        d_temp = {ID[i]: pd.Series(S[i])}
        d.update(d_temp)
    # d = {ID[0]: pd.Series(S[0]),
    #     ID[1]: pd.Series(S[1])}
    """
     here, d includes two acoustic signals in the Ambient Sound folder.
     For acoustic data in the Hydrophone folder, d should be the following.
     d = {ID[0]: pd.Series(S[0]),ID[1]: pd.Series(S[1]),ID[2]: pd.Series(S[2]),
          ID[3]: pd.Series(S[3]),ID[4]: pd.Series(S[4]),ID[5]: pd.Series(S[5]),
          ID[6]: pd.Series(S[6]),ID[7]: pd.Series(S[7]),ID[8]: pd.Series(S[8]),
          ID[9]: pd.Series(S[9]),ID[10]: pd.Series(S[10]),ID[11]: pd.Series(S[11])}
    """
    df_data = pd.DataFrame(d)
    df_data = df_data.head(240000)
    return df_data

