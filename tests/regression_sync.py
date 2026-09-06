import sys, tempfile, pathlib, sqlite3, shutil, json
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'app/backend'))
import server as s
import apple_music_sync as a
results={}
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d); old=root/'unrelated'; old.mkdir(); (old/'old.mp3').write_bytes(b'old')
    events=[]; imports=[]
    proc=SimpleNamespace(stdout=iter([]),returncode=0,wait=lambda:0)
    with patch.object(s,'safe_directory',return_value=d), patch.object(s.subprocess,'Popen',return_value=proc), patch.object(s,'broadcast_job_event',side_effect=lambda j,e:events.append(e)), patch.object(s,'import_folder_to_apple_music',side_effect=lambda p,**kw:(imports.append(p) or (True,'ok'))), patch.object(s,'trigger_mac_iphone_sync',return_value={'success':False}), patch.object(s,'send_macos_notification'), patch.object(s.time,'sleep'):
        s.run_download_worker('test',{'url':'https://example.invalid','sync_apple_music':True})
    results['download_no_output']={'imports_root_recursively':imports==[d],'final':events[-1]['status']}
    db=root/'fixture.db'; con=sqlite3.connect(db)
    con.executescript('CREATE TABLE item(item_pid INTEGER,item_artist_pid INTEGER,album_pid INTEGER); CREATE TABLE item_extra(item_pid INTEGER,title TEXT); CREATE TABLE item_artist(item_artist_pid INTEGER,item_artist TEXT); CREATE TABLE album(album_pid INTEGER,album TEXT); CREATE TABLE container(container_pid INTEGER,name TEXT,distinguished_kind INTEGER); CREATE TABLE container_item(container_pid INTEGER,item_pid INTEGER,position INTEGER); INSERT INTO item VALUES(1,1,1); INSERT INTO item_extra VALUES(1,"Wanted"); INSERT INTO item_artist VALUES(1,"Artist"); INSERT INTO album VALUES(1,"Album"); INSERT INTO container VALUES(1,"Selected",0); INSERT INTO container_item VALUES(1,1,0);');con.commit();con.close()
    def fake_run(cmd,**kw):
        if 'afc' in cmd:
            dest=pathlib.Path(cmd[-1])
            if cmd[-2].endswith('sqlitedb'): shutil.copy2(db,dest)
            else: dest.mkdir();(dest/'unmatched.mp3').write_bytes(b'not a tagged file')
        return SimpleNamespace(stdout='',returncode=0)
    for selection in [['Selected'],[]]:
        out=root/('export_selected' if selection else 'export_empty'); events=[]; imports=[]
        with patch.object(s,'pull_validated_database',side_effect=lambda py,dest: shutil.copy2(db,dest)), patch.object(s,'safe_directory',return_value=str(out)), patch.object(s.subprocess,'run',side_effect=fake_run), patch.object(s,'broadcast_job_event',side_effect=lambda j,e:events.append(e)), patch.object(s,'import_folder_to_apple_music',side_effect=lambda p,**kw:(imports.append(p) or (True,'ok'))),patch.object(s,'send_macos_notification'):
            s.run_iphone_export_worker('isolated_review',{'playlists':selection})
        results['export_'+('selected' if selection else 'empty')]={'final':events[-1]['status'],'import_calls':len(imports),'copied_files':len(list(out.rglob('*.mp3')))}
    from mutagen.id3 import ID3, TIT2, TPE1
    def tagged_run(cmd, **kw):
        if 'afc' in cmd:
            dest=pathlib.Path(cmd[-1]);dest.mkdir()
            tags=ID3();tags.add(TIT2(encoding=3,text=['Wanted']));tags.add(TPE1(encoding=3,text=['Artist']));tags.save(dest/'wanted.mp3')
        return SimpleNamespace(stdout='',returncode=0)
    events=[];imports=[]
    with patch.object(s,'pull_validated_database',side_effect=lambda py,dest: shutil.copy2(db,dest)),patch.object(s,'safe_directory',return_value=str(root/'positive')),patch.object(s.subprocess,'run',side_effect=tagged_run),patch.object(s,'broadcast_job_event',side_effect=lambda j,e:events.append(e)),patch.object(s,'import_tracks_to_apple_music',side_effect=lambda files,**kw:(imports.extend(files) or (True,'ok'))),patch.object(s,'send_macos_notification'):
        s.run_iphone_export_worker('positive',{'playlists':['Selected']})
    assert len(imports)==1 and events[-1]['status']=='completed', events
    with patch.object(a,'get_apple_music_library_tracks',return_value=[{'name':'New','artist':'Artist'}]):
        r=a.calculate_differential_sync('mac_to_iphone',str(db),[])
        results['empty_mac_selection']={'to_add_count':r['to_add_count']}
    with patch.object(a,'run_applescript',return_value=(True,'unexpected')):
        results['unverified_import_rejected']=a.import_tracks_to_apple_music([str(old/'old.mp3')])[0] is False
    results['unsafe_sync_disabled']=a.execute_mac_to_iphone_clean_sync('unused')['success'] is False
