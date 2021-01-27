import logging
from you_anchor_tube import YouAnchorTube

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    try:
        YouAnchorTube()
    except Exception as e:
        logging.error(f'Fatal exception: {e.with_traceback()}')
