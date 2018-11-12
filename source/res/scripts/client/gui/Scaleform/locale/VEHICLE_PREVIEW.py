# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/Scaleform/locale/VEHICLE_PREVIEW.py
from debug_utils import LOG_WARNING

class VEHICLE_PREVIEW(object):
    HEADER_BACKBTN_LABEL = '#vehicle_preview:header/backBtn/label'
    HEADER_BACKBTN_DESCRLABEL_RESEARCHTREE = '#vehicle_preview:header/backBtn/descrLabel/researchTree'
    HEADER_BACKBTN_DESCRLABEL_PERSONALAWARDS = '#vehicle_preview:header/backBtn/descrLabel/personalAwards'
    HEADER_BACKBTN_DESCRLABEL_SHOP = '#vehicle_preview:header/backBtn/descrLabel/shop'
    HEADER_BACKBTN_DESCRLABEL_STORAGE = '#vehicle_preview:header/backBtn/descrLabel/storage'
    HEADER_BACKBTN_DESCRLABEL_HANGAR = '#vehicle_preview:header/backBtn/descrLabel/hangar'
    HEADER_BACKBTN_DESCRLABEL_VEHICLECOMPARE = '#vehicle_preview:header/backBtn/descrLabel/vehicleCompare'
    HEADER_TITLE = '#vehicle_preview:header/title'
    HERO_HEADER_TITLE = '#vehicle_preview:hero/header/title'
    HEADER_CLOSEBTN_LABEL = '#vehicle_preview:header/closeBtn/label'
    BUYINGPANEL_LABEL = '#vehicle_preview:buyingPanel/Label'
    BUYINGPANEL_ALERTLABEL = '#vehicle_preview:buyingPanel/alertLabel'
    BUYINGPANEL_UNIQUEVEHICLELABEL = '#vehicle_preview:buyingPanel/uniqueVehicleLabel'
    BUYINGPANEL_TRADEINLABEL = '#vehicle_preview:buyingPanel/tradeInLabel'
    MODULESPANEL_TITLE = '#vehicle_preview:modulesPanel/title'
    MODULESPANEL_LABEL = '#vehicle_preview:modulesPanel/Label'
    MODULESPANEL_NOMODULESOPTIONS = '#vehicle_preview:modulesPanel/noModulesOptions'
    MODULESPANEL_STATUS_TEXT = '#vehicle_preview:modulesPanel/status/text'
    BUYINGPANEL_BUYBTN_LABEL_BUY = '#vehicle_preview:buyingPanel/buyBtn/label/buy'
    BUYINGPANEL_BUYBTN_LABEL_BUYITEMPACK = '#vehicle_preview:buyingPanel/buyBtn/label/buyItemPack'
    BUYINGPANEL_BUYBTN_LABEL_RESTORE = '#vehicle_preview:buyingPanel/buyBtn/label/restore'
    BUYINGPANEL_BUYBTN_LABEL_RESEARCH = '#vehicle_preview:buyingPanel/buyBtn/label/research'
    BUYINGPANEL_NOTRESEARCHEDVEHICLEWARNING = '#vehicle_preview:buyingPanel/notResearchedVehicleWarning'
    BUYINGPANEL_COMPENSATION_BODY = '#vehicle_preview:buyingPanel/compensation/body'
    INFOPANEL_TAB_CREWINFO_NAME = '#vehicle_preview:infoPanel/tab/crewInfo/name'
    INFOPANEL_TAB_FACTSHEET_NAME = '#vehicle_preview:infoPanel/tab/factSheet/name'
    INFOPANEL_TAB_BROWSE_NAME = '#vehicle_preview:infoPanel/tab/browse/name'
    INFOPANEL_TAB_MODULES_NAME = '#vehicle_preview:infoPanel/tab/modules/name'
    INFOPANEL_TAB_CREWINFO_LISTDESC_TEXT = '#vehicle_preview:infoPanel/tab/crewInfo/listDesc/text'
    INFOPANEL_TAB_ELITEFACTSHEET_TITLE = '#vehicle_preview:infoPanel/tab/eliteFactSheet/title'
    INFOPANEL_TAB_ELITEFACTSHEET_INFO = '#vehicle_preview:infoPanel/tab/eliteFactSheet/info'
    INFOPANEL_LEVEL = '#vehicle_preview:infoPanel/level'
    INFOPANEL_PREMIUM_FREEEXPMULTIPLIER = '#vehicle_preview:infoPanel/premium/freeExpMultiplier'
    INFOPANEL_PREMIUM_FREEEXPTEXT = '#vehicle_preview:infoPanel/premium/freeExpText'
    INFOPANEL_PREMIUM_CREDITSMULTIPLIER = '#vehicle_preview:infoPanel/premium/creditsMultiplier'
    INFOPANEL_PREMIUM_CREDITSTEXT = '#vehicle_preview:infoPanel/premium/creditsText'
    INFOPANEL_PREMIUM_CREWTRANSFERTITLE = '#vehicle_preview:infoPanel/premium/crewTransferTitle'
    INFOPANEL_PREMIUM_CREWTRANSFERTEXT = '#vehicle_preview:infoPanel/premium/crewTransferText'
    HEADER_BACKBTN_DESCRLABEL_ENUM = (HEADER_BACKBTN_DESCRLABEL_RESEARCHTREE,
     HEADER_BACKBTN_DESCRLABEL_PERSONALAWARDS,
     HEADER_BACKBTN_DESCRLABEL_SHOP,
     HEADER_BACKBTN_DESCRLABEL_STORAGE,
     HEADER_BACKBTN_DESCRLABEL_HANGAR,
     HEADER_BACKBTN_DESCRLABEL_VEHICLECOMPARE)

    @classmethod
    def getBackBtnLabel(cls, key):
        outcome = '#vehicle_preview:header/backBtn/descrLabel/{}'.format(key)
        if outcome not in cls.HEADER_BACKBTN_DESCRLABEL_ENUM:
            LOG_WARNING('Localization key "{}" not found'.format(outcome))
            return None
        else:
            return outcome
