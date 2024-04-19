#Note: Ported from https://github.com/martijnbentum/DESRC/tree/master
from lxml import etree
import locations 

pp_dirs = locations.participant_xml_dir_dict()

def load_all_participants(add_words = True):
    '''Load EEG experiment information for all participants.
    add_words       loads the word information of all words in the speech
                    materials participants listened while their EEG 
                    was recorded (increases loading time)
    '''
    participants = []
    for i in range(1,49):
        print('loading participant:',i)
        participants.append(load_participant(i,add_words))
    return participants


def load_participant(pp_id = 1,add_words = False):
    '''This load the experimental information related to 1 participant.
    sessions and blocks are nested within this object
    add_words       loads word information for all words in a block
                    words are nested within a block
    '''
    p = read_participant(pp_id)
    s = read_sessions(pp_id)
    b = read_blocks(pp_id, add_words)
    setattr(p,'sessions',s)
    setattr(p,'blocks',b)
    for s in p.sessions:
        exp_name = s.name.split('_')[-1]
        sb = [b for b in p.blocks if exp_name in b.name]
        setattr(s,'blocks',sb)
    return p


def read_blocks(pp_id = 1, add_words = False,get_names = False):
    '''A block is a ~15 minute section of an EEG recording session
    participant could take break after each block.
    '''
    blocks = []
    pp_dir = pp_dirs[pp_id]
    filename = pp_dir + 'blocks.xml'
    xml = etree.fromstring(open(filename).read())
    names = 'pp_id,exp_type,name,experiment_name,corpus,block_number,st'
    names += ',et,duration,st_sample,et_sample,duration_sample,sample_inacc'
    names += ',nallwords,ncontent_words,wav_filename,nartefacts,fids,fid_st'
    names += ',fid_et,artefact_st,artefact_et,artefact_fn,ica_fn,eog_fn'
    names += ',ica_remove_components,rejected_channels,usability,vmrk_fn'
    names += ',vhdr_fn,eeg_fn,block_duration,artefacts_duration'
    names = names.split(',')
    if get_names: return names
    integers = 'pp_id,block_number,st_sample,et_sample,duration_sample'
    integers +=',sample_inacc,nallwords,ncontent_words,nartefacts,fid_st'
    integers += ',fid_et,artefact_st,artefact_et,ica_remove_components'
    integers = integers.split(',')
    floats = 'artefacts_duration,block_duration'.split(',')
    lists = 'fids,fid_st,fid_et,artefact_st,artefact_et'
    lists += ',ica_remove_components,rejected_channels'
    lists = lists.split(',')
    add_location = 'artefact_fn,eeg_fn,eog_fn,ica_fn,vhdr_fn,vmrk_fn'
    add_location = add_location.split(',')
    for b in xml.iter('block'):
        block = dummy_object('block')
        for name in names:
            text = b.find(name).text
            if text == 'NA' or text == '' or text == None: o = None
            elif name in lists:
                o = text.split(',')
                if name in integers: o = list(map(int,o))
            elif name in integers: o = int(text)
            elif name in floats: o = float(text)
            else: o = text
            if name in add_location and o:
                o = _add_corpus_location_to_filename(o)
            setattr(block,name,o)
        block.xml_filename = filename
        if add_words: setattr(block,'words',read_words(block))
        blocks.append(block)    
    return blocks

def read_participant(pp_id = 1):
    '''A participant participated in three EEG recorded session.
    each session consisted of multiple blocks.
    Session were separated by at least one week.
    Speech from one specific register (books, news, dialogues) was presented
    '''
    participant = dummy_object('participant')
    pp_dir = pp_dirs[pp_id]
    filename = pp_dir + 'participant.xml'
    names = 'pp_id,nallwords,ncontent_words,nartefacts,dates_sessions'
    names += ',names_sessions,nblocks_missing,names_block_missing'
    names += ',blocks_duration,artefacts_duration'
    names = names.split(',')
    integers = 'pp_id,nallwords,ncontent_words,nartefacts,nblocks_missing'
    integers = integers.split(',')
    floats = 'blocks_duration,artefacts_duration'.split(',')
    lists= 'dates_sessions,names_sessions'.split(',')
    xml = etree.fromstring(open(filename).read())
    for name in names:
        text = xml.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        elif name in integers: o = int(text)
        elif name in floats: o = float(text)
        elif name in lists: o = text.split(',')
        else: o = text
        setattr(participant,name,o)
    setattr(participant,'name','PP'+str(pp_id))
    participant.xml_filename = filename
    return participant
    
