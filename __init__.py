import os

from Game import Game
from libavg.AVGAppUtil import getMediaDir, createImagePreviewNode

__all__ = ['apps']

def createPreviewNode(maxSize):
    filename = os.path.join(getMediaDir(__file__), 'preview.png')
    return createImagePreviewNode(maxSize, absHref = filename)

apps = ({'class': Game,
            'createPreviewNode': createPreviewNode},
            )

