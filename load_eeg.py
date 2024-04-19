import locations
import mne
import numpy as np
import os
import read_xml

verbose = False

def load_word_epochs_all_participant(participants, unload_eeg = True):
    '''load all word epochs for all participants.'''
    for participant in participants:
        print(participant.pp_id)
        load_word_epochs_participant(participant, unload_eeg = unload_eeg)

def load_word_epochs_participant(participant, unload_eeg = True,
    value_dict = {},count_dict ={}):
    '''load word_epochs for a participant'''
    participant.bad_blocks = []
    extracted, excluded = 0, 0
    for i,block in enumerate(participant.blocks):
        print(i,block.__repr__(),len(participant.blocks))
        succes = make_eeg_word_epochs(block)
        if not succes: participant.bad_blocks.append(block)
        else:
            extracted += len(block.extracted_eeg_words)
            excluded += len(block.bad_words)
            vd, cd= block2average(block,value_dict,count_dict)
            value_dict, count_dict = vd, cd
        if unload_eeg: unload_eeg_data(block)
    print('pp_id:',participant.pp_id,'bad blocks:',
        len(participant.bad_blocks))
    print('extracted words:',extracted,'excluded words:',excluded)
    o = [participant.pp_id,len(participant.bad_blocks),extracted,excluded]
    return ' '.join(map(str,o)), value_dict, count_dict

def unload_eeg_data(block):
    if hasattr(block,'raw'): delattr(block,'raw')
    if hasattr(block,'data'):delattr(block,'data')
    if hasattr(block,'ica'): delattr(block,'ica')
    block.eeg_loaded = False
    block.ica_applied = False

def make_eeg_word_epochs(block, channel_set = [],remove_bad_ch = True,
    bad_block_check = True):
    '''Extract EEG data corresponding to words in the block.
    Only words are loaded that do not overlap with artefacts in the 
    EEG data or other words
    EEG data is loaded as muVolts
    bandpass filter 0.05 - 30 iir filter
    ica decomposition to remove EOG activity
    channel_set         set of channels to extract default = all eeg 
                        channels
    remove_bad_ch       whether to remove channels with poor EEG data
    bad_block_check     whether to make word epochs if the block contains 
                        bad EEG data
                        defaults to not loading EEG data when quality is 
                        poor
    '''
    if not hasattr(block,'words'): 
        print('words are missing load blocks with add_words = True')
    block.extracted_eeg_words = []
    block.extracted_word_indices = []
    block.bad_words = []
    if bad_block_check and block.usability in ['doubtfull','bad']:
        print('skipping block because it is bad,', 
            'force load by setting bad_block_check = False')
        print('blocks with usability doubtfull or bad have poor eeg data')
        return False
    if channel_set == []: channel_set = load_channel_set('default')
    if not hasattr(block,'raw'): add_eeg_data(block)
    if block.raw == 0:
        print('could not load eeg data',block.__repr__())
        return 
    if not block.ica_applied:
        print('could not load and apply ica',block.__repr__())
        return
    rbch = remove_bad_ch if remove_bad_ch else []
    t = raw2np(block.raw, keep_channels = channel_set, remove_bad_ch = rbch)
    block.data,block.ch,block.removed_ch = t
    if verbose: print('excluded words:')
    for i, word in enumerate(block.words):
        check_word_usability(block,word)
        if not word.usable: block.bad_words.append(word)
        else: 
            d = extract_word_eeg_data(block.data, word, block.st_sample)
            if type(d) == np.ndarray:
                block.extracted_eeg_words.append(d)
                block.extracted_word_indices.append(i)
            else: block.bad_words.append(word)
    print('extracted:',len(block.extracted_eeg_words),
        'excluded:',len(block.bad_words))
    return True

