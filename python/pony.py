import os
from moviepy.editor import *
from mutagen.aiff import AIFF
from mutagen.id3 import ID3, APIC, TALB, TIT2, TBPM, TCOM, TCON, TMOO, TYER, TRCK, TPE1, TKEY, COMM, TPE2, TPUB, GRP1
from mutagen.mp3 import MP3
import pandas
import pydub
import re
import shutil
import time
from timecode import Timecode


# *****************************************************************************
# HELPER FUNCTIONS NOT NORMALLY USED DIRECTLY BY THE USER
# SCROLL TO THE BOTTOM OF THE FILE TO SEE END USER FUNCTIONS
# *****************************************************************************

def log(msg, album="", track=""):
    print(msg)


def metaToListDictionary(meta_file, tab):
    retval = {}
    frame = pandas.read_excel(meta_file, tab)
    retval = frame.to_dict('list')

    # Now we have to do a little more clean up for Unnamed column
    
    # create a list of keys (copy) that will avoid modifying
    # retval while iterating with the object returned fron keys()
    keylist = []
    for key in retval.keys(): 
        keylist.append(key)

    #  cleanup fields and colums in retval
    for key in keylist:
        if key.startswith('Unnamed:'):
            del retval[key]
            continue
        clean = []
        dirty = retval[key]
        for i in dirty:
            if type(i) == str:  # getting rid of nan entries
                clean.append(i)
        retval[key] = clean        


    return retval


def nameFromDirectory(dir):
    abs_path = os.path.abspath(dir)
    retval = os.path.basename(abs_path)
    retval = re.sub('^[0-9]+ - ','', retval, count=1)
    if retval.startswith('Flows from '):
        retval = retval[11:]
    return retval


def applyNamingConvention(naming_convention, album_name, track_name, meta, formats, stem_name="", alt_name="", cut_name="" ):
    retval = "naming_convention_error"
    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]
    if len(matches) > 0:
        retval = formats[naming_convention][0]
        for fld in meta.columns:
            if fld != "artwork":
                sub_str = '!' + fld + '!'
                replacement = matches[fld][0]
                if not type(replacement) == str:
                    replacement = ''   
                retval = re.sub(sub_str, replacement, retval)
        if stem_name != "":
            retval = re.sub('!stem!', stem_name, retval)
        if alt_name != "":
            retval = re.sub('!alt!', alt_name, retval)
        if cut_name != "":
            retval = re.sub('!cut!', cut_name, retval)
                           
    return retval


def applySimplifiedNamingConvention(naming_convention, album_name, track_name, meta):
    retval = "naming_convention_error"
    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]
    if len(matches) > 0:
        retval = matches[naming_convention][0]
        for fld in meta.columns:
            if fld != "artwork":
                sub_str = '!' + fld + '!'
                replacement = matches[fld][0]
                if not type(replacement) == str:
                    replacement = ''   
                retval = re.sub(sub_str, replacement, retval)                       
    return retval         


def  createPruneOrIgnoreDirectory(dir, ignore):
    if not os.path.exists(dir):
        os.mkdir(dir)
    elif not ignore:
        shutil.rmtree(dir)
        os.mkdir(dir)     




