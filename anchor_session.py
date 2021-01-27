import logging
from requests import Session
from utils import to_safe_filename
from io import SEEK_END


class AnchorSession:
    BASE_URL = 'https://anchor.fm'
    LOGIN_URL = 'api/login'
    AUDIO_LIBRARY = 'api/sourceaudio/audiolibrary'
    SIGNED_URL = 'api/proxy/v3/upload/signed_url'
    PROCESS_AUDIO = 'api/proxy/v3/upload/{}/process_audio'

    def __init__(self, username, password):
        self._logger = logging.getLogger(__name__)
        self._session = Session()
        self._login(username, password)

    def _login(self, username, password):
        self._logger.info(f'Logging in as {username}')
        url = f'{self.BASE_URL}/{self.LOGIN_URL}'
        payload = {"betaCode": None, "email": username, "password": password}
        r = self._session.post(url, json=payload)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to log in, status code: {r.status_code}')
        self._logger.info(f'Logged in as {username}')

    def list_uploaded_files(self):
        self._logger.info('Fetching audio library info')
        url = f'{self.BASE_URL}/{self.AUDIO_LIBRARY}'
        r = self._session.get(url)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to get audio library, status code: {r.status_code}')
        items = r.json()["audios"]
        self._logger.info(f'Found {len(items)} items in audio library')
        return [i['caption'] for i in items]

    def save_audio_stream_as_draft(self, audio_stream, mime_type, identifier, published_at, title, description):
        date_prefix = published_at.strftime('%Y-%m-%d %H:%M:%S')
        filename = f'[{date_prefix}][{identifier}] {title}'
        safe_filename = to_safe_filename(filename)

        upload_url, request_uuid = self._get_upload_location_info(mime_type, safe_filename)
        self._upload_audio_stream(upload_url, audio_stream, mime_type)
        self._process_audio_stream(request_uuid, filename)

    def _get_upload_location_info(self, mime_type, safe_filename):
        self._logger.info(f'Getting upload location for {safe_filename}')
        url = f'{self.BASE_URL}/{self.SIGNED_URL}'
        params = {'filename': safe_filename, 'type': mime_type}
        r = self._session.get(url, params=params)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to get signed URL for audio file upload, status code: {r.status_code}')
        response = r.json()
        upload_url = response['signedUrl']
        request_uuid = response['requestUuid']

        headers = {'Access-Control-Request-Method': 'PUT', 'Access-Control-Request-Headers': 'content-type',
                   'Origin': self.BASE_URL}
        r = self._session.options(upload_url, headers=headers)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to get signed URL OPTIONS verbs, status code: {r.status_code}')

        if 'PUT' not in r.headers['access-control-allow-methods']:
            raise Exception(f'PUT method not allowed')

        self._logger.info(f'Upload location for {safe_filename}: {upload_url}')
        return upload_url, request_uuid

    def _upload_audio_stream(self, upload_url, audio_stream, mime_type):
        audio_stream.seek(0, SEEK_END)
        content_length = audio_stream.tell()
        audio_stream.seek(0)

        self._logger.info(f'Uploading audio stream ({content_length} bytes)')
        headers = {'content-type': mime_type, 'content-length': str(content_length)}
        r = self._session.put(upload_url, audio_stream, headers=headers)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to upload audio stream, status code: {r.status_code}')
        self._logger.info('Upload complete')

    def _process_audio_stream(self, request_uuid, title):
        self._logger.info('Initiating audio stream processing')
        url = self.BASE_URL + '/' + self.PROCESS_AUDIO.format(request_uuid)
        payload = {'audioType': 'default', 'caption': title, 'isExtractedFromVideo': False, 'origin': 'podcast:upload'}
        r = self._session.post(url, json=payload)
        if r.status_code < 200 or r.status_code >= 300:
            raise Exception(f'Failed to request audio stream processing, status code: {r.status_code}')
        self._logger.info('Audio stream processing initialized on remote server')
