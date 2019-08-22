# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/web_client_api/battle_royale/__init__.py
from web_client_api import webApiCollection
from web_client_api.request import RequestWebApi
from web_client_api.sound import SoundWebApi, HangarSoundWebApi
from web_client_api.ui import NotificationWebApi, OpenWindowWebApi, CloseViewWebApi

def createBattleRoyaleWebHanlders():
    return webApiCollection(NotificationWebApi, RequestWebApi, OpenWindowWebApi, CloseViewWebApi, SoundWebApi, HangarSoundWebApi)
