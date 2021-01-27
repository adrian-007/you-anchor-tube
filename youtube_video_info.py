import dateutil.parser


class YouTubeVideoInfo:
    def __init__(self, video_id, published_at, title, description):
        self.video_id = video_id
        self.published_at = dateutil.parser.isoparse(published_at)
        self.title = title
        self.description = description

    def __eq__(self, other):
        return self.video_id == other.video_id

    def __str__(self):
        return f'[{self.video_id}] {self.title}'
