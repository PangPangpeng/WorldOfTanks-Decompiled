# Python bytecode 2.7 (decompiled from Python 2.7)
# Embedded file name: scripts/client/gui/impl/gen/view_models/views/battle_royale/br_vehicle_specifications_model.py
from gui.impl.gen import R
from frameworks.wulf import ViewModel

class BrVehicleSpecificationsModel(ViewModel):
    __slots__ = ()

    def getSpecName(self):
        return self._getString(0)

    def setSpecName(self, value):
        self._setString(0, value)

    def getIconSource(self):
        return self._getResource(1)

    def setIconSource(self, value):
        self._setResource(1, value)

    def _initialize(self):
        super(BrVehicleSpecificationsModel, self)._initialize()
        self._addStringProperty('specName', '')
        self._addResourceProperty('iconSource', R.invalid())
