# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/locale/EVENT.py
from debug_utils import LOG_WARNING

class EVENT(object):
    PUNISHMENTWINDOW_REASON_EVENT_DESERTER = '#event:punishmentWindow/reason/event_deserter'
    PUNISHMENTWINDOW_REASON_EVENT_AFK = '#event:punishmentWindow/reason/event_afk'
    ALL_ENUM = (PUNISHMENTWINDOW_REASON_EVENT_DESERTER, PUNISHMENTWINDOW_REASON_EVENT_AFK)

    @classmethod
    def all(cls, key0):
        outcome = '#event:{}'.format(key0)
        if outcome not in cls.ALL_ENUM:
            LOG_WARNING('Localization key "{}" not found'.format(outcome))
            return None
        else:
            return outcome
