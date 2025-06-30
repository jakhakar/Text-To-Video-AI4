# utility/captions/timed_captions_generator.py

import whisper_timestamped as whisper
import re

# This function is the main entry point for the module.
def generate_timed_captions(audio_filename, model_size="base"):
    model = whisper.load_model(model_size, device="cpu")
    result = whisper.transcribe_timestamped(model, audio_filename, verbose=False, fp16=False)
    # The output of getCaptionsWithTime is what we will work with.
    return getCaptionsWithTime(result)

# All the helper functions below are correct as you've provided them.
def splitWordsBySize(words, maxCaptionSize):
    captions = []
    while words:
        caption = words[0]
        words = words[1:]
        while words and len(caption + ' ' + words[0]) <= maxCaptionSize:
            caption += ' ' + words[0]
            words = words[1:]
        if len(caption) >= (maxCaptionSize / 2) and words:
            break
        captions.append(caption)
    return captions

def getTimestampMapping(whisper_analysis):
    index = 0
    locationToTimestamp = {}
    for segment in whisper_analysis['segments']:
        for word in segment['words']:
            newIndex = index + len(word['text']) + 1
            locationToTimestamp[(index, newIndex)] = word['end']
            index = newIndex
    return locationToTimestamp

def cleanWord(word):
    return re.sub(r'[^\w\s\-_"\']', '', word)

def interpolateTimeFromDict(word_position, d):
    for key, value in d.items():
        if key[0] <= word_position <= key[1]:
            return value
    return None

def getCaptionsWithTime(whisper_analysis, maxCaptionSize=15, considerPunctuation=False):
    wordLocationToTime = getTimestampMapping(whisper_analysis)
    position = 0
    start_time = 0
    CaptionsPairs = []
    text = whisper_analysis['text']
    
    if considerPunctuation:
        sentences = re.split(r'(?<=[.!?]) +', text)
        words = [word for sentence in sentences for word in splitWordsBySize(sentence.split(), maxCaptionSize)]
    else:
        words = text.split()
        words = [cleanWord(word) for word in splitWordsBySize(words, maxCaptionSize)]
    
    for word in words:
        position += len(word) + 1
        end_time = interpolateTimeFromDict(position, wordLocationToTime)
        if end_time and word:
            CaptionsPairs.append(((start_time, end_time), word))
            start_time = end_time
    return CaptionsPairs
