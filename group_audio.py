import numpy as np
import librosa
import locations
import soundfile as sf

def concatenate_convert_audio(sound,resfolder):
	files_needed = filter(lambda x: x.startswith("fn"),str.split(sound,"_"))
	count=1
	for file in files_needed:
		if count==1:
			concatenated=librosa.load(locations.cgn_audio+file+".wav",sr=1000)[0]
		else:
			audio=librosa.load(locations.cgn_audio+file+".wav",sr=1000)[0]
			np.concatenate((concatenated,audio))
			count += 1
	resfile=librosa.amplitude_to_db(concatenated,top_db=60)
	sf.write(resfolder+sound,resfile,samplerate=1000)
	print(f"{sound} has been converted.")

def convert_all_audio(input_list="audio_file_list.txt",resfolder="/home/mernestus/ERC_2024/PLV_PILOT/concatenated_audio/"):
	file_list = [line.strip() for line in open(input_list)]
	for file in file_list:
		concatenate_convert_audio(file,resfolder)
	return "All audio has been converted."
