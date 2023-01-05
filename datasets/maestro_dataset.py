# Copyright (c) 2022, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# This work is licensed under a Creative Commons
# Attribution-NonCommercial-ShareAlike 4.0 International License.
# You should have received a copy of the license along with this
# work. If not, see http://creativecommons.org/licenses/by-nc-sa/4.0/

"""Streaming images and labels from datasets created with dataset_tool.py."""

import os
import numpy as np
import zipfile
#import PIL.Image
import json
import torch
import utils.dnnlib as dnnlib
import random
import pandas as pd
import glob
import soundfile as sf

#try:
#    import pyspng
#except ImportError:
#    pyspng = None

#----------------------------------------------------------------------------
# Dataset subclass that loads images recursively from the specified directory
# or ZIP file.

class MaestroDataset_fs(torch.utils.data.IterableDataset):
    def __init__(self,
        dset_args,
        overfit=False, #set to True for overfitting dataset (lightweight tests to vccheck that the dataloading is not bottlenecking)
        seed=42 ):

        super().__init__()
        self.overfit=overfit
        random.seed(seed)
        np.random.seed(seed)
        path=dset_args.path
        years=dset_args.years

        metadata_file=os.path.join(path,"maestro-v3.0.0.csv")
        metadata=pd.read_csv(metadata_file)

        metadata=metadata[metadata["year"].isin(years)]
        metadata=metadata[metadata["split"]=="train"]
        filelist=metadata["audio_filename"]

        filelist=filelist.map(lambda x:  os.path.join(path,x)     , na_action='ignore')


        self.train_samples=filelist.to_list()
       
        self.seg_len=int(dset_args.load_len)


    def __iter__(self):
        if self.overfit:
           data_clean=self.overfit_sample
        while True:
            if not self.overfit:
                num=random.randint(0,len(self.train_samples)-1)
                #for file in self.train_samples:  
                file=self.train_samples[num]
                data, samplerate = sf.read(file)
                #print(file,samplerate)

                data_clean=data
                #Stereo to mono
                if len(data.shape)>1 :
                    data_clean=np.mean(data_clean,axis=1)
    
            #normalize
            #no normalization!!
            #data_clean=data_clean/np.max(np.abs(data_clean))
         
            #framify data clean files

            num_frames=np.floor(len(data_clean)/self.seg_len) 
            
            if num_frames>4:
                for i in range(8):
                    #get 8 random batches to be a bit faster
                    if not self.overfit:
                        idx=np.random.randint(0,len(data_clean)-self.seg_len)
                    else: 
                        idx=0
                    segment=data_clean[idx:idx+self.seg_len]
                    segment=segment.astype('float32')
                    #b=np.mean(np.abs(segment))
                    #segment= (10/(b*np.sqrt(2)))*segment #default rms  of 0.1. Is this scaling correct??
                     
                    #let's make this shit a bit robust to input scale
                    #scale=np.random.uniform(1.75,2.25)
                    #this way I estimage sigma_data (after pre_emph) to be around 1
                   
                    #segment=10.0**(scale) *segment
                    yield  segment, samplerate
            else:
                pass
class MaestroDataset(torch.utils.data.IterableDataset):
    def __init__(self,
        dset_args,
        fs=44100,
        seg_len=131072,
        overfit=False, #set to True for overfitting dataset (lightweight tests to vccheck that the dataloading is not bottlenecking)
        seed=42 ):

        super().__init__()
        self.overfit=overfit
        random.seed(seed)
        np.random.seed(seed)
        path=dset_args.path
        years=dset_args.years

        metadata_file=os.path.join(path,"maestro-v3.0.0.csv")
        metadata=pd.read_csv(metadata_file)

        metadata=metadata[metadata["year"].isin(years)]
        metadata=metadata[metadata["split"]=="train"]
        filelist=metadata["audio_filename"]

        filelist=filelist.map(lambda x:  os.path.join(path,x)     , na_action='ignore')


        self.train_samples=filelist.to_list()
       
        self.seg_len=int(seg_len)
        self.fs=fs
        if self.overfit:
            file=self.train_samples[0]
            data, samplerate = sf.read(file)
            assert samplerate==self.fs, "wrong sampling rate"
            if len(data.shape)>1 :
                data=np.mean(data,axis=1)
            self.overfit_sample=data[10*samplerate:60*samplerate] #use only 50s

    def __iter__(self):
        if self.overfit:
           data_clean=self.overfit_sample
        while True:
            if not self.overfit:
                num=random.randint(0,len(self.train_samples)-1)
                #for file in self.train_samples:  
                file=self.train_samples[num]
                data, samplerate = sf.read(file)
                assert(samplerate==self.fs, "wrong sampling rate")
                data_clean=data
                #Stereo to mono
                if len(data.shape)>1 :
                    data_clean=np.mean(data_clean,axis=1)
    
            #normalize
            #no normalization!!
            #data_clean=data_clean/np.max(np.abs(data_clean))
         
            #framify data clean files
            num_frames=np.floor(len(data_clean)/self.seg_len) 
            
            if num_frames>4:
                for i in range(8):
                    #get 8 random batches to be a bit faster
                    if not self.overfit:
                        idx=np.random.randint(0,len(data_clean)-self.seg_len)
                    else: 
                        idx=0
                    segment=data_clean[idx:idx+self.seg_len]
                    segment=segment.astype('float32')
                    #b=np.mean(np.abs(segment))
                    #segment= (10/(b*np.sqrt(2)))*segment #default rms  of 0.1. Is this scaling correct??
                     
                    #let's make this shit a bit robust to input scale
                    #scale=np.random.uniform(1.75,2.25)
                    #this way I estimage sigma_data (after pre_emph) to be around 1
                   
                    #segment=10.0**(scale) *segment
                    yield  segment
            else:
                pass

