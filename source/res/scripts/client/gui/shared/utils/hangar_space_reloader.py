# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/shared/utils/hangar_space_reloader.py
import logging
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpaceReloader
from skeletons.gui.shared.utils import IHangarSpace
from gui.Scaleform.Waiting import Waiting
_logger = logging.getLogger(__name__)

class HangarSpaceReloader(IHangarSpaceReloader):
    hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self):
        super(HangarSpaceReloader, self).__init__()
        self.__loadingSpacePath = None
        self.__waitingMessage = None
        self.__visibilityMaskCache = {}
        return

    def init(self):
        self.hangarSpace.onSpaceCreate += self.__onHangarSpaceLoaded
        self.hangarSpace.onSpaceDestroy += self.__onSpaceDestroy
        self.hangarSpace.onSpaceRefreshCompleted += self.__onSpaceRefreshed

    def destroy(self):
        self.hangarSpace.onSpaceCreate -= self.__onHangarSpaceLoaded
        self.hangarSpace.onSpaceDestroy -= self.__onSpaceDestroy
        self.hangarSpace.onSpaceRefreshCompleted -= self.__onSpaceRefreshed
        self.__hideWaiting()
        self.__loadingSpacePath = None
        self.__visibilityMaskCache.clear()
        return

    def changeHangarSpace(self, spaceName, waitingMessage=None, backgroundImage=None):
        if not spaceName:
            _logger.error('Invalid space name: the name cannot be empty.')
            return
        elif self.__loadingSpacePath is not None:
            _logger.error('Failed to load space "%s", because another space is loading: %s', spaceName, self.__loadingSpacePath)
            return
        elif not self.hangarSpace.spaceInited or self.hangarSpace.spaceLoading():
            _logger.error('Failed to load space "%s", because another space is loading.', spaceName)
            return
        else:
            hangarSpacePath = self.hangarSpace.spacePath
            if hangarSpacePath is None:
                _logger.error('Abnormal behaviour: hangarSpace.spacePath is not initialized')
                return
            spacePath = 'spaces/' + spaceName
            if spacePath == hangarSpacePath:
                _logger.warning('No need to load space "%s", because it is already loaded', spaceName)
                return
            self.__loadingSpacePath = spacePath
            self.__waitingMessage = waitingMessage
            if waitingMessage:
                Waiting.show(waitingMessage, isAlwaysOnTop=True, backgroundImage=backgroundImage)
            visibilityMask = self.__visibilityMaskCache.get(self.__loadingSpacePath)
            self.__changeHangarSpace(self.__loadingSpacePath, visibilityMask)
            return

    def __onHangarSpaceLoaded(self):
        self.__updateVisibilityMaskCache()
        self.__hideWaiting()
        self.__loadingSpacePath = None
        return

    def __onSpaceDestroy(self, inited):
        if self.__loadingSpacePath is None:
            return
        else:
            if self.hangarSpace.spacePath == self.__loadingSpacePath:
                self.__hideWaiting()
                self.__loadingSpacePath = None
            return

    def __onSpaceRefreshed(self):
        self.__updateVisibilityMaskCache()

    def __updateVisibilityMaskCache(self):
        if self.__loadingSpacePath is not None:
            return
        else:
            path = self.hangarSpace.spacePath
            visibilityMask = self.hangarSpace.visibilityMask
            if visibilityMask is not None:
                self.__visibilityMaskCache[path] = visibilityMask
            return

    @staticmethod
    def __changeHangarSpace(spacePath, visibilityMask=None):
        if not spacePath:
            return
        else:
            from gui.ClientHangarSpace import g_clientHangarSpaceOverride
            if visibilityMask is None:
                g_clientHangarSpaceOverride.setPath(spacePath, isReload=True)
            else:
                g_clientHangarSpaceOverride.setPath(spacePath, visibilityMask=visibilityMask, isReload=True)
            return

    def __hideWaiting(self):
        if self.__waitingMessage is not None:
            Waiting.hide(self.__waitingMessage)
            self.__waitingMessage = None
        return