print(json.dumps(results,ensure_ascii=False,indent=2))

assert results['download_no_output']['final']=='error'
assert not results['download_no_output']['imports_root_recursively']
assert results['export_selected']['final']=='error'
assert results['export_empty']['copied_files']==0
assert results['empty_mac_selection']['to_add_count']==0
assert results['unverified_import_rejected'] and results['unsafe_sync_disabled']
with tempfile.TemporaryDirectory() as d:
    f=pathlib.Path(d)/'new.mp3';f.write_bytes(b'audio')
    events=[];imports=[]
    proc=SimpleNamespace(stdout=iter(['FINAL_FILE:'+json.dumps(str(f))]),returncode=0,wait=lambda:0)
    with patch.object(s,'safe_directory',return_value=d),patch.object(s.subprocess,'Popen',return_value=proc),patch.object(s,'broadcast_job_event',side_effect=lambda j,e:events.append(e)),patch.object(s,'import_tracks_to_apple_music',side_effect=lambda files,**kw:(imports.extend(files) or (True,'ok'))),patch.object(s,'trigger_mac_iphone_sync',return_value={'success':False}),patch.object(s,'send_macos_notification'),patch.object(s.time,'sleep'):
        s.run_download_worker('test',{'url':'https://example.invalid'})
    assert imports==[str(f.resolve())] and events[-1]['status']=='completed'
print('8 regression cases passed')
import iphone_snapshot
with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d);fixture=root/'source.db'
    c=sqlite3.connect(fixture);c.executescript('CREATE TABLE item(item_pid INTEGER); CREATE TABLE container_item(item_pid INTEGER); INSERT INTO item VALUES(1); INSERT INTO container_item VALUES(1);');c.close()
    def pull(cmd,**kw):
        if not cmd[-2].endswith('-wal'):shutil.copy2(fixture,cmd[-1])
        return SimpleNamespace(returncode=0)
    with patch.object(iphone_snapshot.subprocess,'run',side_effect=pull):
        iphone_snapshot.pull_validated_database('mock',root/'valid.db')
        c=sqlite3.connect(fixture);c.execute('INSERT INTO container_item VALUES(2)');c.commit();c.close()
        try:iphone_snapshot.pull_validated_database('mock',root/'invalid.db')
        except RuntimeError:pass
        else:raise AssertionError('dangling playlist accepted')
print('2 snapshot cases passed')

# Metadata-safe matching: missing/Unknown artist metadata may fall back to a
# unique title, while a real title+artist difference remains new.
with patch.object(a, 'get_apple_music_library_tracks', return_value=[
    {'name': 'Same Title', 'artist': 'Known Artist'},
    {'name': 'Same Title', 'artist': 'Different Artist'},
    {'name': 'Unknown Artist Song', 'artist': 'Known Artist'},
]):
    fixture = pathlib.Path(tempfile.mkdtemp()) / 'match.db'
    con = sqlite3.connect(fixture)
    con.executescript('CREATE TABLE item(item_pid INTEGER,item_artist_pid INTEGER,album_pid INTEGER); CREATE TABLE item_extra(item_pid INTEGER,title TEXT); CREATE TABLE item_artist(item_artist_pid INTEGER,item_artist TEXT); CREATE TABLE album(album_pid INTEGER,album TEXT); CREATE TABLE container(container_pid INTEGER,name TEXT,distinguished_kind INTEGER); CREATE TABLE container_item(container_pid INTEGER,item_pid INTEGER,position INTEGER); INSERT INTO item VALUES(1,1,1); INSERT INTO item_extra VALUES(1,"Same Title"); INSERT INTO item_artist VALUES(1,"Unknown"); INSERT INTO album VALUES(1,"A");')
    con.commit(); con.close()
    result = a.calculate_differential_sync('mac_to_iphone', str(fixture), None)
    assert result['to_add_count'] == 3
print('metadata matching cases passed')

# YouTube Kelly playlist comparison uses the requested Mac playlist and title
# variants; the combined GOOD BOY/FANTASTIC BABY performance stays new.
with patch.object(a, 'get_apple_music_playlist_tracks', return_value=[
    {'name': 'Good Goodbye', 'artist': 'HWASA'},
    {'name': 'GOOD BOY', 'artist': 'BIGBANG'},
]):
    result = a.compare_tracks_with_apple_music([
        {'title': "화사 (HWASA) - 'Good Goodbye' MV", 'uploader': 'HWASA'},
        {'title': "GD X TAEYANG -  'GOOD BOY '+ 'FANTASTIC BABY' in MAMA 2014", 'uploader': 'BIGBANG'},
    ], playlist_name='Kelly的KPOP音樂歌單')
    assert result['existing_count'] == 1 and result['new_count'] == 1
print('YouTube playlist scope cases passed')
