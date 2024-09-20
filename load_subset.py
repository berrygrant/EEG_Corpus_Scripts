import locations
import read_xml
import load_eeg
from contextlib import contextmanager
import sys
import os

# Note that when unload_eeg = False (the default), the EEG data is added onto the participant data and is redundant

# Function to remove printout from loading participants
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

# Function to sample the first n participants or to load specific participants by specifying their numbers in an array
def get_data_sample(n=0, sample=[], eeg=True):
    eeg_data = []
    participants = []
    if n != 0:
        print("Getting data for first {} participants. This may take a while".format(n))
        with suppress_stdout():
            for i in range(1, n + 1):
                participants.append(read_xml.load_participant(i, add_words=True))
            if eeg != False:
                for i in range(0, n):
                    eeg_data.append(load_eeg.load_word_epochs_participant(participants[i], unload_eeg=False))
        return participants, eeg_data
    elif sample != []:
        s_dict = {}
        print("Loading data for participants {}. This may take a while".format(sample))
        with suppress_stdout():
            for index in range(len(sample)):
                s_dict.update({index: sample[index]})
            for participant in range(len(s_dict)):
                participants.append(read_xml.load_participant(s_dict[participant], add_words=True))
        if eeg != False:
            for i in range(len(participants)):
                eeg_data.append(load_eeg.load_word_epochs_participant(participants[i], unload_eeg=False))
    else:
        print("Please indicate either a sample size or an array with specific participant numbers")
        return [], []
    print(rep("-",20))
    print("\n")
    print("Now checking for missing block data...")
    valid_participants = []
    valid_eeg_data = []
    for j in range(len(participants)):
        participant = participants[j]
        print(f"Participant {participant} blocks: {participant.nblocks_missing}")
        if participant.nblocks_missing > 0:
            print(f"Participant {participant.name} has missing block data. Discarding...")
        else:
            valid_participants.append(participants[j])
            if eeg != False:
                valid_eeg_data.append(eeg_data[j])
    if sample != []:
        initial_sample_size = len(sample)
    else:
        initial_sample_size = n
    loss = initial_sample_size - len(participants)
    print(f"Final sample size: {len(participants)}. Loss: {loss}")
    return valid_participants, valid_eeg_data

# Need to create a class to hold data so that I don't have to worry about formatting arrays
def get_phrases_only(n, phrases):
    all_data = {}
    for participant in range(1, n + 1):
        print("Loading data for participant {}".format(participant))
        with suppress_stdout():
            participant_data = read_xml.load_participant(participant, add_words=True)
            participant_eeg = load_eeg.load_word_epochs_participant(participant_data, unload_eeg=False)
        phrase_data = []
        for phrase in phrases:
            print("Finding phrase {}".format(phrase))
            phrase_data_participant = None
            try:
                phrase_data_participant = phrase_search.get_participant_phrase_data(phrase, participant_data)
            except Exception as e:
                print("\tERROR OCCURRED: {}".format(e))
            if phrase_data_participant is not None:
                phrase_data.append((phrase, phrase_data_participant))
            else:
                print("\tCould not find {}. Skipping...".format(phrase))
        all_data.update({participant: phrase_data})
    del participant_data
    return all_data