def read_sessions(pp_id = 1):
    '''A session is a separate EEG recording session of ~90 minutes 
    consisting of multiple blocks.'''
    sessions = []
    pp_dir = pp_dirs[pp_id]
    filename = pp_dir + 'sessions.xml'
    names = 'pp_id,exp_type,name,experiment_name,session_number'
    names += ',n_eeg_recordings,start_exp,end_exp,duration'
    names += ',nblocks,nallwords,ncontent_words'
    names += ',nartifacts,fids,fids_missing,usability,answer_fn,log_fn'
    names += ',vmrk_fn,vhdr_fn,eeg_fn,block_names,nblocks_missing'
    names += ',blocks_duration,artefacts_duration'
    names = names.split(',')
    integers = 'pp_id,session_number,n_eeg_recordings,nblocks,nallwords'
    integers = ',ncontent_words,nartefacts,nblocks_missing'
    integers = integers.split(',')
    floats = 'blocks_duration,artefacts_duration'.split(',')
    lists = 'fids_missing,usability,vmrk_fn,vhdr_fn,eeg_fn,block_names'
    lists = lists.split(',')
    nested_lists = ['fids']
    add_location = 'answer_fn,eeg_fn,log_fn,vhdr_fn,vmrk_fn'
    add_location = add_location.split(',')
    xml = etree.fromstring(open(filename).read())
    for s in xml.iter('session'):
        session = dummy_object('session')
        for name in names:
            text = s.find(name).text
            if text == 'NA' or text == '' or text == None: o = None
            elif name in integers: o = int(text)
            elif name in floats: o = float(text)
            elif name in lists: o = text.split(',')
            elif name in nested_lists: 
                o = [fids.split('|') for fids in text.split(',')]
            else: o = text
            if name in add_location and o:
                o = _add_corpus_location_to_filename(name)
            setattr(session,name,o)
        session.xml_filename = filename
        sessions.append(session)
    return sessions

        

        
def read_words(block = None):
    '''Participants listened to speech.
    Each word in the speech materials is time locked to the EEG materials
    Words are grouped within a block (~15 minutes of the EEG experiment)
    and blocks are grouped in a session (one ~90 minute recording session)
    word info can be found in this object
    extra info can be found in the nested objects: 
    phoneme_word, pos, ppl, stats 

    Words can be read by providing a block name
    '''
    if not block:block_name = 'pp1_exp-o_bid-1'
    else: block_name = block.name
    words = []
    pp_id = int(block_name.split('_')[0].strip('p'))
    pp_dir = pp_dirs[pp_id]
    word_dir = pp_dir  + 'WORDS/'
    filename = word_dir + block_name + '.xml'
    names = 'word_utf8_nocode,st_sample,et_sample,duration_sample,st,et,eol'
    names += ',fid,sid,overlap,corpus,register,word,fid_st_sample'
    names += ',block_name,word_index_in_block'
    names = names.split(',')
    integers = 'st_sample,et_sample,fid_st_sample,word_index_in_block'
    integers = integers.split(',')
    floats = 'st,et'.split(',')
    booleans = ['overlap']
    xml = etree.fromstring(open(filename).read())
    for w in xml.getchildren():
        word = dummy_object('word')
        for name in names:
            temp = w.find(name)
            if not hasattr(temp,'text'): return w
            text = w.find(name).text
            if text == 'NA' or text == '' or text == None: o = None
            elif name in integers: o = int(text)
            elif name in floats: o = float(text)
            elif name in booleans: o = True if text == 'True' else False
            else: o = text
            setattr(word,name,o)
        setattr(word,'pos',_read_pos(w))
        setattr(word,'stats',_read_stats(w))
        setattr(word,'ppl',_read_ppl(w))
        setattr(word,'phoneme_word',_read_phoneme_word(w))
        setattr(word,'name',w.attrib['id'])
        word.block = block
        word.xml_filename = filename
        words.append(word)
    return words

def _read_pos(xml_word):
    '''Part of speech information.'''
    pos = dummy_object('pos')
    p = xml_word.find('pos')
    if p == None: return None
    names = 'lemma,morphological_segmentation,pos,pos_simple,pos_tag'
    names += ',probability_of_tag,content_word,base_phrase_chunk'
    names = names.split(',')
    floats = ['probability_of_tag']
    booleans = ['content_word']
    for name in names:
        text = p.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        elif name in booleans: o = True if text == 'True' else False
        elif name in floats: o = float(text)
        else: o = text
        setattr(pos,name,o)
    return pos

def _read_stats(xml_word):
    '''Information theoretic information. 
    Language modelling information see ppl'''
    stats= dummy_object('stats')
    s = xml_word.find('stats')
    names = 'word_frequency,entropy,updated_entropy,cross_entropy'
    names += ',logprob,gate,word_number,word_code,updated_logprob'
    names = names.split(',')
    integers = 'word_frequency,gate'.split(',')
    floats = 'entropy,updated_entropy,cross_entropy,logprob,updated_logprob'
    floats = floats.split(',') 
    for name in names:
        text = s.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        elif name in integers: o = int(text)
        elif name in floats: o = float(text)
        else: o = text
        setattr(stats,name,o)
    return stats

