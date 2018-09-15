# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/prb_control/storages/stronghold_storage.py
from gui.prb_control.storages.local_storage import LocalStorage

class StrongholdStorage(LocalStorage):
    """
    This storage holds active animation index.
    """
    __slots__ = ('_animationIdx',)

    def __init__(self):
        super(StrongholdStorage, self).__init__()
        self._animationIdx = 0

    def init(self):
        super(StrongholdStorage, self).init()

    def fini(self):
        super(StrongholdStorage, self).fini()
        self.clear()

    def clear(self):
        super(StrongholdStorage, self).clear()
        self._animationIdx = 0

    def suspend(self):
        super(StrongholdStorage, self).suspend()
        self.clear()

    def setActiveAnimationIdx(self, animIdx):
        self._animationIdx = animIdx

    def getActiveAnimationIdx(self):
        return self._animationIdx