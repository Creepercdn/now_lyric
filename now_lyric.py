import site
import datetime
import os

import obspython as obs

site.main()

genlyric = None # generator for lyric
genlyricResult = '' # now generator result
global_source = '' # lyric display source
lrcMode = False # LRC AutoSync Mode
startime = None # song start time (used in AutoSync)
lastSongname = '' # last song name for delect song progress
delectSourcename = '' # AutoSync Source name
lyricfileraw = '' # lyrics file content
TEXT_SOURCE = ("text_gdiplus", "text_ft2_source") # Const Var for text filter in source type


def lnext():
    global genlyricResult
    a = ''
    if not genlyricResult:
        return genlyricResult
    try:
        a = next(genlyric) # get next lyric
    except StopIteration:
        a = genlyricResult # lyrics end
    
    genlyricResult = a


def mnext(pressed): # manual next
    if pressed:
        lnext() # next lyric
        sync_lyric()


def lyricgentor(textlyrics): # lyrics generator type
    index = 0

    while True:
        if index >= len(textlyrics.splitlines(False)):
            return
        yield textlyrics.splitlines(False)[index]
        index += 1


def add_souce_list(props, name, description, filters): # Add "Source Name" combo box prop
    p = obs.obs_properties_add_list(
        props, name, description,
        obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    sources = obs.obs_enum_sources()
    if sources:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if filters:
                if source_id in filters:
                    name = obs.obs_source_get_name(source)
                    obs.obs_property_list_add_string(p, name, name)
            else:
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)
    obs.source_list_release(sources)
    return p


def parse_lrc(startTime: datetime.time, nowTime: datetime.time, content: str): # parse lrc
    global genlyricResult
    result = ''
    lyrics = content.splitlines(False)
    for idd in range(len(lyrics)):
        i = lyrics[idd]
        timestr = i[i.find(']')+1:i.find(']')] # now line lyric timedelta
        processtime = nowTime-startTime # now timedelta
        a = timestr.split(':')
        lyrictime = datetime.timedelta(minutes=int(
            a[0]), seconds=int(a[1]), milliseconds=int(a[2]))

        if lyrictime > processtime:
            result = lyrics[idd-1]
            break
        elif lyrictime == processtime:
            result = i
            break
    genlyricResult = result


def sync_lyric(): # sync now lyric to source
    global startime
    if lrcMode: # if enabled AutoSync
        source = obs.obs_get_source_by_name(delectSourcename)
        settings = obs_source_get_settings(source)
        name = obs.obs_data_get_string(settings,"text")
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        if lastSongname != name: # if song changed
            startime = datetime.datetime.now() # restore song start time
        
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", parse_lrc(startime, datetime.datetime.now(),lyricfileraw)) # parse now lryic
        source = obs.obs_get_source_by_name(source_name)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        



    src_settings = obs.obs_source_get_settings(global_source)
    obs.obs_data_set_string(src_settings, "text", genlyricResult)
    obs.obs_source_update(global_source, src_settings)
    obs.obs_data_release(src_settings)


def script_load(settings):
    obs.obs_hotkey_register_frontend(
        "lyric_next", "Next Lyric(Manual Mode)", mnext)


def script_unload():
    obs.obs_hotkey_unregister(mnext)
    obs.timer_remove(sync_lyric)


def script_description():
    return "<b>Now Lyric</b>" + \
        "<hr>" + \
        "Display current song as a text on your screen." + \
        "<hr>"

def sync(prop, propy):
    startime = datetime.datetime.now()

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_bool(props, "enabled", "Enabled")
    obs.obs_properties_add_int(
        props, "check_frequency", "Check frequency", 100, 10000, 100)
    obs.obs_properties_add_path(props, "file", "Lyrics File", obs.OBS_PATH_FILE,
                                "Plain Text Lyric (*.lrc *.txt);;All Files (*.*)")
    obs.obs_properties_add_bool(
        props, "autosync", "AutoSync with Now Playing")
    add_souce_list(props, 'source', 'Source Name:', TEXT_SOURCE)
    add_souce_list(props, 'syncsource', 'Sync Source Name(Only used when AutoSync enbaled):', TEXT_SOURCE)
    obs.obs_properties_add_button(props, "sync", "Sync start time to now time")


def script_update(settings):
    if obs.obs_data_get_bool(settings, "enabled") is True:
        obs.timer_add(sync_lyric, obs.obs_data_get_int("check_frequency"))
    else:
        obs.timer_remove(sync_lyric)
    
    if os.path.splitext(obs.obs_data_get_string("file"))[-1]=='.lrc':
        if obs.obs_data_get_bool('autosync'):
            lrcMode = True

