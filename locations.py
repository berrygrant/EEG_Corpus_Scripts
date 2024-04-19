# Note: Ported from https://github.com/martijnbentum/DESRC/tree/master
import glob
import os

#change this to the directory of the corpus
corpus_dir= '/Volumes/Corpus_Studies/Corpora/Nijmegen_EEG_Corpus/'
#change this to the directory of the CGN audio files:
cgn_audio= '/Volumes/Grants_Flas/CGN/audio/'
#change this to the directory of the IFADV audio files:
#ifadv_audio = '/vol/tensusers/mbentum/IFADV/WAV_16KHZ/'

#you do not need to change this
eeg_dir = corpus_dir + 'EEG/'
other_files_dir = corpus_dir + 'EEG_DATA_ifadv_cgn/'
artefacts_dir = other_files_dir + 'ARTEFAC_ANNOTATIONS/'
excluded_dir = other_files_dir + 'BADS_ANNOTATIONS/'
ica_dir = other_files_dir + 'ICA_SOLUTIONS/'
info_dir = other_files_dir + 'INFO/'
log_dir = other_files_dir + 'log/'
metadata_xml_dir = corpus_dir + 'XML_INFO/'

comp_o= cgn_audio + 'comp-o/nl/'
#comp_k= cgn_audio + 'comp-k/nl/'

fn = glob.glob(metadata_xml_dir + '*')
participant_xml_dirs = [x for x in fn if os.path.isdir(x)]

def participant_xml_dir_dict():
    temp,o = {},{}
    for d in participant_xml_dirs:
        pp_id = int(d.split('PP')[-1])
        temp[pp_id] = d + '/'
    for k in sorted(temp.keys()):
        o[k] = temp[k]
    return o
