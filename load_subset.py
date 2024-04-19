import locations
import read_xml
import load_eeg

# Note that when unload_eeg = False (the default), the EEG data is added onto the participant data and is redundant

# Function to sample the first n participants or to load specific participants by specifying their numbers in an array
def get_data_sample(n=0,sample=[],eeg=True):
    eeg_data = []
    participants = []
    if n!=0:
        print("Getting data for first {} participants. This may take a while".format(n))
        {participants.append(read_xml.load_participant(i,add_words=True)) for i in range(1,n+1)}
        {eeg_data.append(load_eeg.load_word_epochs_participant(participants[i],unload_eeg=False)) for i in range(0,n) if eeg!=False}
        return participants, eeg_data
    if sample!=[]:
        s_dict={}
        print("Loading data for participants {}. This may take a while".format(sample))
        {s_dict.update({index:sample[index]}) for index in range(len(sample))}
        {participants.append(read_xml.load_participant(s_dict[participant],add_words=True))for participant in range(len(s_dict))}
        {eeg_data.append(load_eeg.load_word_epochs_participant(participants[i],unload_eeg=False)) for i in range(0,n) if eeg!=False}
    else:
        print("Please indicate either a sample size or an array with specific participant numbers")
    return participants,eeg_data