def block2average(block,value_dict,count_dict, nsamples = 1300):
    for d in block.extracted_eeg_words:
        for i,ch in enumerate(block.ch):
            if ch not in value_dict.keys():
                value_dict[ch] = np.zeros(nsamples)
                count_dict[ch] = 0
            value_dict[ch] += d[i,:]
            count_dict[ch] += 1
    return value_dict, count_dict
            
        
            

def extract_word_eeg_data(data, word, block_st_sample,epoch = [-300,1000], 
    threshold = 75):
    '''Extract a word epoch from numpy array (data).
    data        numpy array
    word        word object with word information
    block_st... start sample of the block
    epoch       start and end sample of the epoch relative to the word onset
    threshold   maximum value of the abs(EEG data)
    '''
    epoch_st, epoch_et = epoch
    assert epoch_et > epoch_st
    st = word.st_sample + epoch_st - block_st_sample
    et = word.st_sample + epoch_et - block_st_sample
    if st < 0 or et > data.shape[1]:
        print('word is outside eeg data',word.__repr__(),word.word)
        return False
    d = data[:,st:et]
    if d.shape[0] == 0:
        print('eeg empty', word.__repr__(),'\n')
        return False
    if np.max(abs(d)) > threshold:
        print('eeg exceeds threshold', word.__repr__(),word.word)
        return False
    return d
        


def raw2np(raw, keep_channels = 'all', remove_bad_ch = True):
    '''Transform the MNE EEG datastructure to a numpy array.
    select the channels set to keep in the numpy array
    '''
    if keep_channels == 'all': 
        keep_channels = load_channel_set()
    elif keep_channels == 'default': 
        keep_channels = load_channel_set('default')
    elif type(keep_channels) == list: pass
    else: 
        m ='provide channel set type (all/default) or a list' 
        m += 'of channels to keep'
        raise ValueError(m)
    data = raw[:][0] * 10 ** 6
    ch_names = load_channel_set()
    remove_ch = [ch for ch in ch_names if ch not in keep_channels]
    if remove_bad_ch: remove_ch.extend(raw.info['bads'])
    ch_mask = [ch not in remove_ch for ch in ch_names]
    ch_names = [ch for ch in ch_names if not ch in remove_ch]
    print('selected channels:',' '.join(ch_names), len(ch_mask))
    print('removed channels:',' '.join(remove_ch))
    return data[ch_mask,:], ch_names, remove_ch
    

def load_channel_set(set_type = 'all'):
    '''load names of the EEG channels.
    set_type    the channel set to load
    all         contains all channel names
    default     contains the relevant eeg channel subset
    '''
    if set_type == 'all':
        f = locations.other_files_dir + 'channel_names.txt'
        ch = open(f).read().split('\n')
        ch.pop(ch.index('STI 014'))
        assert len(ch) == 30
    elif set_type == 'default':
        f = locations.other_files_dir + 'channel_set_default.txt'
        ch = open(f).read()
        ch = ch.split('\n')[:-1]
        assert len(ch) == 25
    else: print('unknown set type',set_type)
    return ch


def add_eeg_data(block, sf = 1000, freq = [0.05,30], apply_ica = True, 
    remove_bad_ch = True):
    '''Load the eeg data corresponding to a block in the experiment.
    block       block object created with read_xml
    sf          sample frequency, lower number to downsample the sf 
                (recorded with sf = 1000)
    freq        bandpass frequencies for filtering
    apply_ica   whether to apply ica decomposition to remove EOG activity
    remove...   whether to remove EEG channels with poor quality data
    '''
    #block.eeg_loaded = False
    block.raw = load_block(block, sf = sf, freq = freq)
    if block.raw != 0: block.eeg_loaded = True
    else: print('could not load eeg data')
    if remove_bad_ch: block.raw.info['bads'] = block.rejected_channels
    if apply_ica and not hasattr(block,'ica'): load_ica(block)
    else: 
        print('did not apply ica to remove eye related activity')
        if not hasattr(block,'ica'): block.ica_applied = False

