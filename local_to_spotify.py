import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
import time
import re
import audio_metadata

# Lists to define list of songs
credentials = []  # list of credentials
local_playlist = []  # Original local playlist title list
search_playlist = []  # Songs to be searched on Spotify
songs_found_on_spotify = []  # list of ids of identified songs
songs_not_found = []  # songs not identified by spotify
cleaned_songs = []  # list of processed song titles


# import credentials from file
scope = 'playlist-modify-public'  # for a public playlist
credentials.append(scope)
for line in open("credentials.txt", "r").readlines():
    info = line.split()
    if info[0] == "spotify_username=":
        credentials.append(str(info[1]))
    elif info[0] == "SPOTIPY_CLIENT_ID=":
        credentials.append(str(info[1]))
    elif info[0] == "SPOTIPY_CLIENT_SECRET=":
        credentials.append(str(info[1]))
    elif info[0] == "SPOTIPY_REDIRECT_URI=":
        credentials.append(str(info[1]))

# Authorize credentials through Spotify Developer API
username = credentials[1]
token = SpotifyOAuth(scope=credentials[0], username=credentials[1], 
                     client_id=credentials[2], client_secret=credentials[3],
                     redirect_uri=credentials[4])
spotifyObject = spotipy.Spotify(auth_manager=token)


# Enter the location of your local playlist
def find_local_playlist():
    print("Location can be entered as /home/aryan/Documents/my_playlist")
    local_playlist_location = input("Enter location of local playlist : ")
    if os.path.isdir(local_playlist_location):  # path exists
        if any(File.endswith(".mp3") for File in os.listdir(local_playlist_location)):  # check for mp3 audio file in inputted directory
            for file in os.listdir(local_playlist_location):
                if file.lower().endswith(".mp3"):  # look for mp3 files
                    local_playlist.append(file)  # creates a list of names of songs in local playlist
            return local_playlist_location
        else:
            print("Sorry, I didn't find any audio file in this directory")
            find_local_playlist()    
    else:
        print("I think u messed up, I couldn't find this directory.")
        find_local_playlist()


# Creates playlist in Spotify with title & description
def create_playlist():
    playlist_name = input("Enter Spotify Playlist Name : ")
    playlist_desc = input("Enter Spotify Playlist Description : ")
    spotifyObject.user_playlist_create(user=username, name=playlist_name, public=True, description=playlist_desc)  
    print("processing ...")


# Looks for metadata titles in files
def access_metadata(playlist_location):
    for file in os.listdir(playlist_location):
        if file.lower().endswith(".mp3"):
            try:
                metadata = audio_metadata.load(playlist_location + "/" + file)  # there is a problem here
                song = metadata['tags'].title[0]
                song = re.sub('\W+',' ', song)
                local_playlist.remove(file)
                if len(song.split()) < 3:
                    try:
                        artist = metadata['tags'].artist[0]
                        artist = re.sub('\W+',' ', artist)
                        song = song + " " + artist
                    except:
                        a = 3
                local_playlist.append(song)
            except Exception as e:
                b =4


# Read content from the stop_words file
def import_stop_words():
    f = open("stop_words.txt", "r")
    stop_words = f.read().split()
    f.close()
    return stop_words


# Remove stop words and punctuation from song name
def strip_stop_words(stop_words, playlist):
    for song in playlist:
        song = re.sub(r'([^a-zA-Z ]+?)', ' ', song)  # removes numbers
        stripped_name = [word for word in re.split("\W+", song) if word.lower() not in stop_words]  # removes punctuation
        song = ' '.join(stripped_name)
        search_playlist.append(song)


# Search for song on Spotify
def search_song_on_spotify(song):
    try: 
        search_result = spotifyObject.search(q=song)
        # print(json.dumps(search_result, sort_keys= 4, indent=4))
        songs_found_on_spotify.append(search_result['tracks']['items'][0]['uri'])
        return True
    except Exception as e:
        songs_not_found.append(song)
        return False


# Loop to search list of songs on Spotify
def search_songs_on_spotify(playlist):
    for song in playlist:
        search_song_on_spotify(song)


# Process the song title again for better identification
def clean_song_name(songs_not_found):
    # print(len(songs_not_found))
    for song in songs_not_found:
        if len(song.split()) > 3:  # >=6
            new_song = song.split()[:4]  # first 4 words of the title
        else:
            new_song = song.split()[:3]  # first 3 words of the title
        new_song = ' '.join(new_song)
        if search_song_on_spotify(new_song):
            songs_not_found.remove(song)
        else:
            songs_not_found.remove(new_song)


# Access the created playlist
def access_playlist():
    all_playlists = spotifyObject.user_playlists(user=username)
    # print(json.dumps(all_playlists, sort_keys= 4, indent=4))
    playlist_id = all_playlists['items'][0]['id']
    return playlist_id


# Add Spotified tracks to playlist
def add_songs_to_spotify_playlist(playlist_id):
    # You can add a maximum of 100 tracks per request in Spotify
    no_of_songs = len(songs_found_on_spotify)
    quotient = no_of_songs//100
    # remainder = no_of_songs % 100
    for i in range(0, quotient + 1):
        try:
            songs_to_search = []
            songs_to_search = songs_found_on_spotify[(i * 100): ((i+1) * 100)]
            spotifyObject.user_playlist_add_tracks(user=username, playlist_id=playlist_id, tracks=songs_to_search)
        except Exception as e:
            print(e)
    print('Playlist created of ' + str(len(songs_found_on_spotify)) + " songs!")


# Create csv file of songs not identified
def create_csv_file(songs_not_found, playlist_location):
    print("I could not search " + str(len(songs_not_found)) + " songs :((")
    print("You will have to manually search these songs on Spotify")
    with open(playlist_location + '/remaining_songs.csv', mode='wt', encoding='utf-8') as myfile:
        for song in songs_not_found:
            myfile.write(song)
            myfile.write('\n')
    print("You can find them in remaining_songs.csv inside your local playlist folder")


def main():

    playlist_location = find_local_playlist()
    create_playlist()
    access_metadata(playlist_location)
    stop_words = import_stop_words()
    strip_stop_words(stop_words, local_playlist)
    search_songs_on_spotify(search_playlist)
    clean_song_name(songs_not_found)
    playlist_id = access_playlist()
    add_songs_to_spotify_playlist(playlist_id)
    if len(songs_not_found) > 0:
        create_csv_file(songs_not_found, playlist_location)


if __name__ == "__main__":
    main()
