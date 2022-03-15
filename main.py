import vk_api
import nltk
from vk_api.audio import VkAudio
from yandex_music import Client
import time


def adding_in_dict(key, item, dict_):
    if key in list(dict_.keys()):
        dict_[key].append(item)
    else:
        dict_[key] = [item]


def right_search(tracks, q):
    if tracks is not None:
        a = tracks['results'][0]
        title = a['artists'][0]['name'] + '' + a['title']
        title = title.lower()
        if nltk.edit_distance(q, title) / len(title) >= 0.5:
            return None
        return tracks


class ImportMusic:
    def __init__(self, vk_login, vk_password, yandex_login, yandex_password):
        self.vk_session = vk_api.VkApi(vk_login, vk_password)
        self.vk_session.auth()
        self.vk_audio = VkAudio(self.vk_session)
        self.client = Client.from_credentials(yandex_login, yandex_password)

    def search_in_yandex(self, text):
        find_music = self.client.search(text=text, type_='track')
        return right_search(find_music['tracks'], text)

    def add_track_in_yandex(self, track):
        id_ = track['id']
        return self.client.users_likes_tracks_add(track_ids=id_)

    def delete_track_in_yandex(self, track):
        id_ = track['id']
        return self.client.users_likes_tracks_remove(track_ids=id_)

    def search_in_vk(self, text):
        res = list(self.vk_audio.search(text))
        return res

    def audio_dic_vk(self):
        audio_list = self.vk_audio.get()
        res = dict()
        for audio in audio_list:
            artist = audio['artist'].lower()
            title = audio['title'].lower()
            if artist in list(res.keys()):
                res[artist].append(title)
            else:
                res[artist] = [title]
        return res

    def audio_dic_yandex(self):
        tracks = self.client.users_likes_tracks()
        res = dict()
        for track in tracks:
            track = track.fetch_track()
            artist = track['artists'][0]['name'].lower()
            title = track['title'].lower()
            if artist in list(res.keys()):
                res[artist].append(title)
            else:
                res[artist] = [title]
        return res

    def adding_playlists(self):
        res = list()
        playlists_vk = self.vk_audio.get_albums()
        for playlist in playlists_vk:
            tracks = self.vk_audio.get(album_id=playlist['id'])
            play_ya = self.client.users_playlists_create(title=playlist['title'])
            for track in tracks:
                res_search = self.search_in_yandex(track['artist'] + ' ' + track['title'])
                if res_search is not None:
                    id_ = res_search['results'][0]['albums'][0]['id']
                    self.client.users_playlists_insert_track(kind=play_ya['kind'],
                                                             track_id=res_search['results'][0]['id'],
                                                             album_id=id_)
                time.sleep(0.5)
            res.append(play_ya['kind'])
        return self.client.users_playlists(kind=res)

    def adding_with_count(self, artist, track, added_tracks, done_adding, fail_addings):
        res_search = self.search_in_yandex(artist + ' ' + track)
        if res_search is not None:
            res_bool = self.add_track_in_yandex(res_search['results'][0])
            if res_bool:
                adding_in_dict(artist, track, added_tracks)
                done_adding += 1
                print('Добавлен ' + artist + ' ' + track)
            else:
                fail_addings += 1
        else:
            fail_addings += 1

    def delete_all_likes_tracks(self):
        tracks = self.client.users_likes_tracks()
        for track in tracks:
            track = track.fetch_track()
            self.delete_track_in_yandex(track)

    def adding_tracks_from_vk(self):
        added_tracks = dict()
        fail_addings = 0
        done_adding = 0
        vk_tracks = self.audio_dic_vk()
        yandex_tracks = self.audio_dic_yandex()
        for artist, tracks in vk_tracks.items():
            if artist not in yandex_tracks.keys():
                for track in tracks:
                    self.adding_with_count(artist, track, added_tracks, done_adding, fail_addings)
            else:
                for track in tracks:
                    if track not in yandex_tracks[artist]:
                        self.adding_with_count(artist, track, added_tracks, done_adding, fail_addings)
        return added_tracks