def load_ica(block):
    '''load the ica decomposition corresponding to a specific block.
    the ica is fitted on data filtered with iir bandpass filter 1,30
    this attenuates ica sensitivity to slow drift (Winkler et al. 2015)
    '''
    if block.ica_fn == None or not os.path.isfile(block.ica_fn): 
        block.ica_applied= False
        return
    block.ica = mne.preprocessing.read_ica(block.ica_fn)
    block.ica.exclude = block.ica_remove_components
    block.raw.info['bads'] = block.rejected_channels
    if block.ica_remove_components != None: block.ica.apply(block.raw)
    block.ica_applied = True

def load_block(block, sf= 1000,freq = [0.05,30]):
    '''load eeg data corresponding to 1 block
    freq    set frequencies for bandpass filter, see filter_iir
    '''
    raw = load_eeg(block.vhdr_fn)
    start_sec = block.st_sample / 1000
    end_sec = block.et_sample / 1000
    if start_sec < 0: start_sec = 0
    if end_sec > (len(raw) /1000):
        end_sec = int(len(raw)/1000)
    
    raw.crop(tmin = start_sec, tmax = end_sec)
    raw.load_data()
    raw = rereference(raw)
    raw = filter_iir(raw, freq = freq)
    raw = make_eog_diff(raw)

    if sf != 1000:
        print('resampling data to sf:',sf)
        raw.resample(sfreq = sf)

    m = mne.channels.make_standard_montage('easycap-M1')
    raw.set_montage(m)
    return raw


def load_eeg(vhdr_fn = None, block = None,preload = False):
    '''Load the eeg data based on vhdr filename and crop to length of block.
    if all the data of a session is loaded extreme values are loaded, 
    because recording continued during breaks,
     this has an adverse effect on filtering.
    default only loads data corresponding to an experimental block.
    '''
    if block == vhdr_fn == None: 
        print('please provide block or vhdr filename')
        return
    if block: vhdr_fn = block.vhdr_fn
    return mne.io.read_raw_brainvision(vhdr_fn, preload = preload)

def rereference(raw):
    '''Rereference data to linked left and right mastoid electrodes.'''
    print('add empty reference channel LM and use reference \
    function to use average of LM and TP10_RM (average of mastoids)')
    # adds an empty channel (all zeros, for the left mastiod
    r = mne.add_reference_channels(raw,'LM',True)
    # rereference to the mean of the LM and RM
    r.set_eeg_reference(ref_channels = ['LM','TP10_RM'])
    # I visually (plot) checked that the RM value is half of 
    # what is was before
    #to be able to set montage (electrode locations) reference electrodes
    # (and eog) should not be of type eeg
    r.set_channel_types({'TP10_RM':'misc','LM':'misc'})
    return r


def filter_iir(raw,order = 5,freq = [0.05,30],sf = 1000,
    pass_type = 'bandpass', verbose = False):
    '''Filter data with butterworth filter.
    # MNE default =  iir_params is None and method="iir",
    5th order Butterworth will be used

    - 'iir' will use IIR forward-backward filtering (via filtfilt).
    - default: bandpass filter butterworth order 5 0.05 - 30 Hz
    - Filtering is done in place
    - Pad length (number of samples pre post data is 
      calculated automatically)
    '''
    iir_params = dict(order=order, ftype='butter',output = 'sos')
    iir_params = mne.filter.construct_iir_filter(iir_params, freq,None,sf, \
    pass_type, return_copy = False)
    if verbose:
        print('creating IIR butterworth filter with following params:\n',
            iir_params)
        print('frequency cut off:','\t',freq)
        print('sample frequency:',sf)
        print('filter pass_type:',pass_type)
    if pass_type == 'bandpass':
        raw.filter(iir_params =iir_params,l_freq= freq[0],
            h_freq=freq[1],method = 'iir')
    else:
        raw.filter(iir_params =iir_params,l_freq = None,
            h_freq=freq,method = 'iir')
        raw.iir_params = iir_params # add params to raw object 
    return raw 



