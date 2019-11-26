import os
import time
import subprocess32 as subprocess

DEVICE_MUSIC_PATH = "/sdcard/Music"


class IMediaPlayerUtils(object):
    """ interface for controlling a media player """

    def __init__(self):
        super(IMediaPlayerUtils, self).__init__()

    def media_player_select_song(self, device_song_path):
        pass

    def media_player_rewind_song(self):
        pass

    def media_player_pause_song(self):
        pass

    def media_player_stop_song(self):
        """
        stop to play in the media player - pauses and rewinds to beginning of song
        :return:
        """
        pass

    def media_player_close(self, player='com.oppo.music'):
        """
        force-stops the media player
        :param str player - name of player we want to close
        :return:
        """
        pass

    def select_and_play_song(self, song, path=DEVICE_MUSIC_PATH):
        """
        player this song on the default activity
        :param str song: name of song file
        :param str path: path to songs on the device
        :return:
        """
        pass

    def media_player_toggle(self):
        """ toggle pause/play """
        pass

    def media_player_play_song(self):
        pass


class MediaPlayerUtils(IMediaPlayerUtils):
    """
    class for controlling a media player on an Android Device
    (name is unclear - for backwards support
    """

    def media_player_toggle(self):
        self._send_key(85)  # toggle play/pause

    def __init__(self, connection, activity="com.chahal.mpc.hd/org.videolan.vlc.StartActivity", delay=None):
        """
        
        :param IConnection connection: connection to a device
        :param str activity: media player activity to use
        """
        super(MediaPlayerUtils, self).__init__()
        self.connection = connection
        self.activity = activity
        self.delay = delay

    def _send_key(self, keyid):
        """
        :param int keyid:
        """
        self.connection.shell("input keyevent " + str(keyid), timeout_ms=3000)
        # delay script (by sleeping) in an attempt to avoid media player crashes / red screens
        if self.delay:
            time.sleep(self.delay)

    def media_player_select_song(self, device_song_path):
        """
        open a song in the default media player on the device
         :param str device_song_path: path to the song we want to play
        :return:
        """
        media_cmd = ['am', 'start', '-a', 'android.intent.action.VIEW', '-d', '"file://{}"'.format(device_song_path),
                     '-t', 'audio/wav', '--user', '0']
        if self.activity is not None:
            media_cmd.extend(['-n', self.activity])
        self.connection.shell(media_cmd)
        # delay script (by sleeping) in an attempt to avoid media player crashes / red screens
        if self.delay:
            time.sleep(self.delay)

    def media_player_rewind_song(self):
        """
        stop to play in the media player - pauses and rewinds to beginning of song
        :return:
        """
        self._send_key(89)  # rewind

    def media_player_pause_song(self):
        """
        pause in the media player (like pressing the pause button)
        if song is already paused, nothing happens
        :return:
        """
        self._send_key(127)

    def media_player_stop_song(self):
        """
        stop to play in the media player - pauses and rewinds to beginning of song
        :return:
        """
        self._send_key(86)  # stop

    def media_player_close(self, player='com.oppo.music'):
        """
        force-stops the media player
        :param str player - name of player we want to close
        :return:
        """
        self.connection.shell('am force-stop {}'.format(player))

    def media_player_play_song(self):
        """
        Send the play button event
        """
        self._send_key(126)

    def _delay_for_media_player(self):
        # delay script (by sleeping) in an attempt to avoid media player crashes / red screens
        if self.delay:
            time.sleep(self.delay)

    def select_and_play_song(self, song, path=DEVICE_MUSIC_PATH):
        """
        player this song on the default activity
        :param str song: name of song file
        :param str path: path to songs on the device
        :return:
        """
        device_path = os.path.join(path, song)
        self.media_player_select_song(device_path)


class LinuxVlcMediaPlayerUtils(IMediaPlayerUtils):
    def __init__(self, vlc_song_path):
        super(LinuxVlcMediaPlayerUtils, self).__init__()

        self.media_player_select_song(vlc_song_path)

    def _create_vlc(self):
        return subprocess.Popen(
            "vlc {}  --global-key-pause Home --global-key-play End --global-key-prev F8 --global-key-stop F7".format(
                self.vlc_song).split())

    @staticmethod
    def _kill_vlcs():
        """ kill all open VLCs """
        subprocess.call("killall vlc".split())

    def media_player_select_song(self, device_song_path):
        self.vlc_song = device_song_path
        self._kill_vlcs()
        try:
            self.vlc = self._create_vlc()
            self.vlc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.media_player_pause_song()
        except OSError:
            self._install_vlc()

    def media_player_rewind_song(self):
        from pyautogui import hotkey
        hotkey("f8")

    def media_player_pause_song(self):
        from pyautogui import hotkey
        hotkey("home")

    def media_player_stop_song(self):
        from pyautogui import hotkey
        hotkey("f7")

    def media_player_close(self, player='com.oppo.music'):
        if self.vlc is not None:
            self.vlc.kill()

    def select_and_play_song(self, song, path="/home/buga/songs"):
        self.media_player_select_song(song)
        self.media_player_play_song()

    def media_player_play_song(self):
        from pyautogui import press
        press("end")

    def media_player_toggle(self):
        from pyautogui import press
        press(" ")


    def _install_vlc(self):
        print("Error: VLC not installed. Please install from the terminal :\nsudo apt-get install vlc")
        raw_input("Press Enter after installing")
        try:
            self.vlc = self._create_vlc()
            self.vlc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            print('Installation Successful, proceeding...')
            self.media_player_pause_song()


class Mp2MediaPlayerUtils(MediaPlayerUtils):
    def media_player_pause_song(self):
        """
        pause in the media player (like pressing the pause button)
        if song is already paused, nothing happens
        """
        self.connection.shell(["am", "broadcast", "-a", "com.bugatone.mobileproduct2app.stopMusic"])

    def media_player_stop_song(self):
        """
        stop to play in the media player - pauses and rewinds to beginning of song
        """
        self.connection.shell(["am", "broadcast", "-a", "com.bugatone.mobileproduct2app.stopMusic"])

    def media_player_play_song(self):
        """
        Send the play button event
        """
        self.connection.shell(["am", "broadcast", "-a", "com.bugatone.mobileproduct2app.playMusic"])
