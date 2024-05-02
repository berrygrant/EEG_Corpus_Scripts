import librosa
import locations

# Helper function to find an ordered subarray. Useful for word/phrase search.
# Note: Will only find the first complete result for now. Returns bool for match and the start and end indices of the subarray

def find_subarray(word_array, target_subarray):
	n = len(word_array)
	m = len(target_subarray)
	
	for i in range(n - m + 1):
		if word_array[i:i+m] == target_subarray:
			return [True,i, i + m - 1]    
	return [False,0,0]

#More elaborate function to search through a set of participant data generated by get_data_sample

def get_participant_phrase_data(phrase,participant):
	phrase_split = phrase.lower().split(' ')
	blocks = len(participant.blocks)
	for bi in range(0,blocks):
		block = participant.blocks[bi]
		block_name = block.name
		block_words=block.words
		word_list=[x.word.lower() for x in block_words]
		tf,s,e = find_subarray(word_list,phrase_split)
		if tf == True:
			bad_electrodes = block.rejected_channels
			block_eeg = block.data
			phrase_st = block_words[s].st
			phrase_et = block_words[e].et
			wav=block.wav_filename
			sound_sample = librosa.load(locations.cgn_audio+str(wav), sr=1000,offset=phrase_st,duration=phrase_et-phrase_st)[0]
			eeg_s = block_words[s].st_sample-block.st_sample
			eeg_e = block_words[e].et_sample-block.st_sample + 1 # for slicing [:]
			phrase_eeg=block_eeg[:,eeg_s:eeg_e]
			return phrase_eeg, sound_sample, bad_electrodes, [wav,block,participant],[phrase_st,phrase_et],[eeg_s,eeg_e] 
	return None

# General function to search for a set of phrases for a set of participants. Again, this function assumes you have participant data loaded
def find_all_phrases(phrases,participants):
	phrase_data={}
	for phrase in phrases:
		participant_data=[]
		for participant in range(len(participants)):
			data=get_participant_phrase_data(phrase,participants[participant])
			if data!=None:
				participant_data.append([data,participant])
		phrase_data.update({phrase:participant_data})
	return phrase_data


# To add: PhraseData class with attributes