def updateTagsID3(album_name, track_name, meta, destination, formats, environment, substitute_title=""):
    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]
    audio = 'not assigned'
    if destination.endswith('3'):
            audio = MP3(destination, ID3=ID3)
    else:
        audio = AIFF(destination)
        audio.add_tags()

    value = matches['album'][0]
    if value and (type(value) == str):
        audio.tags.add(TALB(text=[value]))

    value = matches['title'][0]
    if value and (type(value) == str):
        if(substitute_title == ""):
            audio.tags.add(TIT2(text=[value]))
        else:
            audio.tags.add(TIT2(text=[substitute_title]))    

    value = matches['bpm'][0]
    if value:
        audio.tags.add(TBPM(text=[value]))

    value = matches['composer'][0]
    if value and (type(value) == str):
        audio.tags.add(TCOM(text=[value])) 

    value = matches['genre'][0]
    if value and (type(value) == str):
        audio.tags.add(TCON(text=[value]))  

    value = matches['key'][0]
    if value and (type(value) == str):
        audio.tags.add(TKEY(text=[value]))

    value = matches['mood'][0]
    if value and (type(value) == str):
        audio.tags.add(TMOO(text=[value]))

    value = matches['artist'][0]
    if value and (type(value) == str):
        audio.tags.add(TPE1(text=[value]))
        
    value = matches['featured artist'][0]
    if value and (type(value) == str):
        audio.tags.add(TPE2(text=[value]))

    value = matches['grouping'][0]
    if value and (type(value) == str):
        audio.tags.add(GRP1(text=[value]))

    value = matches['publisher'][0]
    if value and (type(value) == str):
        audio.tags.add(TPUB(text=[value]))        

    value = matches['track'][0]
    if value:
        audio.tags.add(TRCK(text=[value]))

    value = matches['year'][0]
    if value:
        audio.tags.add(TYER(text=[value])) 

    # comments is a concatenated field, so its a little different
    value = applyNamingConvention('comment construction', album_name, track_name, meta, formats)
    if value:
        audio.tags.add(COMM(text=[value]))                                      
    
    artwork_file = matches["artwork"][0]
    if type(artwork_file) == str:
        image_path = environment["images and video"][0]
        artwork_file = os.path.join(image_path, artwork_file)
        art = open(artwork_file, 'rb').read()
        apic = APIC(
            data = art,
            type = 3,
            desc = "cover",
            mime = "image/jpeg" )
        
        audio.tags.add(apic)

    audio.save(destination)


def buildStemDictionary(meta_file, multi_dir, album_name, track_name):

    stem_dictionary = metaToListDictionary(meta_file, "Stems")
    stem_dictionary = dict(sorted(stem_dictionary.items()))

    retval = stem_dictionary.copy()
    retval['orphan'] = []

    # clear out the pattern values of the copy we just made of the stes
    #directoy because we only want its dictionary structure
    for clear_key in retval.keys():
        retval[clear_key] = []
    
    # Now run though the multitrack files and assign them to a stem
    for f in os.listdir(multi_dir):
        basename = os.path.basename(f)

        # skip any non-wavs that might have been added
        if not basename.endswith('.wav'):
            continue
        
        # process this multitrack file then
        hasStem = False
        for key in stem_dictionary.keys():
            if key == 'orphan' or hasStem :
                continue        
            instruments = stem_dictionary.get(key)
            for pattern in instruments:
                match = re.search(pattern, basename)
                if match and not hasStem:
                    retval[key].append(basename)
                    hasStem = True
                    break

        # if it doesn't match a stem in the dictionary then add to the orphan stem        
        if not hasStem:
            retval['orphan'].append(basename)
            log("*** WARNING *** no matching stem found for " + basename + ", added to orphan stem", album_name, track_name)    

    return retval




def buildAltDictionary(meta_file, multi_dir, album_name, track_name):
    alt_dictionary = metaToListDictionary(meta_file, "Alts")
    retval = alt_dictionary.copy()

    # clear out the pattern values of the copy we just made of the stes
    #directoy because we only want its dictionary structure
    for clear_key in retval.keys():
        retval[clear_key] = []
    
    # Now run though the multitrack files and assign them to a stem
    for f in os.listdir(multi_dir):
        basename = os.path.basename(f)

        # skip any non-wavs that might have been added
        if not basename.endswith('.wav'):
            continue
        
        # process this multitrack file then
        for key in alt_dictionary.keys():       
            instruments = alt_dictionary.get(key)
            for pattern in instruments:
                match = re.search(pattern, basename)
                if match:
                    retval[key].append(basename)
                    break 
    return retval


def timecodeToMillis(tc):
    temp = Timecode(25, tc )
    temp.set_fractional(True)
    secs = temp.secs * 1000
    mins = temp.mins * 60 * 1000
    hrs = temp.hrs * 60 * 60 * 1000
    return hrs + mins + secs


def buildCutDictionary(album_name, track_name, meta):
    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]
    retval = {}
    for x in meta.keys():
        if x.startswith("cut:"):
            key = str.strip(x[4:])
            raw_value =  matches[x][0] 
            if type(raw_value) != str:
                continue
            segments = raw_value.split(",")
            time_segments = []
            for i in segments:
                time_tuple = []
                xfade = i.split("x")
                if len(xfade) > 1:
                    temp = xfade[0].split("-")
                    time_tuple.append(timecodeToMillis(temp[0].strip()))
                    time_tuple.append(timecodeToMillis(temp[1].strip()))
                    time_tuple.append(int(xfade[1]))
                else:    
                    temp = i.split("-")
                    time_tuple.append(timecodeToMillis(temp[0].strip()))
                    time_tuple.append(timecodeToMillis(temp[1].strip()))
                    time_tuple.append(0)
                    
                time_segments.append(time_tuple)

            retval[key] = time_segments
    return retval