def make_eog_diff(raw):
    '''Make VEOG and HEOG channels 
    (difference wave between up low / left right.
    '''
    raw = make_diff_wav(raw,'Fp1_EOG_V_high','Oz_EOG_V_low','VEOG',False)
    raw = make_diff_wav(raw,'FT9_EOG_H_left','FT10','HEOG',False)
    raw.set_channel_types({'VEOG':'eog','HEOG':'eog'})
    return raw

def make_diff_wav(raw,ch_name1,ch_name2,new_ch_name,copy = True):
    '''Make difference wave from two channels.
    Subtract ch2 from ch1 and store it in ch1 and name it new_ch_name
    If copy is true only return difference wave
    Else return difference wav and delete ch1 and ch2.
    '''
    if copy: output = raw.copy()
    else: output = raw
    i1 = output.ch_names.index(ch_name1)
    i2 = output.ch_names.index(ch_name2)
    output[i1][0][0] = output[i1][0][0] - output[i2][0][0]
    output.rename_channels({ch_name1:new_ch_name})
    if copy: output.pick_channels([new_ch_name])
    else: output.drop_channels([ch_name2])
    return output

def check_word_usability(block,word):
    '''check whether a word is usable
    block       object with block info made with read_xml
    word        object with word info (should be from block) 
                made with read_xml
    '''
    artefacts = block2artefacts(block)
    artefact_overlap = check_overlap(word,artefacts)
    word.artefact_overlap = artefact_overlap
    if (word.overlap or artefact_overlap or '*' in word.word or 
        'ggg' == word.word or 'xxx' == word):
        word.usable = False
        if verbose:
            print(word.__repr__(),'| word-overlap:',
                word.overlap,'| artefact-overlap:',artefact_overlap,
                '|',word.word)
    else: word.usable = True

def block2artefacts(block):
    '''creates a list of tuples whereby each tuple contains the start 
    and end sample of an artefact in the EEG data of a block.
    block       object with block info made with read_xml
    '''
    if block.artefact_st == None: return []
    return list(zip(block.artefact_st,block.artefact_et))

def check_overlap(word,artefacts):
    '''checks whether a word overlaps with any of the artefacts.
    word        object with word info made with read_xml
    artefacts   list of tuples with start and end samples of 
                artefacts in a block
    '''
    for a in artefacts:
        a_st, a_et = a
        artefact_overlap = compute_overlap(word.st_sample,
            word.et_sample,a_st,a_et)
        if artefact_overlap > 0: return True


def compute_overlap(start_a,end_a,start_b, end_b):
    '''compute the percentage b overlaps with a.
    if overlap = 1, b is equal in length or larger than a 
    and starts before or at the same time as a and
    b ends later or ate the same time as a.
    '''
    # print(start_a,end_a,start_b,end_b)
    if end_a < start_a:
        raise ValueError(' function assumes increasing intervals',
            start_a,end_a)
    if end_b < start_b:
        raise ValueError(' function assumes increasing intervals',
            start_b,end_b)
    if end_b <= start_a or start_b >= end_a: 
        return 0 # b is completely before or after a
    elif start_a == start_b and end_a == end_b: 
        return end_a - start_a # a and b are identical
    elif start_b < start_a: 
        # first statement already removed b cases completely before a
        if end_b < end_a: 
            # b starts before a and ends before end of a   
            return end_b - start_a 
        else: 
            # b starts before a and ends == or after end of a
            return end_a - start_a 
    elif start_b < end_a: 
        # first statement already romve b cases completely after a
        if end_b > end_a: 
            #b starts after start of a and ends == or after end of a
            return end_a - start_b 
        else: 
            # b starts after start of a and ends before end of a #
            return end_b - start_b  
    else:  print('error this case should be impossible')
