import mne
import mne_connectivity


# This will analyze theta band power spectra for eeg channels and corresponding audio
# Assumes that you have already collected data for a given number of phrases and utterances using phrase_search.py

def tfa_audio_eeg_phrases(phrase_data,band=['Theta',4,8]):
    all_band_data = {}
    for utt_i in range(len(phrase_data)):
        utt = list(phrase_data.keys())[utt_i]
        utt_bands = []
        num_participants = len(phrase_data[utt])
        for participant in range(num_participants):
            combined = []
            participant_data = phrase_data[utt][participant][0]
            eeg_data = participant_data[0]
            bad_channels = participant_data[2]
            all_channels = ['Fz', 'F3', 'F7', 'FC5', 'FC1', 'C3', 'T7', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'O2', 'P4', 'P8', 'CP6', 'CP2', 'Cz', 'C4', 'T8', 'FC6', 'FC2', 'F4', 'F8']
            channels = [str(x) for x in all_channels if str(x) not in bad_channels]
            raw_audio=[participant_data[1]] # must be specified as an array
            eeg_info=mne.create_info(ch_names=channels,sfreq=1000)
            audio_info=mne.create_info(ch_names=['Speech'],sfreq=1000)
            mne_eeg = mne.io.RawArray(eeg_data,info=eeg_info)
            mne_audio = mne.io.RawArray(raw_audio,info=audio_info)
            shortest=min(mne_eeg.__len__()/1000,mne_audio.__len__()/1000)-0.001
            eeg_cropped=mne_eeg.crop(tmax=shortest)
            audio_cropped=mne_audio.crop(tmax=shortest)
            combined=eeg_cropped.add_channels([audio_cropped],force_update_info=True)
            ch_w_speech=channels
            ch_w_speech.append('Speech')
            combined.apply_hilbert(envelope=True,picks=ch_w_speech)
            tfa_band=combined.compute_psd(fmin=band[1],fmax=band[2],picks=ch_w_speech,method='multitaper')
            utt_bands.append([tfa_band,ch_w_speech])
        all_band_data.update({utt:utt_bands})
    return all_band_data

def plot_phrase_band_data(phrase, band_data):
    phrase_bands = band_data[phrase]
    for participant in range(len(phrase_bands)):
        band, picks =phrase_bands[participant]
        band.plot(picks=picks,show=True)

# This will compute the phase-locking value between the audio and each eeg channel for each participant across a set of phrases generated from phrase_search.py
def plv_audio_eeg_phrases(phrase_data,band=['Theta',4,8]):
    all_band_data = {}
    for utt_i in range(len(phrase_data)):
        utt = list(phrase_data.keys())[utt_i]
        utt_bands = []
        num_participants = len(phrase_data[utt])
        for participant in range(num_participants):
            p_data = []
            participant_data = phrase_data[utt][participant][0]
            eeg_data = participant_data[0]
            bad_channels = participant_data[2]
            all_channels = ['Fz', 'F3', 'F7', 'FC5', 'FC1', 'C3', 'T7', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'O2', 'P4', 'P8', 'CP6', 'CP2', 'Cz', 'C4', 'T8', 'FC6', 'FC2', 'F4', 'F8']
            channels = [str(x) for x in all_channels if str(x) not in bad_channels]
            raw_audio=[participant_data[1]] # must be specified as an array
            ch_vals=[]
            for channel in channels:
                ch_index = [i for i in range(len(channels)) if channels[i]==channel]
                eeg_info=mne.create_info(ch_names=[str(channel)],sfreq=1000)
                audio_info=mne.create_info(ch_names=['Speech'],sfreq=1000)
                mne_eeg = mne.io.RawArray(eeg_data[ch_index],info=eeg_info)
                mne_audio = mne.io.RawArray(raw_audio,info=audio_info)
                shortest=min(mne_eeg.__len__()/1000,mne_audio.__len__()/1000)-0.001
                eeg_cropped=mne_eeg.crop(tmax=shortest)
                audio_cropped=mne_audio.crop(tmax=shortest)
                combined=eeg_cropped.add_channels([audio_cropped],force_update_info=True)
                ch_w_speech=[str(channel)]
                ch_w_speech.append('Speech')
                combined.apply_hilbert(envelope=True,picks=ch_w_speech)
                fake_events=mne.make_fixed_length_events(combined,start=0, duration=shortest)
                fake_epochs=mne.Epochs(combined,fake_events,tmin=0,tmax=shortest,reject_by_annotation=False,baseline=(0,0))
                plv=mne_connectivity.spectral_connectivity_time(fake_epochs,freqs=[band[1],band[2]],fmin=band[1],fmax=band[2], method='plv')
                ch_vals.append([channel,plv])
            p_data.append(ch_vals)
        utt_bands.append(p_data)
        all_band_data.update({utt:utt_bands})
    return all_band_data
    