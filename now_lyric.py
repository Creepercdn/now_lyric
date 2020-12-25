import site
import time
import datetime

import obspython as obs

site.main()

genlyric = None
genlyricResult = ''
global_source = None


def lnext():
    a = ''
    if not genlyricResult:
        return genlyricResult
    try:
        a = next(genlyric)
    except StopIteration:
        a = genlyricResult
    return a


def mnext(pressed):
    if pressed:
        lnext()
        sync_lyric()



def lyricgentor(textlyrics):
    index = 0

    while True:
        if index >= len(textlyrics.splitlines(False)):
            return
        yield textlyrics.splitlines(False)[index]
        index += 1

def add_souce_list(props, name, description, filters):
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

def parse_lrc(startTime: datetime.time, nowTime: datetime.time, content: str):
    lyrics = content.splitlines(False)
    for idd in range(len(lyrics)):
        i = lyrics[idd]
        timestr = i[i.find(']')+1:i.find(']')]
        processtime = nowTime-startTime
        a = timestr.split(':')
        lyrictime = datetime.timedelta(minutes=int(a[0]),seconds=int(a[1]),milliseconds=int(a[2]))
        
        if lyrictime>processtime:
            return lyrics[idd-1]
        elif lyrictime==processtime:
            return i
    return ""

def sync_lyric():
    src_settings = obs.obs_source_get_settings(global_source)
    obs.obs_data_set_string(src_settings, "text", genlyricResult)
    obs.obs_source_update(global_source, src_settings)
    obs.obs_data_release(src_settings)

def script_load(settings):
    obs.obs_hotkey_register_frontend("lyric_next", "Next Lyric(Manual Mode)",)
def script_description():
    return "<b>Now Lyric</b>" + \
        "<hr>" + \
        "Display current song as a text on your screen." + \
        "<hr>"

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_bool(props, "enabled", "Enabled")
    obs.obs_properties_add_int(
        props, "check_frequency", "Check frequency", 100, 10000, 100)
    obs.obs_properties_add_path(props, "file", "Lyrics File", obs.OBS_PATH_FILE, "Plain Text Lyric (*.lrc *.txt);;All Files (*.*)")
    obs.obs_properties_add_bool(props, "autosync", "Auto sync with Now Playing")

def script_update(settings):
    if obs.obs_data_get_bool(settings, "enabled") is True:
        obs.timer_add(sync_lyric, obs.obs_data_get_int("check_frequency"))
    else:
        obs.timer_remove(sync_lyric)