def _read_ppl(xml_word):
    '''Language modelling in formation.'''
    ppl = dummy_object('ppl')
    p = xml_word.find('ppl')
    if p == None: return None
    names = 'ngram,oov,p,logprob,p_register,logprob_register,p_other1'
    names += ',logprob_other1,p_other2,logprob_other2,word_id'
    names += ',word_index_sentence'
    names = names.split(',')
    integers = 'ngram,word_index_sentence'.split(',')
    floats = 'p,logprob,p_register,logprob_register,p_other1,logprob_other1'
    floats += ',p_other2,logprob_other2'
    floats = floats.split(',')
    booleans = ['oov']
    for name in names:
        text = p.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        elif name in integers: o = int(text)
        elif name in floats: o = float(text)
        elif name in booleans: o = True if text == 'True' else False
        else: o = text
        setattr(ppl,name,o)
    return ppl

def _read_phoneme_word(xml_word):
    '''All phonemes of the word in ipa.'''
    phoneme_word= dummy_object('phoneme_word')
    p = xml_word.find('phoneme_word')
    if p == None: return None
    names = 'cgn,ipa,nphonemes'.split(',')
    for name in names:
        text = p.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        else: o = text
        setattr(phoneme_word,name,o)
    phonemes = []
    for item in p.iter('phoneme'):
        phonemes.append(_read_phoneme(item))
    setattr(phoneme_word,'phonemes',phonemes)
    phoneme_word.name = phoneme_word.ipa
    return phoneme_word

def _read_phoneme(item):
    '''Phoneme specific information with EEG time lock information.'''
    phoneme= dummy_object('phoneme')
    names = 'index,cgn,ipa,st_sample,et_sample,duration_sample'.split(',')
    for name in names:
        text = item.find(name).text
        if text == 'NA' or text == '' or text == None: o = None
        else: o = text
        setattr(phoneme,name,o)
    phoneme.name = phoneme.ipa
    return phoneme
            

class dummy_object():
    '''object to hold information.'''
    def __init__(self,object_type = '', name = ''):
        '''Information container for the ESSC corpus. 
        Groups participant session block and word information.
        object_type         the information type (e.g. participant)
        name                instance name (e.g. pp1 => participant 1)
        '''
        self.object_type = object_type
        self.name = name

    def __repr__(self):
        if 'explanation' in self.object_type: name = 'field explanations'
        else: name = self.name
        m = self.object_type + ': ' + name
        return m

    def __str__(self):
        nested_objects = []
        d = self.__dict__
        x = len(max(list(d.keys()),key=len))
        m = bolunder +self.object_type+end + '\n' 
        for k in sorted(d.keys()):
            if type(d[k]) == dummy_object and not k.startswith('_'): 
                nested_objects.append(k)
            elif k == 'words' and type(d[k]) == list:
                m += bold+ k.ljust(x + 3)+ end 
                m += underline + 'word objects'+ end
                m += ': '+str(len(d[k])) +'\n'
            else:m += bold+ k.ljust(x + 3)+ end + str(d[k]) + '\n'
        if len(nested_objects) > 0:
            m += '\n'+bold+'nested objects:'.ljust(x + 3)+end 
            m += ' '.join(nested_objects)
        return m

    def explanation(self):
        '''show explanation for each field of an object.'''
        print(make_help(self))
    
        

def make_help(obj):
    '''create field explanation for an object (e.g. block)'''
    object_type= obj.object_type
    f = locations.metadata_xml_dir + 'info_explanation.xml'
    helper = dummy_object('explanation')
    xml_help = etree.fromstring(open(f).read())
    tags = [x.tag for x in xml_help.getchildren()]
    if not object_type in tags: return 'no help available'
    p = xml_help.find(object_type)
    if p == None: return xml_help
    for el in p.getchildren():
        text = el.text.replace('\t',' ').replace('\n','')
        setattr(helper,el.tag,text)
    return helper 
    

bold = '\033[1m'
underline = '\033[4m'
bolunder = '\033[1m\033[4m'
blue = '\033[94m'
red = '\033[91m'
end = '\033[0m'
        

def _add_corpus_dir(f):
    '''add corpus base dir to path if not present.'''
    if not f.startswith(locations.corpus_dir):
        f = locations.corpus_dir + f
    return f

def _add_corpus_location_to_filename(f):
    '''add corpus base dir to path(s) if not present.'''
    if type(f) == list:
        return [_add_corpus_dir(x) for x in f]
    return _add_corpus_dir(f)
