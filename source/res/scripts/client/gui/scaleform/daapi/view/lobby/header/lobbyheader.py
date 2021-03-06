# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/header/LobbyHeader.py
import math
import weakref
from itertools import ifilter, chain
import typing
import BigWorld
import WWISE
import constants
from CurrentVehicle import g_currentVehicle, g_currentPreviewVehicle
from account_helpers.AccountSettings import AccountSettings, QUESTS, QUEST_DELTAS, QUEST_DELTAS_COMPLETION
from account_helpers.AccountSettings import KNOWN_SELECTOR_BATTLES
from account_helpers.AccountSettings import NEW_LOBBY_TAB_COUNTER, RECRUIT_NOTIFICATIONS, NEW_SHOP_TABS
from adisp import process
from debug_utils import LOG_ERROR
from frameworks.wulf import ViewFlags
from gui import makeHtmlString
from gui.ClientUpdateManager import g_clientUpdateManager
from gui.impl import backport
from gui.impl.gen import R
from gui.Scaleform.Waiting import Waiting
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.header import battle_selector_items
from gui.Scaleform.daapi.view.lobby.hof.hof_helpers import getAchievementsTabCounter
from gui.Scaleform.daapi.view.lobby.store.browser.shop_helpers import getBuyPremiumUrl
from gui.Scaleform.daapi.view.lobby.store.browser.shop_helpers import getBuyGoldUrl
from gui.Scaleform.daapi.view.lobby.store.browser.shop_helpers import isSubscriptionEnabled
from gui.Scaleform.daapi.view.meta.LobbyHeaderMeta import LobbyHeaderMeta
from gui.Scaleform.framework import g_entitiesFactories, ViewTypes
from gui.Scaleform.framework.entities.View import ViewKey
from gui.Scaleform.framework.managers.containers import POP_UP_CRITERIA
from gui.Scaleform.framework.managers.view_lifecycle_watcher import IViewLifecycleHandler, ViewLifecycleWatcher
from gui.Scaleform.genConsts.RANKEDBATTLES_ALIASES import RANKEDBATTLES_ALIASES
from gui.Scaleform.genConsts.TOOLTIPS_CONSTANTS import TOOLTIPS_CONSTANTS
from gui.Scaleform.locale.MENU import MENU
from gui.Scaleform.locale.RES_ICONS import RES_ICONS
from gui.Scaleform.locale.TOOLTIPS import TOOLTIPS
from gui.Scaleform.settings import ICONS_SIZES
from gui.clans.clan_helpers import isStrongholdsEnabled, isClansTabReplaceStrongholds
from gui.game_control.ServerStats import STATS_TYPE
from gui.game_control.wallet import WalletController
from gui.gold_fish import isGoldFishActionActive, isTimeToShowGoldFishPromo
from gui.prb_control.entities.base.ctx import PrbAction
from gui.prb_control.entities.listener import IGlobalListener
from gui.prb_control.settings import PREBATTLE_ACTION_NAME, REQUEST_TYPE, UNIT_RESTRICTION
from gui.prb_control.settings import PRE_QUEUE_RESTRICTION, PREBATTLE_RESTRICTION
from gui.server_events import settings as quest_settings
from gui.server_events import recruit_helper
from gui.server_events.events_helpers import isDailyQuest
from gui.shared import event_dispatcher as shared_events
from gui.shared import events
from gui.shared.ClanCache import g_clanCache
from gui.shared.event_bus import EVENT_BUS_SCOPE
from gui.shared.event_dispatcher import showShop, showStorage, hideWebBrowserOverlay
from gui.shared.formatters import text_styles
from gui.shared.formatters.currency import getBWFormatter
from gui.shared.formatters.ranges import toRomanRangeString
from gui.shared.money import Currency
from gui.shared.utils.functions import makeTooltip
from gui.shared.utils.requesters.ItemsRequester import REQ_CRITERIA
from gui.shared.view_helpers.emblems import ClanEmblemsHelper
from gui.shared.gui_items.Vehicle import getTypeUserName
from helpers import dependency
from helpers import i18n, time_utils, isPlayerAccount
from predefined_hosts import g_preDefinedHosts, PING_STATUSES
from shared_utils import CONST_CONTAINER, BitmaskHelper
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.connection_mgr import IConnectionManager
from skeletons.gui.demount_kit import IDemountKitNovelty
from skeletons.gui.offers import IOffersNovelty
from skeletons.gui.game_control import IAnonymizerController, IBadgesController, IBoostersController, IBootcampController, IChinaController, IEpicBattleMetaGameController, IEventProgressionController, IGameSessionController, IIGRController, IRankedBattlesController, IServerStatsController, IWalletController, IClanNotificationController, IBattleRoyaleController
from skeletons.gui.goodies import IGoodiesCache
from skeletons.gui.impl import IGuiLoader
from skeletons.gui.server_events import IEventsCache
from skeletons.gui.techtree_events import ITechTreeEventsListener
from skeletons.gui.shared import IItemsCache
from skeletons.gui.shared.utils import IHangarSpace
from SoundGroups import g_instance as SoundGroupsInstance
from skeletons.gui.linkedset import ILinkedSetController
from constants import PREMIUM_TYPE
_MAX_HEADER_SERVER_NAME_LEN = 6
_SERVER_NAME_PREFIX = '%s..'
_SHORT_VALUE_DIVIDER = 1000000
_SHORT_VALUE_PRECISION = 1
_SHORT_VALUE_D = 10 ** _SHORT_VALUE_PRECISION
_SHORT_VALUE_THRESHOLD = _SHORT_VALUE_DIVIDER / _SHORT_VALUE_D
_SHORT_VALUE_FMT_PATTERN = MENU.HANGAR_HEADER_MILLION
HEADER_BUTTONS_COUNTERS_CHANGED_EVENT = 'lobbyHeaderButtonsCountersChanged'
_DASHBOARD_SUPPRESSED_VIEWS = [VIEW_ALIAS.BADGES_PAGE]

def _predicateLobbyTopSubViews(view):
    return view.layoutID != R.views.lobby.premacc.prem_dashboard_view.PremDashboardView() and view.viewFlags & ViewFlags.LOBBY_TOP_SUB_VIEW


def _isActiveShopNewCounters():
    newTabCounters = AccountSettings.getCounters(NEW_SHOP_TABS)
    return not any(newTabCounters.values())


def _updateShopNewCounters():
    newTabCounters = AccountSettings.getCounters(NEW_SHOP_TABS)
    AccountSettings.setCounters(NEW_SHOP_TABS, dict.fromkeys(newTabCounters, True))


class TOOLTIP_TYPES(object):
    COMPLEX = 'complex'
    SPECIAL = 'special'
    NONE = 'none'


class HeaderMenuVisibilityState(BitmaskHelper):
    NOTHING = 0
    BG_OVERLAY = 1
    BUTTON_BAR = 2
    ONLINE_COUNTER = 4
    ALL = BG_OVERLAY | BUTTON_BAR | ONLINE_COUNTER


class _RankedBattlesWelcomeViewLifecycleHandler(IViewLifecycleHandler):

    def __init__(self, lobbyHeader):
        super(_RankedBattlesWelcomeViewLifecycleHandler, self).__init__([ViewKey(RANKEDBATTLES_ALIASES.RANKED_BATTLES_INTRO_ALIAS)])
        self.__lobbyHeader = weakref.proxy(lobbyHeader)

    def onViewCreated(self, view):
        self.__lobbyHeader.disableLobbyHeaderControls(True)

    def onViewDestroyed(self, view):
        self.__lobbyHeader.disableLobbyHeaderControls(False)

    def onViewAlreadyCreated(self, view):
        self.__lobbyHeader.disableLobbyHeaderControls(True)


class _LobbyHeaderVisibilityHelper(object):
    __slots__ = ('__headerStatesStack',)

    def __init__(self):
        self.__headerStatesStack = []

    def getActiveState(self):
        return self.__headerStatesStack[-1] if self.__headerStatesStack else HeaderMenuVisibilityState.ALL

    def updateStates(self, state):
        previousState = self.getActiveState()
        if previousState == HeaderMenuVisibilityState.NOTHING and state != previousState:
            self.__removePreviousState()
        else:
            self.__addState(state)

    def clear(self):
        self.__headerStatesStack = []

    def __addState(self, state):
        self.__headerStatesStack.append(state)

    def __removePreviousState(self):
        return self.__headerStatesStack.pop() if self.__headerStatesStack else None


