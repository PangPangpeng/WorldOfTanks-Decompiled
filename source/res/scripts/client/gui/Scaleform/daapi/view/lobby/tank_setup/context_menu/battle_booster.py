# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/daapi/view/lobby/tank_setup/context_menu/battle_booster.py
from adisp import process, async
from gui import shop
from gui.Scaleform.daapi.settings.views import VIEW_ALIAS
from gui.Scaleform.daapi.view.lobby.shared.cm_handlers import CMLabel, option
from gui.Scaleform.daapi.view.lobby.tank_setup.context_menu.base import BaseItemContextMenu, BaseSlotContextMenu, TankSetupCMLabel
from gui.Scaleform.daapi.view.lobby.tank_setup.context_menu.base_equipment import BaseHangarEquipmentSlotContextMenu
from gui.impl.gen.view_models.views.lobby.tank_setup.sub_views.base_setup_model import BaseSetupModel
from gui.impl.gen.view_models.views.lobby.tank_setup.tank_setup_constants import TankSetupConstants
from gui.shared.gui_items.items_actions import factory as ActionsFactory
from ids_generators import SequenceIDGenerator

class BattleBoosterItemContextMenu(BaseItemContextMenu):
    __sqGen = SequenceIDGenerator()

    @option(__sqGen.next(), TankSetupCMLabel.SELECT)
    def select(self):
        self._sendSlotAction(BaseSetupModel.SELECT_SLOT_ACTION)

    @option(__sqGen.next(), CMLabel.BUY_MORE)
    def buyMore(self):
        shop.showBattleBoosterOverlay(itemId=self._intCD, source=shop.Source.EXTERNAL, origin=shop.Origin.BATTLE_BOOSTERS, alias=VIEW_ALIAS.BROWSER_LOBBY_TOP_SUB)


class BattleBoosterSlotContextMenu(BaseSlotContextMenu):
    __sqGen = SequenceIDGenerator()

    @option(__sqGen.next(), CMLabel.BUY_MORE)
    def buyMore(self):
        shop.showBattleBoosterOverlay(itemId=self._intCD, source=shop.Source.EXTERNAL, origin=shop.Origin.BATTLE_BOOSTERS, alias=VIEW_ALIAS.BROWSER_LOBBY_TOP_SUB)

    @option(__sqGen.next(), TankSetupCMLabel.UNLOAD)
    def unload(self):
        self._sendSlotAction(BaseSetupModel.SELECT_SLOT_ACTION, intCD=None, currentSlotId=self._installedSlotId)
        return

    @option(__sqGen.next(), TankSetupCMLabel.TAKE_OFF)
    def takeOff(self):
        self._sendSlotAction(BaseSetupModel.REVERT_SLOT_ACTION)


class HangarBattleBoosterSlotContextMenu(BaseHangarEquipmentSlotContextMenu):
    _sqGen = SequenceIDGenerator(BaseHangarEquipmentSlotContextMenu._sqGen.currSequenceID)

    @option(_sqGen.next(), CMLabel.BUY_MORE)
    def buyMore(self):
        shop.showBattleBoosterOverlay(itemId=self._intCD, source=shop.Source.EXTERNAL, origin=shop.Origin.BATTLE_BOOSTERS, alias=VIEW_ALIAS.BROWSER_LOBBY_TOP_SUB)

    @option(_sqGen.next(), TankSetupCMLabel.UNLOAD)
    @process
    def unload(self):
        copyVehicle = self._getCopyVehicle()
        copyVehicle.battleBoosters.layout[self._installedSlotId] = None
        result = yield self._doPutOnAction(copyVehicle)
        if result:
            self._sendLastSlotAction(TankSetupConstants.BATTLE_BOOSTERS, BaseSetupModel.REVERT_SLOT_ACTION, {'slotID': self._installedSlotId})
        return

    def _isVisible(self, label):
        return False if label == CMLabel.INFORMATION else super(HangarBattleBoosterSlotContextMenu, self)._isVisible(label)

    @async
    @process
    def _doPutOnAction(self, vehicle, callback):
        action = ActionsFactory.getAction(ActionsFactory.BUY_AND_INSTALL_BATTLE_BOOSTERS, vehicle, confirmOnlyExchange=True)
        result = yield ActionsFactory.asyncDoAction(action)
        callback(result)
