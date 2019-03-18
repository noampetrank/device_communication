
class MediaPlayerUtils(object):
    """
    class for controlling a media player
    """
    def __init__(self, connection, activity="com.chahal.mpc.hd/org.videolan.vlc.StartActivity"):
        """
        
        :param IConnection connection: connection to a device
        :param str activity: media player activity to use
        """
        super(MediaPlayerUtils, self).__init__()
        self.connection = connection
        self.activity = activity

    def _send_key(self, keyid):
        """
        :param int keyid:
        """
        self.connection.shell("input keyevent " + str(keyid), timeout_ms=3000)
        
    def media_player_select_song(self, device_song_path):
        """
        open a song in the default media player on the device
         :param str device_song_path: path to the song we want to play
        :return:
        """
        media_cmd = 'am start -a android.intent.action.VIEW -d file://%s -t audio/wav --user 0%s' % (
            device_song_path, (" -n " + self.activity) if self.activity is not None else "")
        self.connection.shell(media_cmd)
        self.media_player_rewind_song()  # so it play from the beginning
    
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