class LobbyHeader(LobbyHeaderMeta, ClanEmblemsHelper, IGlobalListener):
    __PREM_WARNING_LIMIT = time_utils.ONE_DAY

    class BUTTONS(CONST_CONTAINER):
        SETTINGS = 'settings'
        ACCOUNT = 'account'
        PREM = 'prem'
        PREMSHOP = 'premShop'
        SQUAD = 'squad'
        GOLD = Currency.GOLD
        CREDITS = Currency.CREDITS
        CRYSTAL = Currency.CRYSTAL
        FREE_XP = 'freeXP'
        BATTLE_SELECTOR = 'battleSelector'

    PRB_NAVIGATION_DISABLE_BUTTONS = (BUTTONS.PREM,
     BUTTONS.CREDITS,
     BUTTONS.GOLD,
     BUTTONS.CRYSTAL,
     BUTTONS.FREE_XP,
     BUTTONS.ACCOUNT,
     BUTTONS.PREMSHOP)

    class TABS(CONST_CONTAINER):
        HANGAR = VIEW_ALIAS.LOBBY_HANGAR
        STORE = VIEW_ALIAS.LOBBY_STORE
        STORAGE = VIEW_ALIAS.LOBBY_STORAGE
        PROFILE = VIEW_ALIAS.LOBBY_PROFILE
        TECHTREE = VIEW_ALIAS.LOBBY_TECHTREE
        BARRACKS = VIEW_ALIAS.LOBBY_BARRACKS
        BROWSER = VIEW_ALIAS.BROWSER
        RESEARCH = VIEW_ALIAS.LOBBY_RESEARCH
        PERSONAL_MISSIONS = VIEW_ALIAS.LOBBY_PERSONAL_MISSIONS
        MISSIONS = VIEW_ALIAS.LOBBY_MISSIONS
        STRONGHOLD = VIEW_ALIAS.LOBBY_STRONGHOLD
        PERSONAL_MISSIONS_PAGE = VIEW_ALIAS.PERSONAL_MISSIONS_PAGE

    RANKED_WELCOME_VIEW_DISABLE_CONTROLS = BUTTONS.ALL()
    ACCOUNT_SETTINGS_COUNTERS = (TABS.STORE,)
    anonymizerController = dependency.descriptor(IAnonymizerController)
    badgesController = dependency.descriptor(IBadgesController)
    boosters = dependency.descriptor(IBoostersController)
    bootcampController = dependency.descriptor(IBootcampController)
    chinaCtrl = dependency.descriptor(IChinaController)
    connectionMgr = dependency.descriptor(IConnectionManager)
    demountKitNovelty = dependency.descriptor(IDemountKitNovelty)
    epicController = dependency.descriptor(IEpicBattleMetaGameController)
    eventProgressionController = dependency.descriptor(IEventProgressionController)
    eventsCache = dependency.descriptor(IEventsCache)
    techTreeEventsListener = dependency.descriptor(ITechTreeEventsListener)
    gameSession = dependency.descriptor(IGameSessionController)
    goodiesCache = dependency.descriptor(IGoodiesCache)
    gui = dependency.descriptor(IGuiLoader)
    hangarSpace = dependency.descriptor(IHangarSpace)
    igrCtrl = dependency.descriptor(IIGRController)
    itemsCache = dependency.descriptor(IItemsCache)
    linkedSetController = dependency.descriptor(ILinkedSetController)
    rankedController = dependency.descriptor(IRankedBattlesController)
    clanNotificationCtrl = dependency.descriptor(IClanNotificationController)
    serverStats = dependency.descriptor(IServerStatsController)
    settingsCore = dependency.descriptor(ISettingsCore)
    wallet = dependency.descriptor(IWalletController)
    offersNovelty = dependency.descriptor(IOffersNovelty)
    __battleRoyaleController = dependency.descriptor(IBattleRoyaleController)

    def __init__(self):
        super(LobbyHeader, self).__init__()
        self.__currentScreen = None
        self.__shownCounters = set()
        self._isLobbyHeaderControlsDisabled = False
        self.__viewLifecycleWatcher = ViewLifecycleWatcher()
        self.__isFightBtnDisabled = self.bootcampController.isInBootcamp()
        self.__isSubscriptionEnabled = isSubscriptionEnabled()
        self.__clanIconID = None
        self.__visibility = HeaderMenuVisibilityState.ALL
        self.__menuVisibilityHelper = _LobbyHeaderVisibilityHelper()
        return

    @property
    def menuVisibilityHelper(self):
        return self.__menuVisibilityHelper

    def onClanEmblem16x16Received(self, clanDbID, emblem):
        if not self.isDisposed() and emblem:
            self.__clanIconID = self.getMemoryTexturePath(emblem, temp=False)
            self._updateHangarMenuData()

    def onPlayerStateChanged(self, entity, roster, accountInfo):
        if accountInfo.isCurrentPlayer():
            self._updatePrebattleControls()

    def onUnitPlayerStateChanged(self, pInfo):
        self._updatePrebattleControls()

    def onPrbEntitySwitched(self):
        self._updatePrebattleControls()

    def onDequeued(self, *_):
        self._updatePrebattleControls()

    def onKickedFromQueue(self, *_):
        self._updatePrebattleControls()

    def updateAccountInfo(self):
        self.updateMoneyStats()
        self.updateXPInfo()
        self.__updatePlayerInfoPanel(g_clanCache.clanInfo)
        self.__updateAccountAttrs()
        self.__updateBadge()

    def updateMoneyStats(self):
        money = self.itemsCache.items.stats.actualMoney
        self.__setCredits(money.credits)
        self.__setGold(money.gold)
        self.__setCrystal(money.crystal)

    def updateXPInfo(self):
        self.__setFreeXP(self.itemsCache.items.stats.actualFreeXP)

    def showLobbyMenu(self):
        self.fireEvent(events.LoadViewEvent(VIEW_ALIAS.LOBBY_MENU), scope=EVENT_BUS_SCOPE.LOBBY)

    @process
    def menuItemClick(self, alias):
        navigationPossible = yield self.lobbyContext.isHeaderNavigationPossible()
        if navigationPossible:
            hideWebBrowserOverlay()
            self.__triggerViewLoad(alias)
        else:
            self.as_doDeselectHeaderButtonS(alias)

    def onCrystalClick(self):
        shared_events.showCrystalWindow(self.__visibility)

    def onPayment(self):
        showShop(getBuyGoldUrl())

    def showExchangeWindow(self):
        shared_events.showExchangeCurrencyWindow()

    def showExchangeXPWindow(self):
        shared_events.showExchangeXPWindow()

    def showPremiumView(self):
        showShop(getBuyPremiumUrl())

    def onPremShopClick(self):
        self.fireEvent(events.OpenLinkEvent(events.OpenLinkEvent.PREM_SHOP))

    @process
    def showDashboard(self):
        navigationPossible = yield self.lobbyContext.isHeaderNavigationPossible()
        if navigationPossible:
            for alias in _DASHBOARD_SUPPRESSED_VIEWS:
                self.app.containerManager.destroyViews(alias)

            views = self.gui.windowsManager.findViews(_predicateLobbyTopSubViews)
            for view in views:
                view.destroyWindow()

            dashbordView = self.gui.windowsManager.getViewByLayoutID(R.views.lobby.premacc.prem_dashboard_view.PremDashboardView())
            if dashbordView is None:
                shared_events.showDashboardView()
            else:
                hideWebBrowserOverlay()
        return

    @process
    def fightClick(self, mapID, actionName):
        navigationPossible = yield self.lobbyContext.isHeaderNavigationPossible()
        fightButtonPressPossible = yield self.lobbyContext.isFightButtonPressPossible()
        if navigationPossible and fightButtonPressPossible:
            if self.prbDispatcher:
                self.prbDispatcher.doAction(PrbAction(actionName, mapID))
            else:
                LOG_ERROR('Prebattle dispatcher is not defined')

    @process
    def showSquad(self):
        navigationPossible = yield self.lobbyContext.isHeaderNavigationPossible()
        if navigationPossible:
            if self.prbDispatcher:
                state = self.prbDispatcher.getFunctionalState()
                isRoyale = state.isInPreQueue(constants.QUEUE_TYPE.BATTLE_ROYALE) or state.isInUnit(constants.PREBATTLE_TYPE.BATTLE_ROYALE)
                if isRoyale:
                    self.__doSelect(PREBATTLE_ACTION_NAME.BATTLE_ROYALE_SQUAD)
                else:
                    self.__doSelect(PREBATTLE_ACTION_NAME.SQUAD)
            else:
                LOG_ERROR('Prebattle dispatcher is not defined')

    def _onPopulateEnd(self):
        pass

    def _populate(self):
        self._cleanupVisitedSettings()
        self._updateHangarMenuData()
        battle_selector_items.create()
        super(LobbyHeader, self)._populate()
        if self.app.tutorialManager.lastHeaderMenuButtonsOverride is not None:
            self.__onOverrideHeaderMenuButtons()
        self._addListeners()
        Waiting.hide('enter')
        self._isLobbyHeaderControlsDisabled = False
        self.__viewLifecycleWatcher.start(self.app.containerManager, [_RankedBattlesWelcomeViewLifecycleHandler(self)])
        if self.bootcampController.isInBootcamp():
            self.as_disableFightButtonS(self.__isFightBtnDisabled)
        self._onPopulateEnd()
        return

    def _invalidate(self, *args, **kwargs):
        super(LobbyHeader, self)._invalidate(*args, **kwargs)
        self._addListeners()

    def _dispose(self):
        self.__removeClanIconFromMemory()
        battle_selector_items.clear()
        self.__viewLifecycleWatcher.stop()
        self._removeListeners()
        self.__clearMenuVisibiliby()
        super(LobbyHeader, self)._dispose()

    def _getPremiumLabelText(self, premiumState):
        if self.__isSubscriptionEnabled:
            return ''
        if premiumState & PREMIUM_TYPE.PLUS:
            return text_styles.main(backport.text(R.strings.menu.headerButtons.doLabel.premium()))
        return text_styles.main(backport.text(R.strings.menu.common.premiumBuy())) if premiumState & PREMIUM_TYPE.BASIC else text_styles.gold(backport.text(R.strings.menu.common.premiumBuy()))

    def _getPremiumTooltipText(self, premiumState):
        if premiumState & PREMIUM_TYPE.PLUS:
            return TOOLTIPS.HEADER_PREMIUM_EXTEND
        return TOOLTIPS.HEADER_PREMIUM_UPGRADE if premiumState & PREMIUM_TYPE.BASIC else TOOLTIPS.HEADER_PREMIUM_BUY

    def _addListeners(self):
        self.startGlobalListening()
        self.app.containerManager.onViewAddedToContainer += self.__onViewAddedToContainer
        self.wallet.onWalletStatusChanged += self.__onWalletChanged
        self.gameSession.onPremiumNotify += self.__onPremiumTimeChanged
        self.gameSession.onPremiumTypeChanged += self._onPremiumTypeChanged
        self.igrCtrl.onIgrTypeChanged += self.__onIGRChanged
        self.lobbyContext.getServerSettings().onServerSettingsChange += self.__onServerSettingChanged
        g_currentVehicle.onChanged += self.__onVehicleChanged
        g_currentPreviewVehicle.onChanged += self.__onVehicleChanged
        self.hangarSpace.onSpaceCreate += self.__onHangarSpaceCreated
        self.hangarSpace.onSpaceDestroy += self.__onHangarSpaceDestroy
        self.eventsCache.onSyncCompleted += self.__onEventsCacheResync
        self.eventsCache.onProgressUpdated += self.__onEventsCacheResync
        self.eventsCache.onEventsVisited += self.__onEventsVisited
        self.eventsCache.onProfileVisited += self.__onProfileVisited
        self.eventsCache.onPersonalQuestsVisited += self.__onMissionsVisited
        self.itemsCache.onSyncCompleted += self.__onItemsCacheResync
        self.linkedSetController.onStateChanged += self.__onLinkedSetStateChanged
        self.boosters.onBoosterChangeNotify += self.__onUpdateGoodies
        self.boosters.onReserveTimerTick += self.__onUpdateGoodies
        self.rankedController.onUpdated += self.__updateRanked
        self.rankedController.onGameModeStatusUpdated += self.__updateRanked
        self.epicController.onUpdated += self.__updateEpic
        self.epicController.onEventEnded += self.__epicEventEnded
        self.eventProgressionController.onUpdated += self.__updateeventProgressionController
        self.epicController.onPrimeTimeStatusUpdated += self.__updateEpic
        self.__battleRoyaleController.onUpdated += self.__updateRoyale
        self.__battleRoyaleController.onPrimeTimeStatusUpdated += self.__updateRoyale
        self.badgesController.onUpdated += self.__updateBadge
        self.anonymizerController.onStateChanged += self.__updateAnonymizedState
        self.clanNotificationCtrl.onClanNotificationUpdated += self.__updateStrongholdCounter
        self.techTreeEventsListener.onSettingsChanged += self._updateHangarMenuData
        self.addListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdated, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.CoolDownEvent.PREBATTLE, self.__handleSetPrebattleCoolDown, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.BubbleTooltipEvent.SHOW, self.__showBubbleTooltip, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.CloseWindowEvent.GOLD_FISH_CLOSED, self.__onGoldFishWindowClosed, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(HEADER_BUTTONS_COUNTERS_CHANGED_EVENT, self.__onCounterChanged, scope=EVENT_BUS_SCOPE.DEFAULT)
        g_clientUpdateManager.addCurrencyCallback(Currency.CREDITS, self.__setCredits)
        g_clientUpdateManager.addCurrencyCallback(Currency.GOLD, self.__setGold)
        g_clientUpdateManager.addCurrencyCallback(Currency.CRYSTAL, self.__setCrystal)
        g_clientUpdateManager.addCallbacks({'stats.freeXP': self.__setFreeXP,
         'stats.clanInfo': self.__updatePlayerInfoPanel,
         'goodies': self.__updateBoostersStatus,
         'cache.activeOrders': self.__updateBoostersStatus,
         'account.activePremiumExpiryTime': self.__onPremiumExpireTimeChanged,
         'cache.SPA': self.__onSPAUpdated})
        self.as_setFightButtonS(i18n.makeString('#menu:headerButtons/battle'))
        self.as_setWalletStatusS(self.wallet.componentsStatuses)
        self.as_setPremShopDataS(RES_ICONS.MAPS_ICONS_LOBBY_ICON_PREMSHOP, MENU.HEADERBUTTONS_BTNLABEL_PREMSHOP, TOOLTIPS.HEADER_PREMSHOP, TOOLTIP_TYPES.COMPLEX)
        self.as_initOnlineCounterS(constants.IS_SHOW_SERVER_STATS)
        if constants.IS_SHOW_SERVER_STATS:
            self.serverStats.onStatsReceived += self.__onStatsReceived
            self.__onStatsReceived()
        else:
            self.as_setServerNameS(makeHtmlString('html_templates:lobby', 'onlineCounter', {'key': self.connectionMgr.serverUserNameShort,
             'delimiter': '',
             'value': ''}))
        self.updateAccountInfo()
        self.__updateServerData()
        if not isTimeToShowGoldFishPromo():
            enabledVal = isGoldFishActionActive()
            tooltip = TOOLTIPS.HEADER_BUTTONS_GOLD_ACTION if enabledVal else TOOLTIPS.HEADER_BUTTONS_GOLD
            self.as_setGoldFishEnabledS(enabledVal, False, tooltip, TOOLTIP_TYPES.COMPLEX)
        g_preDefinedHosts.onPingPerformed += self.__onPingPerformed
        g_preDefinedHosts.requestPing()
        self.settingsCore.onSettingsChanged += self.__onSettingsChanged
        self.addListener(events.TutorialEvent.OVERRIDE_HANGAR_MENU_BUTTONS, self.__onOverrideHangarMenuButtons, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.TutorialEvent.OVERRIDE_HEADER_MENU_BUTTONS, self.__onOverrideHeaderMenuButtons, scope=EVENT_BUS_SCOPE.LOBBY)
        self.addListener(events.LobbyHeaderMenuEvent.TOGGLE_VISIBILITY, self.__onToggleVisibilityMenu, scope=EVENT_BUS_SCOPE.LOBBY)
        self.demountKitNovelty.onUpdated += self.__updateStorageTabCounter
        self.offersNovelty.onUpdated += self.__updateStorageTabCounter
        AccountSettings.onSettingsChanging += self.__onAccountSettingsChanging

    def _removeListeners(self):
        g_clientUpdateManager.removeObjectCallbacks(self)
        self.stopGlobalListening()
        self.removeListener(events.FightButtonEvent.FIGHT_BUTTON_UPDATE, self.__handleFightButtonUpdated, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.CoolDownEvent.PREBATTLE, self.__handleSetPrebattleCoolDown, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.BubbleTooltipEvent.SHOW, self.__showBubbleTooltip, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.CloseWindowEvent.GOLD_FISH_CLOSED, self.__onGoldFishWindowClosed, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(HEADER_BUTTONS_COUNTERS_CHANGED_EVENT, self.__onCounterChanged, scope=EVENT_BUS_SCOPE.DEFAULT)
        self.anonymizerController.onStateChanged -= self.__updateAnonymizedState
        self.gameSession.onPremiumNotify -= self.__onPremiumTimeChanged
        self.gameSession.onPremiumTypeChanged -= self._onPremiumTypeChanged
        self.wallet.onWalletStatusChanged -= self.__onWalletChanged
        self.igrCtrl.onIgrTypeChanged -= self.__onIGRChanged
        self.lobbyContext.getServerSettings().onServerSettingsChange -= self.__onServerSettingChanged
        g_currentVehicle.onChanged -= self.__onVehicleChanged
        g_currentPreviewVehicle.onChanged -= self.__onVehicleChanged
        self.hangarSpace.onSpaceCreate -= self.__onHangarSpaceCreated
        self.hangarSpace.onSpaceDestroy -= self.__onHangarSpaceDestroy
        self.eventsCache.onSyncCompleted -= self.__onEventsCacheResync
        self.eventsCache.onProgressUpdated -= self.__onEventsCacheResync
        self.eventsCache.onEventsVisited -= self.__onEventsVisited
        self.eventsCache.onProfileVisited -= self.__onProfileVisited
        self.eventsCache.onPersonalQuestsVisited -= self.__onMissionsVisited
        self.itemsCache.onSyncCompleted -= self.__onItemsCacheResync
        self.linkedSetController.onStateChanged -= self.__onLinkedSetStateChanged
        self.rankedController.onUpdated -= self.__updateRanked
        self.rankedController.onGameModeStatusUpdated -= self.__updateRanked
        self.epicController.onUpdated -= self.__updateEpic
        self.epicController.onEventEnded -= self.__epicEventEnded
        self.eventProgressionController.onUpdated -= self.__updateeventProgressionController
        self.epicController.onPrimeTimeStatusUpdated -= self.__updateEpic
        self.__battleRoyaleController.onUpdated -= self.__updateRoyale
        self.__battleRoyaleController.onPrimeTimeStatusUpdated -= self.__updateRoyale
        self.badgesController.onUpdated -= self.__updateBadge
        self.clanNotificationCtrl.onClanNotificationUpdated -= self.__updateStrongholdCounter
        self.app.containerManager.onViewAddedToContainer -= self.__onViewAddedToContainer
        if constants.IS_SHOW_SERVER_STATS:
            self.serverStats.onStatsReceived -= self.__onStatsReceived
        self.boosters.onBoosterChangeNotify -= self.__onUpdateGoodies
        self.boosters.onReserveTimerTick -= self.__onUpdateGoodies
        g_preDefinedHosts.onPingPerformed -= self.__onPingPerformed
        self.settingsCore.onSettingsChanged -= self.__onSettingsChanged
        self.techTreeEventsListener.onSettingsChanged -= self._updateHangarMenuData
        self.removeListener(events.TutorialEvent.OVERRIDE_HANGAR_MENU_BUTTONS, self.__onOverrideHangarMenuButtons, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.TutorialEvent.OVERRIDE_HEADER_MENU_BUTTONS, self.__onOverrideHeaderMenuButtons, scope=EVENT_BUS_SCOPE.LOBBY)
        self.removeListener(events.LobbyHeaderMenuEvent.TOGGLE_VISIBILITY, self.__onToggleVisibilityMenu, scope=EVENT_BUS_SCOPE.LOBBY)
        self.demountKitNovelty.onUpdated -= self.__updateStorageTabCounter
        self.offersNovelty.onUpdated -= self.__updateStorageTabCounter
        AccountSettings.onSettingsChanging -= self.__onAccountSettingsChanging

    def __updateAccountAttrs(self):
        accAttrs = self.itemsCache.items.stats.attributes
        battle_selector_items.getItems().validateAccountAttrs(accAttrs)
        self.__setAccountsAttrs()

    def __updateServerData(self):
        serverShortName = self.connectionMgr.serverUserNameShort.strip().split(' ')[-1]
        if len(serverShortName) > _MAX_HEADER_SERVER_NAME_LEN:
            serverShortName = _SERVER_NAME_PREFIX % serverShortName[:_MAX_HEADER_SERVER_NAME_LEN]
        self.as_setServerS(serverShortName, TOOLTIPS_CONSTANTS.SETTINGS_BUTTON, TOOLTIP_TYPES.SPECIAL)

    def __updateServerName(self):
        serverShortName = self.connectionMgr.serverUserNameShort.strip().split(' ')[-1]
        if len(serverShortName) > _MAX_HEADER_SERVER_NAME_LEN:
            serverShortName = _SERVER_NAME_PREFIX % serverShortName[:_MAX_HEADER_SERVER_NAME_LEN]
        self.as_setServerS(serverShortName, TOOLTIPS_CONSTANTS.SETTINGS_BUTTON, TOOLTIP_TYPES.SPECIAL)

    def __updatePlayerInfoPanel(self, clanInfo, diff=None):
        if not isPlayerAccount():
            return
        else:
            name = BigWorld.player().name
            if clanInfo and len(clanInfo) > 1:
                clanAbbrev = clanInfo[1]
            else:
                clanAbbrev = None
            self.as_nameResponseS({'userVO': {'fullName': self.lobbyContext.getPlayerFullName(name, clanInfo=clanInfo),
                        'userName': name,
                        'clanAbbrev': clanAbbrev},
             'isTeamKiller': self.itemsCache.items.stats.isTeamKiller,
             'tooltip': TOOLTIPS.HEADER_ACCOUNT,
             'tooltipType': TOOLTIP_TYPES.COMPLEX})
            self.__updateBoostersStatus()
            self.__removeClanIconFromMemory()
            if g_clanCache.clanDBID:
                self.requestClanEmblem16x16(g_clanCache.clanDBID)
            else:
                self._updateHangarMenuData()
            if diff is not None and any((self.goodiesCache.haveBooster(itemId) for itemId in diff.keys())):
                SoundGroupsInstance.playSound2D('warehouse_booster')
            return

    def __updateAnonymizedState(self, **_):
        self.as_updateAnonymizedStateS(self.anonymizerController.isAnonymized)

    def __updateBoostersStatus(self, *_):
        boosterPresenter = _BoosterInfoPresenter(self.goodiesCache)
        self.as_setBoosterDataS({'hasActiveBooster': boosterPresenter.hasActiveBoosters(),
         'hasAvailableBoosters': boosterPresenter.hasAvailableBoosters(),
         'boosterIcon': boosterPresenter.getIcon(),
         'boosterText': boosterPresenter.getText(),
         'boosterBg': boosterPresenter.getBg()})

    def __updateBadge(self):
        badge = self.badgesController.getPrefix()
        selected = badge is not None
        data = {}
        if selected:
            data = badge.getBadgeVO(ICONS_SIZES.X48)
        self.as_setBadgeS(data, selected)
        return

    def __onPremiumExpireTimeChanged(self, _):
        self.__updateAccountAttrs()

    def __getWalletTooltipSettings(self, btnType):
        currencyStatus = self.wallet.componentsStatuses.get(btnType, WalletController.STATUS.SYNCING)
        if constants.IS_SINGAPORE and btnType in (LobbyHeader.BUTTONS.CREDITS, LobbyHeader.BUTTONS.GOLD):
            if not self.itemsCache.items.stats.mayConsumeWalletResources:
                tooltip = (TOOLTIPS.HEADER_BUTTONS + btnType, TOOLTIP_TYPES.COMPLEX)
            else:
                tooltip = (btnType + TOOLTIPS_CONSTANTS.SINGAPORE_WALLET_STATS, TOOLTIP_TYPES.SPECIAL)
        elif currencyStatus != WalletController.STATUS.AVAILABLE:
            tooltip = (TOOLTIPS.HEADER_BUTTONS + btnType, TOOLTIP_TYPES.COMPLEX)
        else:
            tooltip = (btnType + TOOLTIPS_CONSTANTS.HEADER_BUTTON_INFO, TOOLTIP_TYPES.SPECIAL)
        return tooltip

    def __setCredits(self, accCredits):
        btnType = LobbyHeader.BUTTONS.CREDITS
        if self.__isHeaderButtonPresent(btnType):
            isActionActive = self.itemsCache.items.shop.isCreditsConversionActionActive
            btnData = self._getWalletBtnData(btnType, accCredits, getBWFormatter(Currency.CREDITS), isActionActive)
            self.as_updateWalletBtnS(btnType, btnData)

    def __setGold(self, gold):
        btnType = LobbyHeader.BUTTONS.GOLD
        if self.__isHeaderButtonPresent(btnType):
            btnData = self._getWalletBtnData(btnType, gold, getBWFormatter(Currency.GOLD), isGoldFishActionActive())
            self.as_updateWalletBtnS(btnType, btnData)

    def __setCrystal(self, crystals):
        btnType = LobbyHeader.BUTTONS.CRYSTAL
        if self.__isHeaderButtonPresent(btnType):
            btnData = self._getWalletBtnData(btnType, crystals, getBWFormatter(Currency.CRYSTAL), False, False, False)
            self.as_updateWalletBtnS(btnType, btnData)

    def __setFreeXP(self, freeXP):
        btnType = LobbyHeader.BUTTONS.FREE_XP
        if self.__isHeaderButtonPresent(btnType):
            isActionActive = self.itemsCache.items.shop.isXPConversionActionActive
            btnData = self._getWalletBtnData(btnType, freeXP, backport.getIntegralFormat, isActionActive)
            self.as_updateWalletBtnS(btnType, btnData)

    def _getWalletBtnData(self, btnType, value, formatter, isHasAction=False, isDiscountEnabled=False, isNew=False):
        tooltip, tooltipType = self.__getWalletTooltipSettings(btnType)
        return {'money': formatter(value),
         'btnDoText': self._getWalletBtnDoText(btnType),
         'tooltip': tooltip,
         'tooltipType': tooltipType,
         'icon': btnType,
         'isHasAction': isHasAction,
         'isDiscountEnabled': isDiscountEnabled,
         'isNew': isNew,
         'shortMoneyValue': self.__getShortValue(value, formatter)}

    def _getWalletBtnDoText(self, btnType):
        return MENU.HEADERBUTTONS_BTNLABEL + btnType

    @staticmethod
    def __getShortValue(value, defFormatter):
        if value > _SHORT_VALUE_THRESHOLD:
            shortValue = math.floor(float(value) * _SHORT_VALUE_D / _SHORT_VALUE_DIVIDER) / _SHORT_VALUE_D
            formattedValue = '{:.{precision}f}'.format(shortValue, precision=_SHORT_VALUE_PRECISION)
            return i18n.makeString(_SHORT_VALUE_FMT_PATTERN, value=formattedValue)
        return defFormatter(value)

    def __setAccountsAttrs(self):
        premiumExpiryTime = self.itemsCache.items.stats.activePremiumExpiryTime
        isPremiumAccount = self.itemsCache.items.stats.isPremium
        if isPremiumAccount:
            iconName = 'premiumPlus'
            deltaInSeconds = float(time_utils.getTimeDeltaFromNow(time_utils.makeLocalServerTime(premiumExpiryTime)))
            if self.itemsCache.items.stats.isActivePremium(PREMIUM_TYPE.PLUS):
                premiumBtnLbl = text_styles.gold(backport.text(R.strings.menu.accountTypes.premiumPlus()))
                premiumBtnLblShort = text_styles.gold(backport.text(R.strings.menu.accountTypes.premiumPlusShort()))
            else:
                premiumBtnLbl = text_styles.neutral(backport.text(R.strings.menu.accountTypes.premium()))
                premiumBtnLblShort = text_styles.neutral(backport.text(R.strings.menu.accountTypes.premiumShort()))
                if deltaInSeconds > self.__PREM_WARNING_LIMIT:
                    iconName = 'premium'
            if deltaInSeconds <= self.__PREM_WARNING_LIMIT:
                htmlKey = 'premiumEnd-timeLabel'
            elif self.itemsCache.items.stats.isActivePremium(PREMIUM_TYPE.PLUS):
                htmlKey = 'premiumPlus-timeLabel'
            else:
                htmlKey = 'premium-timeLabel'
            timeLeft, timeMetric = self.__getPremiumExpiryTimeAttrs(deltaInSeconds)
            timeLabel = makeHtmlString('html_templates:lobby/header', htmlKey, {'time': timeLeft,
             'metric': timeMetric})
            premiumIcon = backport.image(R.images.gui.maps.icons.premacc.lobbyHeader.dyn(iconName)())
        else:
            premiumBtnLbl = text_styles.main(backport.text(R.strings.menu.accountTypes.base()))
            premiumBtnLblShort = premiumBtnLbl
            timeLabel = ''
            premiumIcon = None
        premiumState = self.itemsCache.items.stats.activePremiumType
        self.as_setPremiumParamsS({'btnLabel': premiumBtnLbl,
         'btnLabelShort': premiumBtnLblShort,
         'doLabel': self._getPremiumLabelText(premiumState),
         'timeLabel': timeLabel,
         'isHasAction': self.__hasPremiumPacketDiscount(),
         'isPremium': isPremiumAccount,
         'isSubscription': self.__isSubscriptionEnabled and isPremiumAccount,
         'premiumIcon': premiumIcon,
         'tooltip': self._getPremiumTooltipText(premiumState),
         'tooltipType': TOOLTIP_TYPES.COMPLEX})
        return

    @staticmethod
    def __getPremiumExpiryTimeAttrs(deltaInSeconds):
        if deltaInSeconds > time_utils.ONE_DAY:
            timeLeft = math.ceil(deltaInSeconds / time_utils.ONE_DAY)
            timeMetric = backport.text(R.strings.menu.header.account.premium.days())
        else:
            timeLeft = math.ceil(deltaInSeconds / time_utils.ONE_HOUR)
            timeMetric = backport.text(R.strings.menu.header.account.premium.hours())
        return (timeLeft, timeMetric)

    def __hasPremiumPacketDiscount(self):
        return self.itemsCache.items.shop.isActionOnPremium()

    def __triggerViewLoad(self, alias):
        if alias == self.TABS.BROWSER:
            self.chinaCtrl.showBrowser()
        elif alias == self.TABS.STORAGE:
            showStorage()
        else:
            event = g_entitiesFactories.makeLoadEvent(alias)
            if event is not None:
                self.fireEvent(event, scope=EVENT_BUS_SCOPE.LOBBY)
            else:
                LOG_ERROR('Invalid subview alias', alias)
                return
        self.__setCurrentScreen(alias)
        return

    def __setCurrentScreen(self, alias):
        self.__currentScreen = alias
        self.as_setScreenS(alias)

    def __onWalletChanged(self, status):
        self.__setGold(self.itemsCache.items.stats.actualGold)
        self.__setCrystal(self.itemsCache.items.stats.actualCrystal)
        if constants.IS_SINGAPORE:
            self.__setCredits(self.itemsCache.items.stats.actualCredits)
        self.__setFreeXP(self.itemsCache.items.stats.actualFreeXP)
        self.as_setWalletStatusS(status)

    def __onPremiumTimeChanged(self, *_):
        self.__updateAccountAttrs()

    def __onViewAddedToContainer(self, _, pyEntity):
        if pyEntity.viewType is ViewTypes.LOBBY_SUB:
            if pyEntity.alias in self.TABS.ALL():
                self.__setCurrentScreen(pyEntity.alias)

    def __getContainer(self, viewType):
        return self.app.containerManager.getContainer(viewType) if self.app is not None and self.app.containerManager is not None else None

    def __getBattleTypeSelectPopover(self):
        container = self.__getContainer(ViewTypes.WINDOW)
        view = None
        if container:
            view = container.getView({POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.BATTLE_TYPE_SELECT_POPOVER})
        return view

    def __getSquadTypeSelectPopover(self):
        container = self.__getContainer(ViewTypes.WINDOW)
        view = None
        if container:
            view = container.getView({POP_UP_CRITERIA.VIEW_ALIAS: VIEW_ALIAS.SQUAD_TYPE_SELECT_POPOVER})
        return view

    def __closeBattleTypeSelectPopover(self):
        view = self.__getBattleTypeSelectPopover()
        if view:
            view.destroy()

    def __closeSquadTypeSelectPopover(self):
        view = self.__getSquadTypeSelectPopover()
        if view:
            view.destroy()

    def __updateBattleTypeSelectPopover(self):
        view = self.__getBattleTypeSelectPopover()
        if view:
            view.update()

    def __updateSquadTypeSelectPopover(self):
        view = self.__getSquadTypeSelectPopover()
        if view:
            view.update()

    def __getEventTooltipData(self):
        header = i18n.makeString(TOOLTIPS.EVENT_SQUAD_DISABLE_HEADER)
        vehicle = self.eventsCache.getEventVehicles()[0]
        body = i18n.makeString(TOOLTIPS.EVENT_SQUAD_DISABLE_BODY, tankName=vehicle.shortUserName)
        return makeTooltip(header, body)

    def __getPreviewTooltipData(self):
        body = i18n.makeString(TOOLTIPS.HANGAR_STARTBTN_PREVIEW_BODY)
        return makeTooltip(None, body)

    def __getSquadFightBtnTooltipData(self, state):
        if state == UNIT_RESTRICTION.COMMANDER_VEHICLE_NOT_SELECTED:
            header = backport.text(R.strings.tooltips.hangar.startBtn.squadNotReady.header())
            body = backport.text(R.strings.tooltips.hangar.startBtn.squadNotReady.body())
        elif state == UNIT_RESTRICTION.VEHICLE_INVALID_LEVEL:
            header = backport.text(R.strings.tooltips.hangar.tankCarusel.wrongSquadVehicle.header())
            body = backport.text(R.strings.tooltips.hangar.tankCarusel.wrongSquadVehicle.body())
        elif state == UNIT_RESTRICTION.SPG_IS_FULL or state == UNIT_RESTRICTION.SPG_IS_FORBIDDEN:
            header = backport.text(R.strings.tooltips.hangar.tankCarusel.wrongSquadSPGVehicle.header())
            body = backport.text(R.strings.tooltips.hangar.tankCarusel.wrongSquadSPGVehicle.body())
        else:
            return ''
        return makeTooltip(header, body)

    def __getRankedFightBtnTooltipData(self, result):
        state = result.restriction
        resShortCut = R.strings.menu.headerButtons.fightBtn.tooltip
        if state == PRE_QUEUE_RESTRICTION.MODE_NOT_SET:
            header = backport.text(resShortCut.rankedNotSet.header())
            body = backport.text(resShortCut.rankedNotSet.body())
        elif state == PRE_QUEUE_RESTRICTION.MODE_DISABLED:
            header = backport.text(resShortCut.rankedDisabled.header())
            body = backport.text(resShortCut.rankedDisabled.body())
        elif state == PRE_QUEUE_RESTRICTION.LIMIT_LEVEL:
            levelStr = toRomanRangeString(result.ctx['levels'])
            levelSubStr = backport.text(resShortCut.rankedVehLevel.levelSubStr(), levels=levelStr)
            header = backport.text(resShortCut.rankedVehLevel.header())
            body = backport.text(resShortCut.rankedVehLevel.body(), levelSubStr=text_styles.neutral(levelSubStr))
        elif state == PRE_QUEUE_RESTRICTION.LIMIT_VEHICLE_TYPE:
            typeSubStr = text_styles.neutral(result.ctx['forbiddenType'])
            header = backport.text(resShortCut.rankedVehType.header())
            body = backport.text(resShortCut.rankedVehType.body(), forbiddenType=typeSubStr)
        elif state == PRE_QUEUE_RESTRICTION.LIMIT_VEHICLE_CLASS:
            classSubStr = text_styles.neutral(getTypeUserName(result.ctx['forbiddenClass'], False))
            header = backport.text(resShortCut.rankedVehClass.header())
            body = backport.text(resShortCut.rankedVehClass.body(), forbiddenClass=classSubStr)
        else:
            return ''
        return makeTooltip(header, body)

    def __getEpicFightBtnTooltipData(self, result):
        state = result.restriction
        if state == PRE_QUEUE_RESTRICTION.MODE_DISABLED:
            header = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.battleRoyaleDisabled.header())
            body = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.battleRoyaleDisabled.body())
        elif state == PRE_QUEUE_RESTRICTION.LIMIT_LEVEL:
            header = i18n.makeString(MENU.HEADERBUTTONS_FIGHTBTN_TOOLTIP_EPICLEVELREQUIRED_HEADER)
            body = text_styles.main(i18n.makeString(MENU.HEADERBUTTONS_FIGHTBTN_TOOLTIP_EPICLEVELREQUIRED_BODYSTART, requirements=text_styles.neutral(i18n.makeString(MENU.HEADERBUTTONS_FIGHTBTN_TOOLTIP_EPICLEVELREQUIRED_BODYEND, level=toRomanRangeString(result.ctx['levels'], 1)))))
        elif state == UNIT_RESTRICTION.UNSUITABLE_VEHICLE:
            header = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.wrongVehicle.header())
            body = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.wrongVehicle.body())
        elif state == UNIT_RESTRICTION.UNIT_NOT_FULL:
            header = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.wrongPlayers.header())
            body = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.wrongPlayers.body())
        elif state == UNIT_RESTRICTION.NOT_READY_IN_SLOTS:
            header = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.notReady.header())
            body = backport.text(R.strings.tooltips.hangar.startBtn.battleRoyaleSquadNotReady.notReady.body())
        elif state == UNIT_RESTRICTION.CURFEW:
            header = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.battleRoyaleDisabled.header())
            body = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.battleRoyaleDisabled.body())
        elif state == PREBATTLE_RESTRICTION.VEHICLE_NOT_SUPPORTED:
            header = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.unsutableToBattleRoyale.header())
            body = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.unsutableToBattleRoyale.body())
        else:
            return ''
        return makeTooltip(header, body)

    def __getUnsuitableToQueueTooltipData(self, result):
        state = result.restriction
        if state in (PREBATTLE_RESTRICTION.VEHICLE_NOT_SUPPORTED, UNIT_RESTRICTION.VEHICLE_WRONG_MODE):
            header = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.epicBattleOnly.header())
            body = backport.text(R.strings.menu.headerButtons.fightBtn.tooltip.epicBattleOnly.body())
            return makeTooltip(header, body)

    def __getSandboxTooltipData(self, result):
        state = result.restriction
        return makeTooltip(i18n.makeString(MENU.HEADERBUTTONS_FIGHTBTN_TOOLTIP_SANDBOX_INVALID_HEADER), i18n.makeString(MENU.HEADERBUTTONS_FIGHTBTN_TOOLTIP_SANDBOX_INVALID_LEVEL_BODY, levels=toRomanRangeString(result.ctx['levels'], 1))) if state == PRE_QUEUE_RESTRICTION.LIMIT_LEVEL else ''

    def _updatePrebattleControls(self):
        if self._isLobbyHeaderControlsDisabled:
            return
        if not self.prbDispatcher:
            return
        items = battle_selector_items.getItems()
        squadItems = battle_selector_items.getSquadItems()
        state = self.prbDispatcher.getFunctionalState()
        selected = items.update(state)
        squadSelected = squadItems.update(state)
        result = self.prbEntity.canPlayerDoAction()
        canDo, canDoMsg = result.isValid, result.restriction
        playerInfo = self.prbDispatcher.getPlayerInfo()
        if selected.isInSquad(state):
            isInSquad = True
            self.as_doDisableHeaderButtonS(self.BUTTONS.SQUAD, True)
        else:
            isInSquad = False
            self.as_doDisableHeaderButtonS(self.BUTTONS.SQUAD, self.prbDispatcher.getEntity().getPermissions().canCreateSquad())
        isNavigationEnabled = not state.isNavigationDisabled()
        isEvent = self.eventsCache.isEventEnabled()
        isRanked = state.isInPreQueue(constants.QUEUE_TYPE.RANKED)
        isSandbox = state.isInPreQueue(constants.QUEUE_TYPE.SANDBOX)
        isEpic = state.isInPreQueue(constants.QUEUE_TYPE.EPIC)
        iseventProgressionControllerEnabled = self.eventProgressionController.modeIsEnabled()
        isRoyale = state.isInPreQueue(constants.QUEUE_TYPE.BATTLE_ROYALE) or state.isInUnit(constants.PREBATTLE_TYPE.BATTLE_ROYALE)
        if self.__isHeaderButtonPresent(LobbyHeader.BUTTONS.SQUAD):
            if not isNavigationEnabled:
                tooltip = ''
            elif isInSquad:
                tooltip = TOOLTIPS.HEADER_SQUAD_MEMBER
            elif isEvent:
                tooltip = TOOLTIPS.HEADER_SQUAD_MEMBER
            elif isRanked:
                tooltip = TOOLTIPS.HEADER_RANKEDSQUAD
            elif isInSquad:
                tooltip = TOOLTIPS.HEADER_SQUAD_MEMBER
            elif isEvent:
                tooltip = TOOLTIPS.HEADER_SQUAD_MEMBER
            elif isRanked:
                tooltip = TOOLTIPS.HEADER_RANKEDSQUAD
            elif isRoyale:
                tooltip = TOOLTIPS.HEADER_BATTLEROYALESQUAD
            else:
                tooltip = TOOLTIPS.HEADER_SQUAD
            if isRoyale:
                iconSquad = backport.image(R.images.gui.maps.icons.battleTypes.c_40x40.royaleSquad())
            elif state.isInUnit(constants.PREBATTLE_TYPE.EVENT):
                iconSquad = backport.image(R.images.gui.maps.icons.battleTypes.c_40x40.eventSquad())
            else:
                iconSquad = backport.image(R.images.gui.maps.icons.battleTypes.c_40x40.squad())
            self.as_updateSquadS(isInSquad, tooltip, TOOLTIP_TYPES.COMPLEX, isEvent, iconSquad)
        self.__isFightBtnDisabled = self._checkFightButtonDisabled(canDo, selected.isLocked())
        tooltipData, isSpecial = '', False
        if self.__isFightBtnDisabled and not state.hasLockedState:
            if isSandbox:
                tooltipData = self.__getSandboxTooltipData(result)
            elif isEvent and state.isInUnit(constants.PREBATTLE_TYPE.EVENT):
                tooltipData = self.__getEventTooltipData()
            elif g_currentVehicle.isUnsuitableToQueue() and g_currentVehicle.isOnlyForEpicBattles():
                tooltipData = self.__getUnsuitableToQueueTooltipData(result)
            elif (isEpic or isRoyale) and iseventProgressionControllerEnabled:
                tooltipData = self.__getEpicFightBtnTooltipData(result)
            elif isInSquad:
                tooltipData = self.__getSquadFightBtnTooltipData(canDoMsg)
            elif g_currentPreviewVehicle.isPresent():
                tooltipData = self.__getPreviewTooltipData()
            elif isRanked:
                tooltipData = self.__getRankedFightBtnTooltipData(result)
            elif g_currentVehicle.isUnsuitableToQueue() and g_currentVehicle.isOnlyForEpicBattles():
                tooltipData = self.__getUnsuitableToQueueTooltipData(result)
        elif isRoyale and g_currentVehicle.isOnlyForBattleRoyaleBattles():
            tooltipData = TOOLTIPS_CONSTANTS.BATTLE_ROYALE_PERF_ADVANCED
            isSpecial = True
        self.as_setFightBtnTooltipS(tooltipData, isSpecial)
        if self.hangarSpace.spaceInited or not self.bootcampController.isInBootcamp():
            self.as_disableFightButtonS(self.__isFightBtnDisabled)
        self.as_setFightButtonS(selected.getFightButtonLabel(state, playerInfo))
        if self.__isHeaderButtonPresent(LobbyHeader.BUTTONS.BATTLE_SELECTOR):
            eventEnabled = not self.bootcampController.isInBootcamp() and (self.rankedController.isAvailable() or self.eventProgressionController.isEnabled)
            self.as_updateBattleTypeS(i18n.makeString(selected.getLabel()), selected.getSmallIcon(), selected.isSelectorBtnEnabled(), TOOLTIPS.HEADER_BATTLETYPE, TOOLTIP_TYPES.COMPLEX, selected.getData(), eventEnabled, eventEnabled and not WWISE.WG_isMSR())
        else:
            self.as_updateBattleTypeS('', '', False, '', TOOLTIP_TYPES.NONE, '', False, False)
        if selected.isDisabled():
            self.__closeBattleTypeSelectPopover()
        else:
            self.__updateBattleTypeSelectPopover()
        if squadSelected.isDisabled():
            self.__closeSquadTypeSelectPopover()
        else:
            self.__updateSquadTypeSelectPopover()
        for button in self.PRB_NAVIGATION_DISABLE_BUTTONS:
            self.as_doDisableHeaderButtonS(button, isNavigationEnabled)

        if not isNavigationEnabled:
            self.as_doDisableNavigationS()
        else:
            self.as_setScreenS(self.__currentScreen)
        self.__updateAccountAttrs()

    def __onHangarSpaceCreated(self):
        if self.bootcampController.isInBootcamp():
            self.as_disableFightButtonS(self.__isFightBtnDisabled)

    def __onHangarSpaceDestroy(self, inited):
        if inited and self.bootcampController.isInBootcamp():
            self.as_disableFightButtonS(True)

    def __onToggleVisibilityMenu(self, event):
        state = event.ctx['state']
        self.__menuVisibilityHelper.updateStates(state)
        activeState = self.__menuVisibilityHelper.getActiveState()
        self.as_toggleVisibilityMenuS(activeState)

    def _checkFightButtonDisabled(self, canDo, isLocked):
        return not canDo or isLocked

    def _updateTabCounters(self):
        self._updatePremiumQuestsVisitedStatus(self.eventsCache.getPremiumQuests())
        self.__onProfileVisited()
        self.__updateStrongholdCounter()
        self.__updateShopTabCounter()
        self.__updateStorageTabCounter()
        self.__onEventsVisited()
        self.__updateMissionsTabCounter()
        self.__updateRecruitsTabCounter(self.TABS.BARRACKS)

    def _onPremiumTypeChanged(self, _):
        self._updateTabCounters()

    def __handleFightButtonUpdated(self, _):
        self._updatePrebattleControls()

    def __handleSetPrebattleCoolDown(self, event):
        if not self.prbDispatcher:
            return
        playerInfo = self.prbDispatcher.getPlayerInfo()
        isCreator = playerInfo.isCreator
        if event.requestID is REQUEST_TYPE.SET_PLAYER_STATE and not isCreator:
            self.as_setCoolDownForReadyS(event.coolDown)

    def __showBubbleTooltip(self, event):
        self.as_showBubbleTooltipS(event.getMessage(), event.getDuration())

    def __onVehicleChanged(self, *_):
        self._updatePrebattleControls()

    def __onEventsCacheResync(self, *_):
        self._updatePrebattleControls()
        self._updateTabCounters()
        self.updateMoneyStats()
        self.updateXPInfo()

    def __onItemsCacheResync(self, *_):
        self.__updateRecruitsTabCounter(self.TABS.BARRACKS)

    def __onLinkedSetStateChanged(self, *_):
        self.__onEventsCacheResync()

    def __onEventsVisited(self, counters=None):
        if counters is not None:
            if 'missions' in counters:
                self.__onMissionVisited(counters['missions'])
        else:
            quests = self.eventsCache.getAdvisableQuests()
            counter = len(quest_settings.getNewCommonEvents(quests.values()))
            self.__onMissionVisited(counter)
        return

    @staticmethod
    def _updatePremiumQuestsVisitedStatus(quests):
        if not quests:
            return
        firstPremiumId = sorted(quests.keys())[0]
        currFirstPremMissionCompleted = quests[firstPremiumId].isCompleted()
        if currFirstPremMissionCompleted:
            return
        questSettings = AccountSettings.getSettings(QUESTS)
        prevFirstPremMissionCompleted = questSettings.get(QUEST_DELTAS, {}).get(QUEST_DELTAS_COMPLETION, {}).get(firstPremiumId, False)
        if prevFirstPremMissionCompleted and firstPremiumId in questSettings['visited']:
            questSettings['visited'] = tuple((t for t in questSettings['visited'] if t != firstPremiumId))
            AccountSettings.setSettings(QUESTS, questSettings)

    def __onMissionVisited(self, counter):
        if counter:
            self.__setCounter(self.TABS.MISSIONS, counter)
        else:
            self.__hideCounter(self.TABS.MISSIONS)

    def __onProfileVisited(self):
        self.__updateProfileTabCounter()

    def __onMissionsVisited(self):
        alias = self.TABS.PERSONAL_MISSIONS
        counters = AccountSettings.getCounters(NEW_LOBBY_TAB_COUNTER)
        if alias in counters and counters[alias]:
            counters[alias] = False
            AccountSettings.setCounters(NEW_LOBBY_TAB_COUNTER, counters)
        self.__updateMissionsTabCounter()

    def __onIGRChanged(self, *_):
        self._updatePrebattleControls()

    def __updateRanked(self, *_):
        self._updatePrebattleControls()
        self._updateTabCounters()

    def __updateEpic(self, *_):
        self._updatePrebattleControls()

    def __epicEventEnded(self, *_):
        state = self.prbDispatcher.getFunctionalState()
        if state.isQueueSelected(constants.QUEUE_TYPE.EPIC):
            self.__doSelect(PREBATTLE_ACTION_NAME.RANDOM)
            self._updatePrebattleControls()

    def __updateeventProgressionController(self, *_):
        self._updatePrebattleControls()

    def __updateRoyale(self, *_):
        self._updatePrebattleControls()

    def _updateStrongholdsSelector(self):
        strongholdEnabled = isStrongholdsEnabled()
        clansTabReplaceStrongholds = isClansTabReplaceStrongholds()
        clanDBID = self.itemsCache.items.stats.clanDBID
        if not clanDBID:
            strongholdsTabConfig = {(True, False): (MENU.HEADERBUTTONS_CLAN, TOOLTIPS.HEADER_BUTTONS_FORTS),
             (False, False): (MENU.HEADERBUTTONS_CLAN, TOOLTIPS.HEADER_BUTTONS_FORTS_TURNEDOFF),
             (True, True): (MENU.HEADERBUTTONS_CLANS, TOOLTIPS.HEADER_BUTTONS_CLANS),
             (False, True): (MENU.HEADERBUTTONS_CLANS, TOOLTIPS.HEADER_BUTTONS_CLANS_TURNEDOFF)}
            label, tooltip = strongholdsTabConfig[strongholdEnabled, clansTabReplaceStrongholds]
        else:
            label = MENU.HEADERBUTTONS_CLAN
            tooltip = TOOLTIPS.HEADER_BUTTONS_FORTS if strongholdEnabled else TOOLTIPS.HEADER_BUTTONS_FORTS_TURNEDOFF
        return {'label': label,
         'value': VIEW_ALIAS.LOBBY_STRONGHOLD,
         'tooltip': tooltip,
         'icon': self.__clanIconID,
         'enabled': strongholdEnabled}

    def _getPersonalMissionSelectorTabData(self):
        if self.lobbyContext.getServerSettings().isPersonalMissionsEnabled():
            tooltip = TOOLTIPS.HEADER_BUTTONS_PERSONALMISSIONS
            enabled = True
        else:
            tooltip = TOOLTIPS.HEADER_BUTTONS_PERSONALMISSIONSDISABLED
            enabled = False
        return {'label': MENU.HEADERBUTTONS_PERSONALMISSIONS,
         'value': self.TABS.PERSONAL_MISSIONS,
         'tooltip': tooltip,
         'enabled': enabled,
         'subValues': [self.TABS.PERSONAL_MISSIONS_PAGE]}

    def _getHangarMenuItemDataProvider(self):
        tabDataProvider = [{'label': MENU.HEADERBUTTONS_HANGAR,
          'value': self.TABS.HANGAR,
          'textColor': 16764006,
          'textColorOver': 16768409,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_HANGAR},
         {'label': MENU.HEADERBUTTONS_SHOP,
          'value': self.TABS.STORE,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_SHOP},
         {'label': MENU.HEADERBUTTONS_STORAGE,
          'value': self.TABS.STORAGE,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_STORAGE},
         {'label': MENU.HEADERBUTTONS_MISSIONS,
          'value': self.TABS.MISSIONS,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_MISSIONS},
         self._getPersonalMissionSelectorTabData(),
         {'label': MENU.HEADERBUTTONS_PROFILE,
          'value': self.TABS.PROFILE,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_PROFILE}]
        techTreeData = {'label': MENU.HEADERBUTTONS_TECHTREE,
         'value': self.TABS.TECHTREE,
         'tooltip': TOOLTIPS.HEADER_BUTTONS_TECHTREE,
         'isTooltipSpecial': False,
         'subValues': [self.TABS.RESEARCH]}
        if self.techTreeEventsListener.actions:
            techTreeData['tooltip'] = TOOLTIPS_CONSTANTS.TECHTREE_DISCOUNT_INFO
            techTreeData['isTooltipSpecial'] = True
            if self.techTreeEventsListener.getNations(unviewed=True):
                techTreeData['actionIcon'] = backport.image(R.images.gui.maps.icons.library.discountIndicator())
        tabDataProvider.extend([techTreeData])
        tabDataProvider.extend([{'label': MENU.HEADERBUTTONS_BARRACKS,
          'value': self.TABS.BARRACKS,
          'tooltip': TOOLTIPS.HEADER_BUTTONS_BARRACKS}])
        if constants.IS_CHINA:
            tabDataProvider.append({'label': MENU.HEADERBUTTONS_BROWSER,
             'value': self.TABS.BROWSER,
             'tooltip': TOOLTIPS.HEADER_BUTTONS_BROWSER})
        if isStrongholdsEnabled():
            tabDataProvider.append(self._updateStrongholdsSelector())
        override = self.app.tutorialManager.lastHangarMenuButtonsOverride
        if override is not None:
            tabDataProvider[:] = ifilter(lambda item: item['value'] in override, tabDataProvider)
        return tabDataProvider

    def _updateHangarMenuData(self):
        self.as_setHangarMenuDataS(self._getHangarMenuItemDataProvider())
        self._updateTabCounters()

    def __onOverrideHangarMenuButtons(self, _=None):
        self.__hideDisabledTabCounters()
        self._updateHangarMenuData()

    def __onOverrideHeaderMenuButtons(self, _=None):
        menuOverride = self.app.tutorialManager.lastHeaderMenuButtonsOverride
        self.as_setHeaderButtonsS(menuOverride)
        if LobbyHeader.BUTTONS.BATTLE_SELECTOR in menuOverride:
            self._updatePrebattleControls()

    def __onSPAUpdated(self, _):
        self.__updateGoldFishState(False)
        self.__updateSubscriptionState()

    def __onGoldFishWindowClosed(self, _):
        self.__updateGoldFishState(True)

    def __updateGoldFishState(self, isAnimEnabled):
        enabledVal = isGoldFishActionActive()
        tooltip = TOOLTIPS.HEADER_BUTTONS_GOLD_ACTION if enabledVal else TOOLTIPS.HEADER_BUTTONS_GOLD
        self.as_setGoldFishEnabledS(enabledVal, isAnimEnabled, tooltip, TOOLTIP_TYPES.COMPLEX)

    def __updateSubscriptionState(self):
        subscriptionEnabled = isSubscriptionEnabled()
        if subscriptionEnabled != self.__isSubscriptionEnabled:
            self.__isSubscriptionEnabled = subscriptionEnabled
            self.__updateAccountAttrs()

    def __onServerSettingChanged(self, diff):
        strongholdSettingsChanged = 'strongholdSettings' in diff
        epicRandomStateChanged = 'isEpicRandomEnabled' in diff
        commandBattlesStateChanged = 'isCommandBattleEnabled' in diff
        bootcampStateChanged = 'isBootcampEnabled' in diff
        battleRoyaleStateChanged = constants.Configs.BATTLE_ROYALE_CONFIG.value in diff
        updateHangarMenuData = any((strongholdSettingsChanged,
         epicRandomStateChanged,
         commandBattlesStateChanged,
         'isRegularQuestEnabled' in diff))
        updatePrebattleControls = any((strongholdSettingsChanged,
         epicRandomStateChanged,
         commandBattlesStateChanged,
         bootcampStateChanged,
         'isSandboxEnabled' in diff,
         'ranked_config' in diff,
         'epic_config' in diff,
         battleRoyaleStateChanged))
        if bootcampStateChanged:
            battle_selector_items.clear()
            battle_selector_items.create()
        if updateHangarMenuData:
            self._updateHangarMenuData()
        if updatePrebattleControls:
            self._updatePrebattleControls()
        if not updateHangarMenuData and 'hallOfFame' in diff:
            self.__updateProfileTabCounter()

    def __updateProfileTabCounter(self):
        if self.lobbyContext.getServerSettings().isHofEnabled():
            hofCounter = getAchievementsTabCounter()
            if hofCounter:
                self.__setCounter(self.TABS.PROFILE, hofCounter)
            else:
                self.__hideCounter(self.TABS.PROFILE)
        else:
            self.__hideCounter(self.TABS.PROFILE)

    def __updateMissionsTabCounter(self):
        counters = AccountSettings.getCounters(NEW_LOBBY_TAB_COUNTER)
        alias = self.TABS.PERSONAL_MISSIONS
        if alias not in counters:
            counters[alias] = True
            AccountSettings.setCounters(NEW_LOBBY_TAB_COUNTER, counters)
        if counters[alias]:
            self.__setCounter(alias, 1)
        else:
            self.__hideCounter(alias)

    def __updateRecruitsTabCounter(self, alias):
        counter = recruit_helper.getNewRecruitsCounter()
        if counter:
            self.__setCounter(alias, counter)
        else:
            self.__hideCounter(alias)

    def __updateShopTabCounter(self):
        self.__updateTabCounter(self.TABS.STORE)

    def __updateStorageTabCounter(self):
        self.__updateTabCounter(self.TABS.STORAGE, self.demountKitNovelty.noveltyCount + self.offersNovelty.noveltyCount)

    def __updateStrongholdCounter(self):
        self.__updateTabCounter(self.TABS.STRONGHOLD, self.clanNotificationCtrl.newsCounter)

    def __updateTabCounter(self, alias, counter=None):
        if alias not in self.TABS.ALL():
            return
        else:
            if alias in self.ACCOUNT_SETTINGS_COUNTERS:
                counters = AccountSettings.getCounters(NEW_LOBBY_TAB_COUNTER)
                if alias not in counters or _isActiveShopNewCounters():
                    counters[alias] = backport.text(R.strings.menu.headerButtons.defaultCounter())
                    _updateShopNewCounters()
                elif counter is not None:
                    counters[alias] = counter
                AccountSettings.setCounters(NEW_LOBBY_TAB_COUNTER, counters)
                counter = counters[alias]
            if counter:
                self.__setCounter(alias, counter)
            else:
                self.__hideCounter(alias)
            return

    def __onUpdateGoodies(self, *_):
        self.__updateBoostersStatus()

    def __onPingPerformed(self, _):
        self.__updatePing()

    def __onSettingsChanged(self, diff):
        if 'isColorBlind' in diff:
            self.__updatePing()
        if KNOWN_SELECTOR_BATTLES in diff:
            self._updatePrebattleControls()

    def __updatePing(self):
        pingData = g_preDefinedHosts.getHostPingData(self.connectionMgr.url)
        pingStatus = pingData.status
        pingStatus = PING_STATUSES.UNDEFINED if pingStatus == PING_STATUSES.REQUESTED else pingStatus
        self.as_updatePingStatusS(pingStatus, self.settingsCore.getSetting('isColorBlind'))

    def __onCounterChanged(self, event):
        self.__updateTabCounter(event.ctx.get('alias'), event.ctx.get('value'))

    def __setCounter(self, alias, counter=None):
        if not self.__isTabPresent(alias):
            return
        self.__shownCounters.add(alias)
        counter = counter or i18n.makeString(MENU.HEADER_NOTIFICATIONSIGN)
        self.as_setButtonCounterS(alias, text_styles.counterLabelText(counter))

    def __hideCounter(self, alias):
        if alias in self.__shownCounters:
            self.__shownCounters.remove(alias)
            self.as_removeButtonCounterS(alias)

    @process
    def __doSelect(self, prebattleActionName):
        yield self.prbDispatcher.doSelectAction(PrbAction(prebattleActionName))

    def __onStatsReceived(self):
        clusterUsers, regionUsers, tooltipType = self.serverStats.getStats()
        if tooltipType == STATS_TYPE.UNAVAILABLE:
            tooltip = TOOLTIPS.HEADER_INFO_PLAYERS_UNAVAILABLE
            clusterUsers = regionUsers = ''
        elif tooltipType == STATS_TYPE.CLUSTER:
            tooltip = TOOLTIPS.HEADER_INFO_PLAYERS_ONLINE_REGION
        else:
            tooltip = TOOLTIPS.HEADER_INFO_PLAYERS_ONLINE_FULL
        clusterStats = makeHtmlString('html_templates:lobby', 'onlineCounter', {'key': self.connectionMgr.serverUserNameShort,
         'delimiter': backport.text(R.strings.common.common.colon()),
         'value': clusterUsers})
        if tooltipType == STATS_TYPE.FULL:
            regionStats = makeHtmlString('html_templates:lobby', 'onlineCounter', {'key': backport.text(R.strings.menu.onlineCounter.total()),
             'delimiter': backport.text(R.strings.common.common.colon()),
             'value': regionUsers})
        else:
            regionStats = ''
        body = i18n.makeString('{}/body'.format(tooltip), servername=self.connectionMgr.serverUserName)
        header = '{}/header'.format(tooltip)
        isAvailable = tooltipType != STATS_TYPE.UNAVAILABLE
        self.as_updateOnlineCounterS(clusterStats, regionStats, makeTooltip(header, body), isAvailable)

    def disableLobbyHeaderControls(self, disable):
        self._isLobbyHeaderControlsDisabled = disable
        self.as_disableFightButtonS(disable)
        for button in self.RANKED_WELCOME_VIEW_DISABLE_CONTROLS:
            self.as_doDisableHeaderButtonS(button, not disable)

        self.as_doDisableNavigationS()

    def __isTabPresent(self, tabID):
        if self.app is not None and self.app.tutorialManager is not None:
            override = self.app.tutorialManager.lastHangarMenuButtonsOverride
            if override is not None:
                return tabID in override
        return True

    def __isHeaderButtonPresent(self, buttonID):
        if self.app is not None and self.app.tutorialManager is not None:
            override = self.app.tutorialManager.lastHeaderMenuButtonsOverride
            if override is not None:
                return buttonID in override
        return True

    def __hideDisabledTabCounters(self):
        for tabID in self.__shownCounters.copy():
            if not self.__isTabPresent(tabID):
                self.__hideCounter(tabID)

    def __onAccountSettingsChanging(self, key, _):
        if key == RECRUIT_NOTIFICATIONS:
            self.__updateRecruitsTabCounter(self.TABS.BARRACKS)

    def __removeClanIconFromMemory(self):
        if self.__clanIconID is not None:
            self.removeTextureFromMemory(self.__clanIconID)
            self.__clanIconID = None
        return

    def _cleanupVisitedSettings(self):
        currentDynamicQuests = self.eventsCache.getDailyQuests(includeEpic=True).keys()
        questSettings = AccountSettings.getSettings(QUESTS)
        for visitedKey in ['visited', 'naVisited']:
            visitedQuestIds = questSettings[visitedKey]
            questSettings[visitedKey] = tuple((q for q in visitedQuestIds if not isDailyQuest(q) or q in currentDynamicQuests))
            AccountSettings.setSettings(QUESTS, questSettings)

    def __clearMenuVisibiliby(self):
        self.__menuVisibilityHelper.clear()
        self.__menuVisibilityHelper = None
        return


