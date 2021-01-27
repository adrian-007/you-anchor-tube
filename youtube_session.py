import googleapiclient.discovery
import googleapiclient.errors
import logging
from io import BytesIO
from pytube import YouTube
from youtube_video_info import YouTubeVideoInfo


class YouTubeSession:
    def __init__(self, api_key):
        self._logger = logging.getLogger(__name__)
        self._youtube = googleapiclient.discovery.build(
            serviceName='youtube',
            version='v3',
            developerKey=api_key,
            cache_discovery=False
        )

    def list_playlist_videos(self, playlist_id):
        video_info_list = []
        next_page_token = None

        while True:
            max_results = 100
            if next_page_token is None:
                response = self._youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    maxResults=max_results,
                    playlistId=playlist_id
                ).execute()
            else:
                response = self._youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    maxResults=max_results,
                    playlistId=playlist_id,
                    pageToken=next_page_token
                ).execute()

            if 'items' not in response:
                raise Exception("Playlist does not contain any video info")

            for item in response['items']:
                try:
                    details = item['contentDetails']
                    snippet = item['snippet']

                    video_info = YouTubeVideoInfo(
                        video_id=details['videoId'],
                        published_at=snippet['publishedAt'],
                        title=snippet['title'],
                        description=snippet['description']
                    )

                    self._logger.info(f'Video info: {video_info}')
                    video_info_list.append(video_info)
                finally:
                    pass

            next_page_token = response['nextPageToken'] if 'nextPageToken' in response else None

            if next_page_token is None:
                break

        return video_info_list

    def download_audio_file(self, video_id):
        try:
            yt = YouTube(f'http://youtube.com/watch?v={video_id}')
            audio_streams = yt.streams.filter(only_audio=True, audio_codec='opus').order_by('abr').desc()
            if len(audio_streams) == 0:
                raise Exception(f'No audio streams are available for {video_id}')

            audio_stream = audio_streams.first()
            buffer = BytesIO()
            audio_stream.stream_to_buffer(buffer)
            return buffer
        except Exception as e:
            self._logger.error(f'Failed to download audio of {video_id}: {e}')
            return None
