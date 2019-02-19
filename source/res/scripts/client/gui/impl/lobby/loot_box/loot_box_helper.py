# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/impl/lobby/loot_box/loot_box_helper.py
import BigWorld
from gui import SystemMessages
from gui.Scaleform.locale.LOOTBOXES import LOOTBOXES
from gui.shared.notifications import NotificationPriorityLevel
from helpers.i18n import makeString as _ms
from optional_bonuses import BONUS_MERGERS

def getMergedLootBoxBonuses(bonusesList):
    result = {}
    for bonuses in bonusesList:
        for bonusName, bonusValue in bonuses.iteritems():
            BONUS_MERGERS[bonusName](result, bonusName, bonusValue, False, 1, None)

    return result


def showRestrictedSysMessage():

    def _showRestrictedSysMessage():
        SystemMessages.pushMessage(text=_ms(LOOTBOXES.RESTRICTEDMESSAGE_BODY), type=SystemMessages.SM_TYPE.ErrorHeader, priority=NotificationPriorityLevel.HIGH, messageData={'header': _ms(LOOTBOXES.RESTRICTEDMESSAGE_HEADER)})

    BigWorld.callback(0.0, _showRestrictedSysMessage)