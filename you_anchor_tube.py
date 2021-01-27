import json
import logging
import argparse
from anchor_session import AnchorSession
from youtube_session import YouTubeSession
from types import SimpleNamespace


class YouAnchorTube:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)

        self._configure_app()

        youtube_session = YouTubeSession(self._config.ytApiKey)

        for item in self._config.items:
            try:
                anchor_session = AnchorSession(item.anchorUsername, item.anchorPassword)
                videos = youtube_session.list_playlist_videos(item.ytPlaylistId)
                uploaded_audio_files = anchor_session.list_uploaded_files()
                videos_to_process = self._find_missing_videos(videos, uploaded_audio_files)

                for video_info in videos_to_process:
                    try:
                        audio_stream = youtube_session.download_audio_file(video_info.video_id)
                        anchor_session.save_audio_stream_as_draft(
                            audio_stream=audio_stream,
                            mime_type='audio/ogg',
                            identifier=video_info.video_id,
                            published_at=video_info.published_at,
                            title=video_info.title,
                            description=video_info.description)
                    except Exception as e:
                        self._logger.error(f'Exception while processing video "{video_info.title}": {e}')

            except Exception as e:
                self._logger.error(f'Exception while processing item: {e}')

    def _configure_app(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--config')
        args = parser.parse_args()

        if args.config is None:
            raise Exception('Config not specified')

        try:
            with open(args.config, "r") as config_file:
                self._config = json.load(config_file, object_hook=lambda d: SimpleNamespace(**d))
        except:
            raise Exception(f'Cannot read configuration file {args.config}')

    @staticmethod
    def _find_missing_videos(videos, audio_files):
        results = []
        for video_info in videos:
            video_has_matching_audio = False
            for audio_file in audio_files:
                if audio_file.find(f'[{video_info.video_id}]') > 0:
                    video_has_matching_audio = True
                    break
            if video_has_matching_audio is False:
                results.append(video_info)
        return results