class _BoosterInfoPresenter(object):
    __MAX_BOOSTERS_TO_DISPLAY = 99

    def __init__(self, goodiesCache):
        self.__goodiesCache = goodiesCache
        self.__activeBoosters = goodiesCache.getBoosters(criteria=REQ_CRITERIA.BOOSTER.ACTIVE).values()
        self.__activeClanReserves = None
        return

    def hasActiveBoosters(self):
        return self.__hasActiveAccountBooster() or self.__hasActiveClanReserves()

    def hasAvailableBoosters(self):
        return self.__getAvailableBoostersCount() > 0

    def getIcon(self):
        if self.__hasActiveAccountBooster() and self.__getActiveClanReserves():
            return backport.image(R.images.gui.maps.icons.boosters.mixedBoosterIcon())
        elif self.__hasActiveAccountBooster():
            return backport.image(R.images.gui.maps.icons.boosters.activeBoosterIcon())
        elif self.__getActiveClanReserves():
            return backport.image(R.images.gui.maps.icons.boosters.clanBoosterIcon())
        else:
            return backport.image(R.images.gui.maps.icons.boosters.availableBoosterIcon()) if self.hasAvailableBoosters else None

    def getBg(self):
        if self.__getActiveClanReserves() and not self.__hasActiveAccountBooster():
            return backport.image(R.images.gui.maps.icons.boosters.clanBoosterBg())
        else:
            return backport.image(R.images.gui.maps.icons.boosters.activeBoosterBg()) if self.hasActiveBoosters() or self.hasAvailableBoosters() else None

    def getText(self):
        if not self.hasActiveBoosters() and not self.hasAvailableBoosters():
            return None
        else:
            templateKey = 'accountBooster'
            if self.hasActiveBoosters():
                if not self.__hasActiveAccountBooster():
                    templateKey = 'clanBooster'
                allBoosters = chain(self.__activeBoosters, self.__getActiveClanReserves())
                minUsageTime = min((booster.getUsageLeftTime() for booster in allBoosters)) or 0
                message = time_utils.getTillTimeString(minUsageTime, MENU.BOOSTERS_TIMELEFT, removeLeadingZeros=True)
            else:
                boostersAvailable = self.__getAvailableBoostersCount()
                if boostersAvailable <= self.__MAX_BOOSTERS_TO_DISPLAY:
                    message = str(boostersAvailable)
                else:
                    message = str(self.__MAX_BOOSTERS_TO_DISPLAY) + '+'
            return makeHtmlString('html_templates:lobby/header', templateKey, {'message': message})

    def __getAvailableBoostersCount(self):
        readyBoosters = self.__goodiesCache.getBoosters(criteria=REQ_CRITERIA.BOOSTER.IS_READY_TO_ACTIVATE).values()
        return sum((booster.count for booster in readyBoosters))

    def __hasActiveAccountBooster(self):
        return len(self.__activeBoosters) > 0

    def __getActiveClanReserves(self):
        if self.__activeClanReserves is None:
            self.__activeClanReserves = self.__goodiesCache.getClanReserves().values()
        return self.__activeClanReserves

    def __hasActiveClanReserves(self):
        return len(self.__getActiveClanReserves()) > 0