def export_WAV_44100_16(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(2)
    audio_segment.export(path, format='wav')

def export_WAV_44100_24(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(3)
    audio_segment.export(path, format='wav')

def export_WAV_44100_32(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(4)
    audio_segment.export(path, format='wav')

def export_WAV_48000_16(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(2)
    audio_segment.export(path, format='wav')

def export_WAV_48000_24(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(3)
    audio_segment.export(path, format='wav')

def export_WAV_48000_32(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(4)
    audio_segment.export(path, format='wav')

def export_AIFF_44100_16(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(2)
    audio_segment.export(path, format='aiff')

def export_AIFF_44100_24(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(3)
    audio_segment.export(path, format='aiff')

def export_AIFF_44100_32(path, audio_segment):
    audio_segment.set_frame_rate(44100)
    audio_segment.set_sample_width(4)
    audio_segment.export(path, format='aiff')

def export_AIFF_48000_16(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(2)
    audio_segment.export(path, format='aiff')

def export_AIFF_48000_24(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(3)
    audio_segment.export(path, format='aiff')

def export_AIFF_48000_32(path, audio_segment):
    audio_segment.set_frame_rate(48000)
    audio_segment.set_sample_width(4)
    audio_segment.export(path, format='aiff')

def export_MP3_128(path, audio_segment):
    audio_segment.export(path, format='mp3', bitrate="128k")

def export_MP3_192(path, audio_segment):
    audio_segment.export(path, format='mp3', bitrate="192k")

def export_MP3_320(path, audio_segment):
    audio_segment.export(path, format='mp3', bitrate="320k") 

def export_video(audio_track, video_clip, output_dir):
    log("Combining master audio with video")
    audio = AudioFileClip(audio_track)
    video = VideoFileClip(video_clip)
    final = video.set_audio(audio)
    output_path = os.path.join(output_dir, video_clip)
    final.write_videofile(output_path)


def export_still_video(audio_track, image_path, output_path):
    log("Combining master audio with a still image to create video version")
    audio = AudioFileClip(audio_track)
    image = ImageClip(image_path)
    video = image.set_audio(audio)
    video.duration = audio.duration
    video.fps = 1
    video.write_videofile(output_path)             


def exportRequiredFormats(album_name, track_name, meta, basename, song, audio_formats, formats, environment, substitute_title=""):
    for export_format in audio_formats:
        export_format = export_format.strip()
        if export_format == 'WAV_44100_16':
            export_WAV_44100_16(basename + '.wav', song)
        elif export_format == 'WAV_44100_24':
            export_WAV_44100_24(basename + '.wav', song)
        elif export_format == 'WAV_44100_32':
            export_WAV_44100_32(basename + '.wav', song) 
        elif export_format == 'WAV_48000_16':
            export_WAV_48000_16(basename + '.wav', song)
        elif export_format == 'WAV_48000_24':
            export_WAV_48000_24(basename + '.wav', song)
        elif export_format == 'WAV_48000_32':
            export_WAV_48000_32(basename + '.wav', song)
        elif export_format == 'AIFF_44100_16':
            export_AIFF_44100_16(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title) 
        elif export_format == 'AIFF_44100_24':
            export_AIFF_44100_24(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title) 
        elif export_format == 'AIFF_44100_32':
            export_AIFF_44100_32(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title) 
        elif export_format == 'AIFF_48000_16':
            export_AIFF_48000_16(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title)  
        elif export_format == 'AIFF_48000_24':
            export_AIFF_48000_24(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title)
        elif export_format == 'AIFF_48000_32':
            export_AIFF_48000_32(basename + '.aiff', song)
            updateTagsID3(album_name, track_name, meta, basename + '.aiff', formats, environment, substitute_title=substitute_title) 
        elif export_format == 'MP3_128':
            export_MP3_128(basename + '.mp3', song)
            updateTagsID3(album_name, track_name, meta, basename + '.mp3', formats, environment, substitute_title=substitute_title) 
        elif export_format == 'MP3_192':
            export_MP3_192(basename + '.mp3', song)
            updateTagsID3(album_name, track_name, meta, basename + '.mp3', formats, environment, substitute_title=substitute_title)
        elif export_format == 'MP3_320':
            export_MP3_320(basename + '.mp3', song)
            updateTagsID3(album_name, track_name, meta, basename + '.mp3', formats, environment, substitute_title=substitute_title)         



def backupTrack(meta, formats, track_dir, album_name, track_name, environment):
    backup_dir = environment["backup"][0]
    if backup_dir:
        backup_dir = os.path.join(backup_dir, album_name)
        backup_dir = os.path.join(backup_dir, track_name)
        if backup_dir:
            log("\n", album_name, track_name)
            log("Copying production output to backup location " + backup_dir, album_name, track_name)
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            shutil.copytree(track_dir, backup_dir)



def oneCutInternal(key, source_path, cuts_dir, audio_segments, audio_format_list, meta, formats, environment, album_name, track_name, prefix = ""):
    cut_file_name = applyNamingConvention('cut naming', album_name, track_name, meta, formats, cut_name = key)
    if prefix:
        cut_file_name = prefix + " " + applyNamingConvention('cut suffix naming', album_name, track_name, meta, formats, cut_name = key)
    
    cut_file_path_no_ext = os.path.join(cuts_dir, cut_file_name)
    
    if(len(audio_segments) > 0):
        src_audio = pydub.AudioSegment.from_file(source_path)
        audio = False # we will reassign this in a minutes
        for s in audio_segments: 
            if not audio :
                audio = src_audio[s[0] : s[1]]
            else:
                dub = src_audio[s[0] : s[1]]
                audio = audio.append(dub, crossfade=s[2])

    exportRequiredFormats(album_name, track_name, meta, cut_file_path_no_ext, audio, audio_format_list, formats, environment, substitute_title=cut_file_name)  



def createCutsPlus(source_path, cuts_dir, stems_dir, alts_dir, album_name, track_name, meta, formats, environment):
    cut_dictionary = buildCutDictionary(album_name, track_name, meta)
    audio_format_list = formats['cut audio'][0].split(',')

    for key in cut_dictionary.keys():
        log('\n', album_name, track_name ) 
        log('Creating with its own stems and alts: ' + key, album_name, track_name )
        # Because we will have sub dirs for stems and alts
        # we make a slight different directory setup
        new_dir = os.path.join(cuts_dir, key)
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
            
        cuts_plus_alts_dir = os.path.join(new_dir, "alts")
        cuts_plus_stems_dir = os.path.join(new_dir, "stems")
        cuts_plus_master_dir = os.path.join(new_dir, "masters")
        createPruneOrIgnoreDirectory(cuts_plus_alts_dir, False)
        createPruneOrIgnoreDirectory(cuts_plus_stems_dir, False)
        createPruneOrIgnoreDirectory(cuts_plus_master_dir, False) 
        audio_segments = cut_dictionary[key]

        # do the basic cut
        oneCutInternal(key, source_path, cuts_plus_master_dir, audio_segments, audio_format_list, meta, formats, environment, album_name, track_name)
       
        # now create cut-down stems for the cut
        for f in os.scandir(stems_dir):
            fpath = os.path.realpath(f)
            sub_name = os.path.basename(f)
            if fpath.endswith(".wav"):
                log("Adding Stem for cut:" + key + " " + os.path.basename(f))
                oneCutInternal(key, fpath, cuts_plus_stems_dir, audio_segments, audio_format_list, meta, formats, environment, album_name, track_name, prefix = sub_name)

        for f in os.scandir(alts_dir):
            fpath = os.path.realpath(f)
            sub_name = os.path.basename(f)
            if fpath.endswith(".wav"):
                log("Adding Alt for cut:" + key + " " + os.path.basename(f))
                oneCutInternal(key, fpath, cuts_plus_alts_dir, audio_segments, audio_format_list, meta, formats, environment, album_name, track_name, prefix = sub_name)

        log("Finishing Cut in requested audio formats.")        
              
                 
          


def createCuts(source_path, cuts_dir, album_name, track_name, meta, formats, environment):
    cut_dictionary = buildCutDictionary(album_name, track_name, meta)
    audio_format_list = formats['cut audio'][0].split(',')
    for key in cut_dictionary.keys():
        log('\n', album_name, track_name ) 
        log('Creating Cut: ' + key, album_name, track_name )
        audio_segments = cut_dictionary[key]
        oneCutInternal(key, source_path, cuts_dir, audio_segments, audio_format_list, meta, formats, environment, album_name, track_name)
        log("Finishing Cut in requested audio formats.") 
                



def createAlts(meta_file, multi_dir, alts_dir, album_name, track_name, meta, formats, environment):
    alt_dict = buildAltDictionary(meta_file, multi_dir, album_name, track_name)
    audio_format_list = formats['alt audio'][0].split(',')
    
    for key in alt_dict.keys():
        alt_file_name = applyNamingConvention('alt naming', album_name, track_name, meta, formats, alt_name = key)
        alt_file_path_no_ext = os.path.join(alts_dir, alt_file_name)
        mults = alt_dict[key]
        if(len(mults) > 0) :
            audio = False # will switch to actual audio content in a moment
            for m in mults:
                path = os.path.join(multi_dir, m)
                if not audio :
                    audio = pydub.AudioSegment.from_file(path)
                    log('\n', album_name, track_name ) 
                    log('Creating Alt: ' + key, album_name, track_name)
                    log('Adding to Alt: ' + m, album_name, track_name)
                else:
                    dub = pydub.AudioSegment.from_file(path)
                    audio = audio.overlay(dub)
                    log('Adding to Alt: ' +m, album_name, track_name)
            exportRequiredFormats(album_name, track_name, meta, alt_file_path_no_ext, audio, audio_format_list, formats, environment, substitute_title=alt_file_name)            
            log("Converting Alt: " + key  + " to requested audio formats", album_name, track_name)




def createStems(meta_file, multi_dir, stems_dir, album_name, track_name, meta, formats, environment):
    stem_dict = buildStemDictionary(meta_file, multi_dir, album_name, track_name)
    audio_format_list = formats['stem audio'][0].split(',')
    
    for key in stem_dict.keys():
        stem_file_name = applyNamingConvention('stem naming', album_name, track_name, meta, formats, stem_name = key)
        stem_file_path_no_ext = os.path.join(stems_dir, stem_file_name)
        mults = stem_dict[key]
        if(len(mults) > 0) :
            audio = False # will switch to actual audio content in a moment
            for m in mults:
                path = os.path.join(multi_dir, m)
                if not audio :
                    audio = pydub.AudioSegment.from_file(path)
                    log('\n', album_name, track_name ) 
                    log('Creating Stem: ' + key, album_name, track_name ) 
                    log('Adding to Stem: ' + m, album_name, track_name)
                else:
                    dub = pydub.AudioSegment.from_file(path)
                    audio = audio.overlay(dub)
                    log('Adding to Stem: ' + m, album_name, track_name)
            exportRequiredFormats(album_name, track_name, meta, stem_file_path_no_ext, audio, audio_format_list, formats, environment, substitute_title=stem_file_name)            
            log("Converting Stem: " + key + " to requested audio formats", album_name, track_name)



def createMasters(src_file, prod_dir, album_name, track_name, meta, formats, environment, ignore_video):
    audio_format_list = formats['master audio'][0].split(',')
    file_name = applyNamingConvention('master naming', album_name, track_name, meta, formats)
    file_path_no_ext = os.path.join(prod_dir, file_name)
    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]

    audio = pydub.AudioSegment.from_file(src_file)
    log("\n")
    log("Creating masters: " + file_name + " in requested audio formats", album_name, track_name)
    exportRequiredFormats(album_name, track_name, meta, file_path_no_ext, audio, audio_format_list, formats, environment)            

    # process possible video masters
    if not ignore_video:
        video_still = matches['video still'][0]
        video_reel = matches['video'][0]
        image_dir = environment["images and video"][0]
        audio_temp = os.path.join(prod_dir, "audio_for_video_temp")
        audio.export(audio_temp, format='mp3', bitrate="320k") 

        if type(video_still) == str and video_still:
            video_still = os.path.join(image_dir, video_still)
            export_still_video(audio_temp, video_still, file_path_no_ext + ".mp4")

        if type(video_reel) == str and video_reel:
            print(video_reel)
            video_reel = os.path.join(image_dir, video_reel)
            export_video(audio_temp, video_reel, prod_dir) 

        os.remove(audio_temp)       


def track_scan_internal(album_dir, 
                        track_dir, 
                        meta_file, 
                        meta,
                        environment, 
                        ignore_alts, 
                        ignore_master, 
                        ignore_stems, 
                        ignore_cuts, 
                        ignore_cuts_plus, 
                        ignore_video,
                        ignore_backup):
    
    source_for_cuts = ""
    track_name = nameFromDirectory(os.path.basename(track_dir))
    album_name = nameFromDirectory(os.path.basename(album_dir))

    prod_root = environment["production"][0]
    prod_album_dir = os.path.join(prod_root, album_name)
    prod_track_dir = os.path.normpath(os.path.join(prod_album_dir, track_name))

    alts_dir = os.path.join(prod_track_dir, "alts")
    cuts_dir = os.path.join(prod_track_dir, "cuts")
    stems_dir = os.path.join(prod_track_dir, "stems")
    master_dir = os.path.join(prod_track_dir, "masters")
    multitrack_dir = os.path.join(prod_track_dir, "multitrack")

    createPruneOrIgnoreDirectory(prod_root, True)
    createPruneOrIgnoreDirectory(prod_album_dir, True)
    createPruneOrIgnoreDirectory(prod_track_dir, True)
    createPruneOrIgnoreDirectory(alts_dir, ignore_alts)
    createPruneOrIgnoreDirectory(stems_dir, ignore_stems)
    createPruneOrIgnoreDirectory(master_dir, ignore_master)
    createPruneOrIgnoreDirectory(multitrack_dir, False)
    createPruneOrIgnoreDirectory(cuts_dir, ignore_cuts)

    matches = meta.loc[(meta['album'] == album_name) & (meta['title'] == track_name)]
    format_entry = matches['format'][0]
    format_dictionary = pandas.read_excel(meta_file, "Formats")
    formats = format_dictionary.loc[(format_dictionary['format name'] == format_entry)] 

    for f in os.listdir(track_dir):
        base_name = os.path.basename(f)
        tup = os.path.splitext(base_name)
        source_file = os.path.join(track_dir, base_name)

        if tup[1].lower() =='.wav' or  tup[1].lower() =='.aiff':
            # move multitrack files to the correct directory
            if not tup[0].endswith(track_name):
                destination = os.path.join(multitrack_dir, base_name)
                shutil.copy(source_file, destination)
                log("Copying Multitrack: " + base_name, album_name, track_name)
            # else it is a master, so move to the master directory
            else:
                source_for_cuts = source_file
                if not ignore_master:
                    createMasters(source_file, master_dir, album_name, track_name, meta, formats, environment, ignore_video) 

    if not ignore_stems:
        createStems(meta_file, multitrack_dir, stems_dir, album_name, track_name, meta, formats, environment)
    if not ignore_alts:
        createAlts(meta_file, multitrack_dir, alts_dir, album_name, track_name, meta, formats, environment)    
    if not ignore_cuts_plus:
        createCutsPlus(source_for_cuts, cuts_dir, stems_dir, alts_dir, album_name, track_name, meta, formats, environment) 
    elif not ignore_cuts:
        createCuts(source_for_cuts, cuts_dir, album_name, track_name, meta, formats, environment) 
    if not ignore_backup:
        backupTrack(meta, formats,  prod_track_dir, album_name, track_name, environment)



def monitorStaging(meta_file, 
                    ignore_alts = False, 
                    ignore_master = False, 
                    ignore_stems = False, 
                    ignore_cuts = False,
                    ignore_cuts_plus = False, 
                    ignore_video = False,
                    ignore_backup = False):

    meta = pandas.read_excel(meta_file, "Works")
    environment =  pandas.read_excel(meta_file, "Environment")
    stage_dir = environment["staging"][0]
    time_standard = time.time()
    log("\n")
    log("Monitoring Staging")
    while(True):
        starting_file_count = sum([len(files) for r, d, files in os.walk(stage_dir)])

        # walk the albums
        for dir in os.listdir(stage_dir):
            album_dir = os.path.join(stage_dir, dir)
            if os.path.isdir(album_dir):
                # walk the tracks in the album
                for( root, dirs, files) in os.walk(album_dir):

                    for dir in dirs: 
                        track_dir = os.path.join(album_dir, dir)
                        starting_file_count = sum([len(files) for r, d, files in os.walk(stage_dir)])
                        found_modified = False
                        found_locked = False
                        found_new_addition = False

                        # walk all of the audio files in the track
                        for f in os.listdir(track_dir):
                            base_name = os.path.basename(f)
                            source_file = os.path.join(track_dir, f)
                            tup = os.path.splitext(base_name)
                            if tup[1].lower() =='.wav' or  tup[1].lower() =='.aiff':
                                file_modified = os.path.getmtime(source_file)
                                if file_modified > time_standard:
                                    found_modified = True
                                try:
                                    block_test = open(source_file, 'r')
                                    block_test.close()
                                except IOError:
                                    found_locked = True
                        ending_file_count = sum([len(files) for r, d, files in os.walk(stage_dir)]) 
                        if starting_file_count != ending_file_count:
                            found_new_addition = True
                                       
                        # if we found changes, and there aren't any files blocked 
                        # or new files still being added, then we can go           
                        if(found_modified and not(found_locked or found_new_addition)):
                            log("Identified modified track file(s) in staging " + track_dir)
                            log("\n")
                            track_scan_internal(album_dir, 
                                track_dir, 
                                meta_file, 
                                meta,
                                environment, 
                                ignore_alts, 
                                ignore_master, 
                                ignore_stems, 
                                ignore_cuts, 
                                ignore_cuts_plus, 
                                ignore_video,
                                ignore_backup)
                            
                            time_standard = time.time()
                            log("\n")
                            log("Monitoring Staging")

        
        time.sleep(60)

# *****************************************************************************
# *****************************************************************************
# THESE ARE THE ONLY FUNCTIONS TYPICALLY USED DIRECTLY BY THE END USER
# *****************************************************************************
# *****************************************************************************

# This function processes an album in the staging directory.  By default it 
# performs all of its automation tasks, but you can tell it to ignore
# certain tasks by adding and setting any of the ignore paramaters
# to true. For example ignore_stems=True, ignore_cuts = True

def rideAlbum(album_dir, 
              meta_file, 
              ignore_alts = False, 
              ignore_master = False, 
              ignore_stems = False, 
              ignore_cuts = False,
              ignore_cuts_plus = False, 
              ignore_video = False,
              ignore_backup = False):
    
    log("Started processing album: " + album_dir + " at " + time.ctime())
    
    # first load up our metadata file
    meta = pandas.read_excel(meta_file, "Works")
    environment =  pandas.read_excel(meta_file, "Environment")

    # walk the tracks in the album
    for( root, dirs, files) in os.walk(album_dir):
        for dir in dirs: 
            track_dir = os.path.join(album_dir, dir)      
            track_scan_internal(album_dir, 
                                track_dir, 
                                meta_file, 
                                meta,
                                environment, 
                                ignore_alts, 
                                ignore_master, 
                                ignore_stems, 
                                ignore_cuts, 
                                ignore_cuts_plus, 
                                ignore_video,
                                ignore_backup)
    
   


# This function processes all albums in the staging directory.  By default it 
# performs all of the automation tasks, but you can tell it to ignore
# certain tasks by adding and setting any of the ignore paramaters
# to true. For example ignore_stems=True, ignore_cuts = True
def rideStaging(meta_file, 
                ignore_alts = False, 
                ignore_master = False, 
                ignore_stems = False, 
                ignore_cuts = False,
                ignore_cuts_plus = False, 
                ignore_video = False,
                ignore_backup = False):
    
    environment =  pandas.read_excel(meta_file, "Environment")
    stage_dir = environment["staging"][0]
 
    # walk the albums
    for dir in os.listdir(stage_dir):
        album_dir = os.path.join(stage_dir, dir)
        if os.path.isdir(album_dir):
            rideAlbum(album_dir, 
                      meta_file, 
                      ignore_alts, 
                      ignore_master, 
                      ignore_stems, 
                      ignore_cuts, 
                      ignore_cuts_plus,
                      ignore_video, 
                      ignore_backup)

     
                              