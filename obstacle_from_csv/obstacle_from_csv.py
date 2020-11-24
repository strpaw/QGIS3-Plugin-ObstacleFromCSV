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


class ObstacleFromCSV:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.count = None
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

    @staticmethod
    def get_obstacle_fields():
        """ Create fields for output layer. """
        attributes = [
            QgsField("ctry_name", QVariant.String, len=150),
            QgsField("obst_ident", QVariant.String, len=50),
            QgsField("obst_name", QVariant.String, len=100),
            QgsField("lon_src", QVariant.String, len=30),
            QgsField("lat_src", QVariant.String, len=30),
            QgsField("agl", QVariant.Double),
            QgsField("amsl", QVariant.Double),
            QgsField("vert_uom", QVariant.String, len=2),
            QgsField("obst_type", QVariant.String, len=30)
        ]

        fields = QgsFields()
        for attribute in attributes:
            fields.append(attribute)
        return fields

    @staticmethod
    def get_missing_csv_fields(layer_fields, csv_fields):
        """ Check if source data CSV fields are the same as in output layer.
        Return list of 'missing' fields.
        :param layer_fields: list, field names in output layer
        :param csv_fields: list, field names from input CSV file
        :return missing_fields: list, fields that are in output layer but not in CSV file
        """
        if sorted(layer_fields) == sorted(csv_fields):
            return
        else:
            missing_fields = []
            for layer_field in layer_fields:
                if layer_field not in csv_fields:
                    missing_fields.append(layer_field)
            return missing_fields

    def add_obstacle(self, feature, attributes, src_data, provider):
        """ Add obstacle feature to layer.
        """
        check_msg, parsed_data = Obstacle.parse_obstacle_data(src_data)
        if check_msg:
            QMessageBox.critical(QWidget(), "Message", "Input data error:\n"
                                                       "{}".format(check_msg))
        else:
            # Assign attribute data
            for attribute in attributes:
                feature[attribute] = parsed_data[attribute]

            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(parsed_data["lon_dd"],
                                                                   parsed_data["lat_dd"])))

            provider.addFeatures([feature])
            self.count += 1

    def import_obstacle_from_csv_file(self):
        """ Import obstacle from CSV file into shapefile. """
        msg = ''
        self.count = 0
        input_file = self.dlg.mQgsFileWidgetInputFile.filePath()
        output_file = self.dlg.mQgsFileWidgetOutputFile.filePath()

        if not input_file:
            msg += "Input file is required!\n"

        if not output_file:
            msg += "Output file is required!"

        if input_file and output_file:
            obstacle_fields = self.get_obstacle_fields()

            writer = QgsVectorFileWriter(output_file, 'UTF-8', obstacle_fields, QgsWkbTypes.Point,
                                         QgsCoordinateReferenceSystem('EPSG:4326'), 'ESRI Shapefile')
            del writer

            layer_name = os.path.splitext(os.path.basename(output_file))[0]

            layer = QgsVectorLayer(output_file, layer_name, 'ogr')
            provider = layer.dataProvider()

            feature = QgsFeature(layer.fields())

            with open(input_file, 'r') as f:
                delimiter = self.dlg.comboBoxCSVDelimiter.currentText()
                reader = csv.DictReader(f, delimiter=delimiter)
                header = reader.fieldnames
                field_names = obstacle_fields.names()

                missing_fields = self.get_missing_csv_fields(field_names, header)

                if not missing_fields:
                    self.dlg.labelCtryName.setEnabled(False)
                    self.dlg.lineEditCountryName.clear()
                    self.dlg.lineEditCountryName.setEnabled(False)
                    self.dlg.labelVertUOM.setEnabled(False)
                    self.dlg.comboBoxVerticalUOM.setCurrentIndex(0)
                    self.dlg.comboBoxVerticalUOM.setEnabled(False)
                    # Fields in input CSV file are the same as in output layer
                    for row in reader:
                        self.add_obstacle(feature, field_names, row, provider)
                    layer.commitChanges()
                    if self.dlg.checkBoxAddLayerToMap.isChecked():
                        QgsProject.instance().addMapLayer(layer)
                    QMessageBox.information(QWidget(), "Message", "Import completed.\n"
                                                                  "Imported: {}".format(self.count))
                elif missing_fields == ["ctry_name", "vert_uom"]:
                    self.dlg.labelCtryName.setEnabled(True)
                    self.dlg.lineEditCountryName.setEnabled(True)
                    self.dlg.labelVertUOM.setEnabled(True)
                    self.dlg.comboBoxVerticalUOM.setEnabled(True)
                    all_ctry_name = self.dlg.lineEditCountryName.text().strip()
                    all_vert_uom = self.dlg.comboBoxVerticalUOM.currentText()
                    if all_ctry_name and all_vert_uom in ['ft', 'm']:
                        for row in reader:
                            # Check input data
                            row["ctry_name"] = all_ctry_name
                            row["vert_uom"] = all_vert_uom
                            self.add_obstacle(feature, field_names, row, provider)
                        layer.commitChanges()
                        if self.dlg.checkBoxAddLayerToMap.isChecked():
                            QgsProject.instance().addMapLayer(layer)
                        QMessageBox.information(QWidget(), "Message", "Import completed.\n"
                                                                      "Imported: {}".format(self.count))

                    else:
                        QMessageBox.information(QWidget(), "Message", "Missing fields in CSV file:\n"
                                                                      "{}.\n"
                                                                      "Assign country name and vertical UOM"
                                                                      " for all imported data.".format(missing_fields))
                elif missing_fields == ["ctry_name"]:
                    self.dlg.labelCtryName.setEnabled(True)
                    self.dlg.lineEditCountryName.setEnabled(True)
                    self.dlg.labelVertUOM.setEnabled(False)
                    self.dlg.comboBoxVerticalUOM.setCurrentIndex(0)
                    self.dlg.comboBoxVerticalUOM.setEnabled(False)
                    all_ctry_name = self.dlg.lineEditCountryName.text().strip()
                    if all_ctry_name:
                        for row in reader:
                            # Check input data
                            row["ctry_name"] = all_ctry_name
                            self.add_obstacle(feature, field_names, row, provider)
                        layer.commitChanges()
                        if self.dlg.checkBoxAddLayerToMap.isChecked():
                            QgsProject.instance().addMapLayer(layer)
                        QMessageBox.information(QWidget(), "Message", "Import completed.\n"
                                                                      "Imported: {}".format(self.count))
                    else:
                        QMessageBox.information(QWidget(), "Message", "Missing fields in CSV file:\n"
                                                                      "{}.\n"
                                                                      "Assign country name "
                                                                      "for all imported data.".format(missing_fields))
                elif missing_fields == ["vert_uom"]:
                    self.dlg.labelVertUOM.setEnabled(True)
                    self.dlg.comboBoxVerticalUOM.setEnabled(True)
                    self.dlg.lineEditCountryName.clear()
                    self.dlg.lineEditCountryName.setEnabled(False)
                    all_vert_uom = self.dlg.comboBoxVerticalUOM.currentText()
                    if all_vert_uom in ['ft', 'm']:
                        for row in reader:
                            row["vert_uom"] = all_vert_uom
                            self.add_obstacle(feature, field_names, row, provider)
                        layer.commitChanges()
                        if self.dlg.checkBoxAddLayerToMap.isChecked():
                            QgsProject.instance().addMapLayer(layer)
                        QMessageBox.information(QWidget(), "Message", "Import completed.\n"
                                                                      "Imported: {}".format(self.count))
                    else:
                        QMessageBox.information(QWidget(), "Message", "Missing fields in CSV file:\n"
                                                                      "{}.\n"
                                                                      "Assign vertical UOM "
                                                                      "for all imported data.".format(missing_fields))
                else:
                    self.dlg.labelCtryName.setEnabled(False)
                    self.dlg.lineEditCountryName.clear()
                    self.dlg.lineEditCountryName.setEnabled(False)
                    self.dlg.labelVertUOM.setEnabled(False)
                    self.dlg.comboBoxVerticalUOM.setCurrentIndex(0)
                    self.dlg.comboBoxVerticalUOM.setEnabled(False)
                    QMessageBox.information(QWidget(), "Message", "Missing fields in CSV file:\n"
                                                                  "{}.\n".format(missing_fields))

        else:
            QMessageBox.critical(QWidget(), "Message", msg)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ObstacleFromCSVDialog()
            self.dlg.mQgsFileWidgetInputFile.setFilter('*.csv')
            self.dlg.mQgsFileWidgetOutputFile.setFilter('*.shp')
            self.dlg.pushButtonImport.clicked.connect(self.import_obstacle_from_csv_file)

        # show the dialog
        self.dlg.show()
        self.dlg.mQgsFileWidgetInputFile.lineEdit().clear()
        self.dlg.mQgsFileWidgetOutputFile.lineEdit().clear()
        self.dlg.checkBoxAddLayerToMap.setChecked(False)
        self.dlg.labelCtryName.setEnabled(False)
        self.dlg.lineEditCountryName.clear()
        self.dlg.lineEditCountryName.setEnabled(False)
        self.dlg.labelVertUOM.setEnabled(False)
        self.dlg.comboBoxVerticalUOM.setCurrentIndex(0)
        self.dlg.comboBoxVerticalUOM.setEnabled(False)
        self.dlg.comboBoxCSVDelimiter.setCurrentIndex(0)
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
