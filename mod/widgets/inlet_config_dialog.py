#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""DesignSPHysics Inlet/Oulet Configuration Dialog """

from uuid import UUID
from PySide import QtCore, QtGui

from mod.translation_tools import __
from mod.freecad_tools import get_fc_main_window
from mod.stdout_tools import debug

from mod.enums import InletOutletDetermLimit

from mod.widgets.inlet_zone_edit import InletZoneEdit

from mod.dataobjects.case import Case
from mod.dataobjects.inletoutlet.inlet_outlet_config import InletOutletConfig
from mod.dataobjects.inletoutlet.inlet_outlet_zone import InletOutletZone


class InletZoneWidget(QtGui.QWidget):
    """ A widget representing a zone to embed in the zones table. """

    on_edit = QtCore.Signal(UUID)
    on_delete = QtCore.Signal(InletOutletZone)

    def __init__(self, index, io_object):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel(__("Inlet/Outlet Zone {}").format(str(index + 1)))
        self.edit_button = QtGui.QPushButton(__("Edit"))
        self.delete_button = QtGui.QPushButton(__("Delete"))

        self.edit_button.clicked.connect(lambda _=False, i=io_object.id: self.on_edit.emit(i))
        self.delete_button.clicked.connect(lambda _=False, obj=io_object: self.on_delete.emit(obj))

        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.edit_button)
        self.layout.addWidget(self.delete_button)
        self.setLayout(self.layout)


class InletConfigDialog(QtGui.QDialog):
    """ Defines the Inlet/Outlet dialog window.
       Modifies data dictionary passed as parameter. """

    MINIMUM_WIDTH = 570
    MINIMUM_HEIGHT = 630
    MINIMUM_TABLE_SECTION_HEIGHT = 64

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Reference to the inlet outlet configuration on the case data
        self.inlet_outlet: InletOutletConfig = Case.the().inlet_outlet

        # Creates a dialog
        self.setWindowTitle("Inlet/Outlet configuration")
        self.setModal(False)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setMinimumHeight(self.MINIMUM_HEIGHT)
        self.main_layout = QtGui.QVBoxLayout()

        # Creates layout for content first options
        self.io_options_layout = QtGui.QHBoxLayout()

        # Creates resizetime option
        self.resizetime_layout = QtGui.QHBoxLayout()
        self.resizetime_option = QtGui.QLabel(__("Resizetime: "))
        self.resizetime_line_edit = QtGui.QLineEdit(str(self.inlet_outlet.resizetime))

        self.resizetime_layout.addWidget(self.resizetime_option)
        self.resizetime_layout.addWidget(self.resizetime_line_edit)

        # Creates extrapolate mode selector
        self.extrapolatemode_layout = QtGui.QHBoxLayout()
        self.extrapolatemode_option = QtGui.QLabel(__("Extrapolate mode: "))
        self.extrapolatemode_combobox = QtGui.QComboBox()
        self.extrapolatemode_combobox.insertItems(0, [__("Fast-Single"), __("Single"), __("Double")])
        self.extrapolatemode_combobox.setCurrentIndex(self.inlet_outlet.extrapolatemode - 1)

        self.extrapolatemode_layout.addWidget(self.extrapolatemode_option)
        self.extrapolatemode_layout.addWidget(self.extrapolatemode_combobox)

        # Creates use determlimit option
        self.determlimit_layout = QtGui.QHBoxLayout()
        self.determlimit_option = QtGui.QLabel(__("Determlimit: "))
        self.determlimit_combobox = QtGui.QComboBox()
        self.determlimit_combobox.insertItems(0, [__("1e+3"), __("1e-3")])
        self.determlimit_combobox.setCurrentIndex(0 if self.inlet_outlet.determlimit == InletOutletDetermLimit.ZEROTH_ORDER else 1)

        self.determlimit_layout.addWidget(self.determlimit_option)
        self.determlimit_layout.addWidget(self.determlimit_combobox)

        # Creates 2 main buttons
        self.finish_button = QtGui.QPushButton(__("Close"))
        self.button_layout = QtGui.QHBoxLayout()

        self.finish_button.clicked.connect(self.on_finish)

        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.finish_button)

        # Create the list for zones
        self.zones_groupbox = QtGui.QGroupBox(__("Inlet/Outlet zones"))
        self.zones_groupbox_layout = QtGui.QVBoxLayout()
        self.io_zones_table = QtGui.QTableWidget()
        self.io_zones_table.setColumnCount(1)
        self.io_zones_table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.io_zones_table.verticalHeader().setDefaultSectionSize(self.MINIMUM_TABLE_SECTION_HEIGHT)
        self.io_zones_table.horizontalHeader().setVisible(False)
        self.io_zones_table.verticalHeader().setVisible(False)

        # Add button
        self.add_button_layout = QtGui.QHBoxLayout()
        self.add_zone_button = QtGui.QPushButton(__("Add a new zone..."))
        self.add_button_layout.addStretch(1)
        self.add_button_layout.addWidget(self.add_zone_button)
        self.add_zone_button.clicked.connect(self.on_add_zone)

        self.zones_groupbox_layout.addLayout(self.add_button_layout)
        self.zones_groupbox_layout.addWidget(self.io_zones_table)

        self.zones_groupbox.setLayout(self.zones_groupbox_layout)

        # Adds options to option layout
        self.io_options_layout.addLayout(self.resizetime_layout)
        self.io_options_layout.addLayout(self.extrapolatemode_layout)
        self.io_options_layout.addLayout(self.determlimit_layout)

        # Adds options to main
        self.main_layout.addLayout(self.io_options_layout)
        self.main_layout.addWidget(self.zones_groupbox)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)

        self.refresh_zones()

        self.finish_button.setFocus()

        self.exec_()

    def on_add_zone(self):
        """ Adds Inlet/Outlet zone """
        new_io_zone = InletOutletZone()
        self.inlet_outlet.zones.append(new_io_zone)
        self.refresh_zones()
        self.zone_edit(new_io_zone.id)

    def refresh_zones(self):
        """ Refreshes the zones list """
        self.io_zones_table.clear()
        self.io_zones_table.setRowCount(len(self.inlet_outlet.zones))

        count = 0
        for io_object in self.inlet_outlet.zones:
            io_zone_widget = InletZoneWidget(count, io_object)
            io_zone_widget.on_edit.connect(self.zone_edit)
            io_zone_widget.on_delete.connect(self.zone_delete)
            self.io_zones_table.setCellWidget(count, 0, io_zone_widget)
            count += 1

    def zone_delete(self, io):
        """ Delete one zone from the list """
        self.inlet_outlet.zones.remove(io)
        self.refresh_zones()

    def zone_edit(self, io_id):
        """ Calls a window for edit zones """
        debug("Trying to open a zone edit for zone UUID {}".format(io_id))
        InletZoneEdit(io_id, parent=get_fc_main_window())
        self.refresh_zones()

    def on_cancel(self):
        """ Cancels the dialog not saving anything. """
        self.reject()

    def on_finish(self):
        """ Save data """

        if not self.inlet_outlet:
            self.inlet_outlet = InletOutletConfig

        self.inlet_outlet.resizetime = float(self.resizetime_line_edit.text())
        self.inlet_outlet.determlimit = self.determlimit_combobox.currentText()
        self.inlet_outlet.extrapolatemode = self.extrapolatemode_combobox.currentIndex() + 1
        InletConfigDialog.accept(self)
