# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/bootcamp/BCBattlePage.py
import SoundGroups
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.meta.BCBattlePageMeta import BCBattlePageMeta
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.Scaleform.daapi.view.battle.shared.crosshair import CrosshairPanelContainer
from gui.Scaleform.daapi.view.battle.classic.minimap import ClassicMinimapComponent, GlobalSettingsPlugin
from gui.Scaleform.daapi.view.battle.shared.minimap import common
from gui.Scaleform.daapi.view.battle.shared.minimap import settings
from gui.battle_control import minimap_utils
from constants import ARENA_PERIOD, HINT_TYPE, HINT_NAMES
from debug_utils_bootcamp import LOG_DEBUG_DEV_BOOTCAMP, LOG_ERROR_BOOTCAMP
from bootcamp.BootcampGUI import BootcampMarkersComponent
from bootcamp.BootCampEvents import g_bootcampEvents
from bootcamp.Bootcamp import g_bootcamp
from bootcamp.BootcampConstants import UI_STATE, CONSUMABLE_ERROR_MESSAGES
from bootcamp.BootcampSettings import getBattleSettings
from PlayerEvents import g_playerEvents
from gui.shared import g_eventBus, events, EVENT_BUS_SCOPE
_BOOTCAMP_EXTERNAL_COMPONENTS = (CrosshairPanelContainer, BootcampMarkersComponent)

class BootcampTargetPlugin(common.EntriesPlugin):

    def addTarget(self, markerID, position):
        matrix = minimap_utils.makePositionMatrix(position)
        model = self._addEntryEx(markerID, settings.ENTRY_SYMBOL_NAME.BOOTCAMP_TARGET, settings.CONTAINER_NAME.ICONS, matrix=matrix, active=True)
        return model is not None

    def delTarget(self, markerID):
        return self._delEntryEx(markerID)


class BootcampMinimapDisablePlugin(GlobalSettingsPlugin):

    def start(self):
        pass

    def stop(self):
        pass


class BootcampMinimapComponent(ClassicMinimapComponent):

    def _setupPlugins(self, arenaVisitor):
        setup = super(BootcampMinimapComponent, self)._setupPlugins(arenaVisitor)
        setup['bootcamp'] = BootcampTargetPlugin
        try:
            lessonId = arenaVisitor.getArenaExtraData()['lessonId']
            if BATTLE_VIEW_ALIASES.MINIMAP in getBattleSettings(lessonId).hiddenPanels:
                setup['settings'] = BootcampMinimapDisablePlugin
        except KeyError:
            LOG_ERROR_BOOTCAMP("Extra data doesn't contain lessonId")

        return setup


class BCBattlePage(BCBattlePageMeta):

    def __init__(self, ctx=None):
        super(BCBattlePageMeta, self).__init__(external=_BOOTCAMP_EXTERNAL_COMPONENTS)
        self._fullStatsAlias = BATTLE_VIEW_ALIASES.FULL_STATS
        self._onAnimationsCompleteCallback = None
        self.__hideOnCountdownPanels = set()
        return

    def reload(self):
        g_bootcamp.getUI().reload()
        super(BCBattlePage, self).reload()

    @property
    def topHint(self):
        return self.getComponent(BATTLE_VIEW_ALIASES.BOOTCAMP_BATTLE_TOP_HINT)

    def showNewElements(self, newElements):
        self._onAnimationsCompleteCallback = newElements['callback']
        self.as_showAnimatedS(newElements)

    def onAnimationsComplete(self):
        LOG_DEBUG_DEV_BOOTCAMP('onAnimationsComplete')
        if self._onAnimationsCompleteCallback is not None:
            self._onAnimationsCompleteCallback()
            self._onAnimationsCompleteCallback = None
        return

    def _populate(self):
        g_bootcampEvents.onUIStateChanged(UI_STATE.INIT)
        super(BCBattlePageMeta, self)._populate()
        g_bootcampEvents.onBattleComponentVisibility += self.__onComponentVisibilityEvent
        g_playerEvents.onArenaPeriodChange += self.__onArenaPeriodChange

    def _dispose(self):
        self._onAnimationsCompleteCallback = None
        self.__hideOnCountdownPanels.clear()
        g_playerEvents.onArenaPeriodChange -= self.__onArenaPeriodChange
        g_bootcampEvents.onBattleComponentVisibility -= self.__onComponentVisibilityEvent
        super(BCBattlePageMeta, self)._dispose()
        return

    def _onBattleLoadingStart(self):
        if len(self._blToggling) == 0:
            self._blToggling = set(self.as_getComponentsVisibilityS())
        self._blToggling.difference_update([BATTLE_VIEW_ALIASES.BATTLE_LOADING])
        self._setComponentsVisibility(visible={BATTLE_VIEW_ALIASES.BATTLE_LOADING}, hidden=self._blToggling)
        introVideoData = g_bootcamp.getIntroVideoData()
        g_eventBus.handleEvent(events.LoadViewEvent(VIEW_ALIAS.BOOTCAMP_INTRO_VIDEO, None, introVideoData), EVENT_BUS_SCOPE.BATTLE)
        SoundGroups.g_instance.restoreWWISEVolume()
        return

    def _onBattleLoadingFinish(self):
        super(BCBattlePageMeta, self)._onBattleLoadingFinish()
        battleSettings = getBattleSettings(g_bootcamp.getLessonNum())
        visiblePanels, hiddenPanels = battleSettings.visiblePanels, battleSettings.hiddenPanels
        periodCtrl = self.sessionProvider.shared.arenaPeriod
        inCountdown = periodCtrl.getPeriod() in (ARENA_PERIOD.WAITING, ARENA_PERIOD.PREBATTLE)
        if inCountdown and BATTLE_VIEW_ALIASES.PLAYERS_PANEL in visiblePanels:
            self.__hideOnCountdownPanels.add(BATTLE_VIEW_ALIASES.PLAYERS_PANEL)
        self._setComponentsVisibility(visible=set(visiblePanels).difference(self.__hideOnCountdownPanels), hidden=set(hiddenPanels).union(self.__hideOnCountdownPanels))
        uselessConsumable = HINT_NAMES[HINT_TYPE.HINT_USELESS_CONSUMABLE]
        if uselessConsumable in battleSettings.hints:
            errorMessages = self.getComponent(BATTLE_VIEW_ALIASES.VEHICLE_ERROR_MESSAGES)
            if errorMessages is not None:
                errorMessages.ignoreKeys = CONSUMABLE_ERROR_MESSAGES
        return

    def _toggleRadialMenu(self, enable):
        pass

    def __onComponentVisibilityEvent(self, name, isVisible):
        if isVisible:
            self._setComponentsVisibility(visible={name}, hidden=set())
        else:
            self._setComponentsVisibility(visible=set(), hidden={name})
        self.__setComponentEnabled(name, isVisible)

    def __setComponentEnabled(self, name, enable):
        if name == BATTLE_VIEW_ALIASES.SIXTH_SENSE:
            component = self.getComponent(BATTLE_VIEW_ALIASES.SIXTH_SENSE)
            if component is not None:
                component.enabled = enable
        return

    def __onArenaPeriodChange(self, period, *args):
        if period == ARENA_PERIOD.BATTLE and self.__hideOnCountdownPanels:
            self._setComponentsVisibility(visible=self.__hideOnCountdownPanels, hidden=set())