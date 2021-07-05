# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ObstacleFromCSV
                                 A QGIS plugin
 Imports obstacle data from CSV
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Paweł Strzelewicz
        email                : pawel.strzelewicz@wp.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget, QMessageBox
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .obstacle_from_csv_dialog import ObstacleFromCSVDialog
import os.path
import csv
from .aviation_gis_tools.coordinate import *
from .obstacle_tools import *
from datetime import datetime


class ObstacleFromCSV:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.input_file_path = None
        self.output_file_path = None
        self.import_log_path = None
        self.csv_delimiter = None
        self.err_msg = ''
        self.field_assignment_controls = None
        self.obstacle_data = {
            'ctry_name': '',
            'obst_ident': '',
            'obst_name': '',
            'obst_type': '',
            'lon_src': '',
            'lat_src': '',
            'agl': '',
            'amsl': '',
            'vert_uom': ''
        }
        self.count_imported = 0

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ObstacleFromCSV_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&ObstacleFromCSV')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ObstacleFromCSV', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/obstacle_from_csv/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'ObstacleFromCSV'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&ObstacleFromCSV'),
                action)
            self.iface.removeToolBarIcon(action)

    def log(self, msg):
        with open('C:\GIS_test\obstacle_csv.txt', 'a') as f:
            f.write(str(msg) + '\n')

    def set_csv_delimiter(self):
        self.csv_delimiter = self.dlg.comboBoxCSVDelimiter.currentText()

    @staticmethod
    def get_output_fields():
        """ Create fields (attributes) for output layer.
        :return output_fields: QgsFields
        """
        output_fields = QgsFields()
        output_fields.append(QgsField("ctry_name", QVariant.String, len=150))
        output_fields.append(QgsField("obst_ident", QVariant.String, len=50))
        output_fields.append(QgsField("obst_name", QVariant.String, len=100))
        output_fields.append(QgsField("obst_type", QVariant.String, len=30))
        output_fields.append(QgsField("lon_src", QVariant.String, len=30))
        output_fields.append(QgsField("lat_src", QVariant.String, len=30))
        output_fields.append(QgsField("agl", QVariant.Double))
        output_fields.append(QgsField("amsl", QVariant.Double))
        output_fields.append(QgsField("vert_uom", QVariant.String, len=2))

        return output_fields

    def get_csv_fields(self):
        """ Get csv fields from input file.
        :return csv_fields: list
        """
        with open(self.input_file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter=self.csv_delimiter)
            csv_fields = reader.fieldnames
            return csv_fields

    def fill_field_assignment_controls(self, csv_fields):
        """ Fill in assignment controls with csv fields.
        :param csv_fields: list
        """
        for assignment_control_object in self.field_assignment_controls.values():
            assignment_control_object.addItems(csv_fields)

        # For some of the fields user can enter value that will be used for all records in given csv data files
        self.dlg.comboBoxCountryName.addItem("[Use value:]")
        self.dlg.comboBoxObstacleType.addItem("[Use value:]")
        self.dlg.comboBoxVerticalUOM.addItem("[Use value:]")
        # Obstacle name is optional - in case there is no in csv data file user can skip this field
        self.dlg.comboBoxObstacleName.addItem("[Skip]")

    def assign_default_csv_field_to_controls(self, output_fields):
        """ Set field assignment controls with default value: if there is csv field in input csv that name is
        the same as in attribute (field) in output file.
        :param output_fields: list, name of field in output file
        """
        for output_field in output_fields:
            assignment_control = self.field_assignment_controls[output_field]
            assignment_control.setCurrentText(output_field)

    def clear_assignment_controls(self):
        """ Remove items (csv input file fields) from assignment controls. """
        for assignment_control_object in self.field_assignment_controls.values():
            assignment_control_object.clear()

    def change_country_name_user_entry_state(self):
        """ Disable/enable country name input field if  item [Use value:] is selected or not in Country name assignment
        control. """
        items_count = self.dlg.comboBoxCountryName.count()
        if items_count > 0:
            if self.dlg.comboBoxCountryName.currentIndex() == items_count - 1:
                self.dlg.lineEditCountryNameByUser.setEnabled(True)
            else:
                self.dlg.lineEditCountryNameByUser.clear()
                self.dlg.lineEditCountryNameByUser.setEnabled(False)

    def change_obstacle_type_user_entry_state(self):
        """ Disable/enable obstacle type input field if  item [Use value:] is selected or not in
        Obstacle type assignment control. """
        items_count = self.dlg.comboBoxObstacleType.count()
        if items_count > 0:
            if self.dlg.comboBoxObstacleType.currentIndex() == items_count - 1:
                self.dlg.lineEditObstacleTypeByUser.setEnabled(True)
            else:
                self.dlg.lineEditObstacleTypeByUser.clear()
                self.dlg.lineEditObstacleTypeByUser.setEnabled(False)

    def change_vertical_uom_user_entry_state(self):
        """ Disable/enable Vertical UOM combobox with UOMs (ft, m)  if  item [Use value:] is selected or not in
        Vertical UOM obstacle assignment control. """
        items_count = self.dlg.comboBoxVerticalUOM.count()
        if items_count > 0:
            if self.dlg.comboBoxVerticalUOM.currentIndex() == items_count - 1:
                self.dlg.comboBoxCommonVerticalUOMByUser.setEnabled(True)
            else:
                self.dlg.comboBoxCommonVerticalUOMByUser.setCurrentIndex(0)
                self.dlg.comboBoxCommonVerticalUOMByUser.setEnabled(False)

    def disable_obstacle_attributes_by_user(self):
        """ Disable controls to enter obstacle attributes (such as country name, obstacle type) by user - not
        taken from input csv data file. """
        self.dlg.lineEditCountryNameByUser.clear()
        self.dlg.lineEditCountryNameByUser.setEnabled(False)
        self.dlg.lineEditObstacleTypeByUser.clear()
        self.dlg.lineEditObstacleTypeByUser.setEnabled(False)
        self.dlg.comboBoxCommonVerticalUOMByUser.setCurrentIndex(0)
        self.dlg.comboBoxCommonVerticalUOMByUser.setEnabled(False)

    def init_plugin(self):
        self.dlg.mQgsFileWidgetInputFile.lineEdit().clear()
        self.dlg.mQgsFileWidgetOutputFile.lineEdit().clear()
        self.dlg.checkBoxAddLayerToMap.setChecked(False)
        self.clear_assignment_controls()
        self.disable_obstacle_attributes_by_user()
        self.dlg.pushButtonImportLog.setText("")
        self.dlg.pushButtonImportLog.setEnabled(False)

    def reset_csv_fields_assignment(self):
        """ Read fields from CSV input file and fill drop-down lists with them if there are 3 or more
        fields in CSV file. """
        self.clear_assignment_controls()
        self.disable_obstacle_attributes_by_user()
        self.set_csv_delimiter()
        self.input_file_path = self.dlg.mQgsFileWidgetInputFile.filePath()

        if os.path.isfile(self.input_file_path):
            csv_fields = self.get_csv_fields()
            if len(csv_fields) >= 5:
                self.fill_field_assignment_controls(csv_fields)
                output_fields = self.get_output_fields()
                output_field_names = output_fields.names()
                self.assign_default_csv_field_to_controls(output_field_names)
            else:
                QMessageBox.critical(QWidget(), "Message", "At least 6 fields required!")

    def get_user_value_fields(self):
        """ Get fields that value is entered directly bus user not taken from input csv file - in case such data
        not exists in input csv file, example country name, vertical UOM is not given
        but is the same for all records. """
        user_value_fields = []

        if self.dlg.lineEditCountryNameByUser.isEnabled():
            user_value_fields.append("ctry_name")
        if self.dlg.lineEditObstacleTypeByUser.isEnabled():
            user_value_fields.append("obst_type")
        if self.dlg.comboBoxCommonVerticalUOMByUser.isEnabled():
            user_value_fields.append("vert_uom")

        return user_value_fields

    def assign_user_value_fields(self, user_value_fields):
        """ Assign values entered directly by user to obstacle_data record.
        :param user_value_fields: list, output fields that values are given by user not taken from csv file
        """
        for field in user_value_fields:
            if field == "ctry_name":
                self.obstacle_data["ctry_name"] = self.dlg.lineEditCountryNameByUser.text()
            if field == "obst_type":
                self.obstacle_data["obst_type"] = self.dlg.lineEditObstacleTypeByUser.text()
            if field == "vert_uom":
                self.obstacle_data["vert_uom"] = self.dlg.comboBoxCommonVerticalUOMByUser.currentText()

    def get_fields_to_skip(self):
        """ Get fields that are not mandatory  in case input csv file not contain data related to those fields. """
        # For possible future development this is in separate method - possible additional fields such lighting, marking
        # source information, accuracy - are not always published in csv files.
        items_count = self.dlg.comboBoxObstacleName.count()
        if self.dlg.comboBoxObstacleName.currentIndex() == items_count - 1:
            return ["obst_name"]

    def map_csv_fields(self, exclude_fields):
        """ Create dictionary that is a map between output field and input csv file field,
        key - field name in output file
        value - corresponding field name in input csv file
        :param exclude_fields: list, output fields that values are given by user not taken from csv file or are not
        mandatory and not given in csv file (selected as [Skip] in assignment control combobox)
        :return map_field_output_csv: dict
        """
        map_field_output_csv = {}
        for assignment_control_name, assignment_control_object in self.field_assignment_controls.items():
            if assignment_control_name not in exclude_fields:
                map_field_output_csv[assignment_control_name] = assignment_control_object.currentText()
        return map_field_output_csv

    def get_source_data_from_csv_row(self, row, field_map):
        """ Read row of input csv file based on the given relation between output fields and csv fields.
        :param row: dict, row of csv file returned by csv.Reader
        :param field_map: dict, map between output fields and csv fields
        """
        for layer_field, csv_field in field_map.items():
            self.obstacle_data[layer_field] = row[csv_field]

    def check_input_data(self, user_value_fields):
        """ Check if:
             - input file is selected
             - input file has CSV fields (if selected CSV delimiter is correct)
             - output file is selected
        """
        self.err_msg = ''
        is_input_ok = True
        self.output_file_path = self.dlg.mQgsFileWidgetOutputFile.filePath()

        if os.path.isfile(self.input_file_path):
            csv_fields = self.get_csv_fields()
            if len(csv_fields) < 5:
                # At least required data taken from csv file:
                # obst_ident, lon_scr, lat_src, agl, amsl
                is_input_ok = False
                self.err_msg += "Not enough fields in input file! Hint: check field delimiter.\n"
        else:
            is_input_ok = False
            self.err_msg += "Input file is required!\n"

        if not self.output_file_path:
            is_input_ok = False
            self.err_msg += "Output file is required!\n"

        if user_value_fields:
            for field in user_value_fields:
                if field == "ctry_name":
                    if self.dlg.lineEditCountryNameByUser.text().strip() == "":
                        is_input_ok = False
                        self.err_msg += "Country name is required!\n"
                if field == "obst_type":
                    if self.dlg.lineEditObstacleTypeByUser.text().strip() == "":
                        is_input_ok = False
                        self.err_msg += "Obstacle type is required!\n"
                if field == "vert_uom":
                    if self.dlg.comboBoxCommonVerticalUOMByUser.currentIndex() == 0:
                        is_input_ok = False
                        self.err_msg += "Select vertical UOM!\n"

        return is_input_ok

    def add_obstacle(self, feature, attributes, obstacle_data, provider):
        """ Add obstacle feature to layer.
        :param feature: QqsFeature
        :param attributes:
        :param obstacle_data: dict
        :param provider: QgsDataProvider
        """
        for attribute in attributes:
            feature[attribute] = obstacle_data[attribute]

            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(obstacle_data["lon_dd"],
                                                                   obstacle_data["lat_dd"])))

        provider.addFeatures([feature])
        self.count_imported += 1

    def set_import_log_path(self):
        """ Return full path to import log file - contains errors and not imported records from CSV file, example if
        there is incorrect or not supported coordinate format.
        """
        directory = os.path.dirname(self.input_file_path)
        input_file_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        self.import_log_path = os.path.join(directory, "{}_import.log".format(input_file_name))

    def open_import_log(self):
        os.startfile(self.import_log_path)

    def get_no_mapping_fields(self, user_value_fields):
        fields_to_skip = self.get_fields_to_skip()
        if fields_to_skip:
            return user_value_fields + fields_to_skip
        else:
            return user_value_fields

    def import_obstacle_from_csv_file(self):
        user_value_fields = self.get_user_value_fields()

        if self.check_input_data(user_value_fields):
            self.count_imported = 0
            self.set_import_log_path()

            # Create output shapefile
            output_fields = self.get_output_fields()
            writer = QgsVectorFileWriter(self.output_file_path, 'UTF-8', output_fields, QgsWkbTypes.Point,
                                         QgsCoordinateReferenceSystem('EPSG:4326'), 'ESRI Shapefile')
            del writer

            # Map output layer fields with csv fields, before get 'not to map fields': values entered by user,
            # not mandatory fields to skip if data is missing in csv file
            exclude_fields = self.get_no_mapping_fields(user_value_fields)
            field_map = self.map_csv_fields(exclude_fields)

            # Create output layer, data provider for adding features to layer
            layer_name = os.path.splitext(os.path.basename(self.output_file_path))[0]
            layer = QgsVectorLayer(self.output_file_path, layer_name, 'ogr')
            provider = layer.dataProvider()
            feature = QgsFeature(layer.fields())
            # self.assign_default_csv_field_to_controls(exclude_fields)
            self.assign_user_value_fields(user_value_fields)
            field_names = output_fields.names()
            obst = Obstacle()

            with open(self.input_file_path, 'r') as f:
                reader = csv.DictReader(f, delimiter=self.csv_delimiter)
                for row in reader:
                    self.get_source_data_from_csv_row(row, field_map)
                    parsing_error, parsed_data = obst.parse_obstacle_data(self.obstacle_data)
                    if parsing_error:
                        with open(self.import_log_path, 'a') as log:
                            log.write("{} | Line skipped. "
                                      "Input data error: {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                                                                      parsing_error))
                    else:
                        self.add_obstacle(feature, field_names, parsed_data, provider)

            if self.dlg.checkBoxAddLayerToMap.isChecked():
                QgsProject.instance().addMapLayer(layer)
            self.dlg.pushButtonImportLog.setEnabled(True)
            self.dlg.pushButtonImportLog.setText(self.import_log_path)
            QMessageBox.information(QWidget(), "Message", "Import completed.\n"
                                    "Imported: {}".format(self.count_imported))

        else:
            QMessageBox.critical(QWidget(), "Message", self.err_msg)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ObstacleFromCSVDialog()

            self.field_assignment_controls = {
                'ctry_name': self.dlg.comboBoxCountryName,
                'obst_ident': self.dlg.comboBoxObstacleIdent,
                'obst_name': self.dlg.comboBoxObstacleName,
                'obst_type': self.dlg.comboBoxObstacleType,
                'lon_src': self.dlg.comboBoxSourceLongitude,
                'lat_src': self.dlg.comboBoxSourceLatitude,
                'agl': self.dlg.comboBoxAgl,
                'amsl': self.dlg.comboBoxAmsl,
                'vert_uom': self.dlg.comboBoxVerticalUOM
             }

            self.dlg.mQgsFileWidgetInputFile.setFilter('*.csv')
            self.dlg.mQgsFileWidgetOutputFile.setFilter('*.shp')
            self.dlg.mQgsFileWidgetInputFile.fileChanged.connect(self.reset_csv_fields_assignment)
            self.dlg.comboBoxCSVDelimiter.currentIndexChanged.connect(self.reset_csv_fields_assignment)
            self.dlg.comboBoxCountryName.currentIndexChanged.connect(self.change_country_name_user_entry_state)
            self.dlg.comboBoxObstacleType.currentIndexChanged.connect(self.change_obstacle_type_user_entry_state)
            self.dlg.comboBoxVerticalUOM.currentIndexChanged.connect(self.change_vertical_uom_user_entry_state)
            self.dlg.pushButtonImport.clicked.connect(self.import_obstacle_from_csv_file)
            self.dlg.pushButtonImportLog.clicked.connect(self.open_import_log)

        # show the dialog
        self.dlg.show()
        self.init_plugin()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
