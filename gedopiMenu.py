# -*- coding: utf-8 -*-
# Ce script construit le menu du plugin et gère l'ouverture et la fermeture des fenêtres et formulaires.

# Import des modules PyQt5 nécessaire à l'exécution de ce fichier
from PyQt5.QtGui import (QIcon)
from PyQt5.QtWidgets import (QAction, QDockWidget, QMenu)

# Initialise les ressources Qt à partir du fichier resources.py
from .resources_rc import *

# Import des scripts principaux des différentes pages du plugin
from .commonDialogs import (Gedopi_common)
from .autreDialogs import (About_dialog, Version_dialog, Help_dialog)
from .espePecheElecDialogs import (EspePecheElec_dialog)
from .exportCsvDialogs import (Csv_dialog)
from .bailPecheDialogs import (Bail_peche_dialog)
from .opePecheDialogs import (Peche_elec_dialog)
from .opeSuiviDialogs import (Suivi_thermi_dialog)
from .opeInventaireDialogs import (Inventaire_dialog)
from .stationDialogs import (Station_dialog)

import os.path

class gedopi:
    '''Implémentation du plugin QGIS.'''

    def __init__(self, iface):
        '''
        Constructeur.

        :param iface: Une instance d'interface qui sera passée à cette classe
                qui fournit le crochet par lequel vous pouvez manipuler l'application QGIS
                au moment de l'exécution.
        :type iface: QgsInterface
        '''
     # Sauvegarde la référence à l'interface QGIS
        self.iface = iface
        self.mapCanvas = iface.mapCanvas()

     # Initialise le répertoire du plugin
        self.plugin_dir = os.path.dirname(__file__)

     # Déclaration des attributs d'instance
        self.actions = []
        self.pluginIsActive = True
        self.dockwidget = None

     # Ajout de menu perso
        self.espePecheElec_action = None
        self.csv_action = None
        self.bail_peche_action = None
        self.station_action = None
        self.ope_peche_action = None
        self.ope_suivi_action = None
        self.ope_inventaire_action = None
        self.about_action = None
        self.help_action = None
        self.version_action = None

     # Initialise les attributs "dialog"
        self.csv_dialog = None
        self.bail_peche_dialog = None
        self.station_dialog = None
        self.peche_elec_dialog = None
        self.suivi_thermi_dialog = None
        self.inventaire_dialog = None

    def initGui(self):
        '''Créé les entrées de menu et les icônes de la barre d'outils dans l'interface graphique de QGIS.'''

     # # Décommentez pour ajouter le plugin au menu "Extensions" de QGIS
        # icon_path = ':/plugins/gedopi/icon.png'
        # self.add_action(
            # icon_path,
            # text=self.tr(u'Gedopi'),
            # callback=self.run,
            # parent=self.iface.mainWindow())

     # Ajoute le plugin dans un menu dédié
        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setObjectName("menu_gedopi")
        self.menu.setTitle("Gedopi")
        menuBar = self.iface.mainWindow().menuBar()
        menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)

     # Onglet Couche pêche élec
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon1.png")
        self.espePecheElec_action = QAction(icon,u"Export pêche électrique", self.iface.mainWindow())
        self.espePecheElec_action.triggered.connect(self.open_espePecheElec_dialog)

     # Onglet Export CSV
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon1.png")
        self.csv_action = QAction(icon,u"Export CSV", self.iface.mainWindow())
        self.csv_action.triggered.connect(self.toggle_csv_dialog)

     # Onglet droit de pêche
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon1.png")
        self.bail_peche_action = QAction(icon,u"Droit de pêche", self.iface.mainWindow())
        self.bail_peche_action.triggered.connect(self.toggle_bail_peche_dialog)

     # Onglet station
        icon = QIcon(os.path.dirname(__file__) + "/icons/icon1.png")
        self.station_action = QAction(icon,u"Station", self.iface.mainWindow())
        self.station_action.triggered.connect(self.toggle_station_dialog)

     # Onglet opération
      # Pêches électriques
        icon = QIcon(os.path.dirname(__file__) + "/icons/database1.png")
        self.ope_peche_action = QAction(icon, u"Pêche électrique", self.iface.mainWindow())
        self.ope_peche_action.setCheckable(True)
        self.ope_peche_action.setChecked(False)
        self.ope_peche_action.triggered.connect(self.toggle_peche_elec_dialog)

      # Suivi thermiques
        icon = QIcon(os.path.dirname(__file__) + "/icons/database2.png")
        self.ope_suivi_action = QAction(icon, u"Suivi thermique", self.iface.mainWindow())
        self.ope_suivi_action.setCheckable(True)
        self.ope_suivi_action.setChecked(False)
        self.ope_suivi_action.triggered.connect(self.toggle_suivi_thermi_dialog)

      # Inventaire de reproduction
        icon = QIcon(os.path.dirname(__file__) + "/icons/database3.png")
        self.ope_inventaire_action = QAction(icon, u"Inventaire de reproduction", self.iface.mainWindow())
        self.ope_inventaire_action.setCheckable(True)
        self.ope_inventaire_action.setChecked(False)
        self.ope_inventaire_action.triggered.connect(self.toggle_inventaire_dialog)

     # Onglet Autres
      # Action à propos
        icon = QIcon(os.path.dirname(__file__) + "/icons/about1.png")
        self.about_action = QAction(icon, u"À propos", self.iface.mainWindow())
        self.about_action.triggered.connect(self.open_about_dialog)

      # Action aide
        icon = QIcon(os.path.dirname(__file__) + "/icons/about2.png")
        self.help_action = QAction(icon, u"Aide", self.iface.mainWindow())
        self.help_action.triggered.connect(self.open_help_dialog)

      # Action notes de version
        icon = QIcon(os.path.dirname(__file__) + "/icons/about3.png")
        self.version_action = QAction(icon, u"Notes de version", self.iface.mainWindow())
        self.version_action.triggered.connect(self.open_version_dialog)

     # Gestion du menu
        self.menu.addAction(self.espePecheElec_action)
        self.menu.addAction(self.csv_action)
        self.menu.addAction(self.bail_peche_action)
        self.menu.addAction(self.station_action)
        self.ope_menu = self.menu.addMenu(u"Opérations")
        self.ope_menu.addAction(self.ope_peche_action)
        self.ope_menu.addAction(self.ope_suivi_action)
        self.ope_menu.addAction(self.ope_inventaire_action)
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.help_action)
        self.menu.addAction(self.version_action)

        icon = QIcon(os.path.dirname(__file__) + "/icons/icon1.png")
        self.ope_menu.setIcon(icon)

     # Gestion des fenêtres dockées
        self.hide_toogle_dialog()

    def hide_toogle_dialog(self):
        '''Gère la fermeture et l'ouverture des QDockWidget afin qu'un seul soit ouvert à la fois'''

        listQDockWidget = self.iface.mainWindow().findChildren(QDockWidget)
        for elem in listQDockWidget:
            if (type(elem).__name__ == "Csv_dialog"):
                if (elem.isVisible()):
                    elem.hide()
            if (type(elem).__name__ == "Bail_peche_dialog"):
                if (elem.isVisible()):
                    elem.hide()
            if (type(elem).__name__ == "Peche_elec_dialog"):
                if (elem.isVisible()):
                    elem.hide()
            if (type(elem).__name__ == "Suivi_thermi_dialog"):
                if (elem.isVisible()):
                    elem.hide()
            if (type(elem).__name__ == "Inventaire_dialog"):
                if (elem.isVisible()):
                    elem.hide()
            if (type(elem).__name__ == "Station_dialog"):
                if (elem.isVisible()):
                    elem.hide()

    def toggle_csv_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget de l'export CSV'''

        if not self.csv_dialog:
            self.hide_toogle_dialog()
            dialog = Csv_dialog(self.iface, self.csv_action)
            self.csv_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.csv_dialog.isVisible():
                self.csv_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.csv_dialog.show()

    def toggle_bail_peche_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget des Droits de pêche'''

        if not self.bail_peche_dialog:
            self.hide_toogle_dialog()
            dialog = Bail_peche_dialog(self.iface, self.bail_peche_action)
            self.bail_peche_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.bail_peche_dialog.isVisible():
                self.bail_peche_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.bail_peche_dialog.show()

    def toggle_peche_elec_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget des Pêches électriques'''

        if not self.peche_elec_dialog:
            self.hide_toogle_dialog()
            dialog = Peche_elec_dialog(self.iface, self.ope_peche_action)
            self.peche_elec_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.peche_elec_dialog.isVisible():
                self.peche_elec_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.peche_elec_dialog.show()

    def toggle_suivi_thermi_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget des Suivis thermiques'''

        if not self.suivi_thermi_dialog:
            self.hide_toogle_dialog()
            dialog = Suivi_thermi_dialog(self.iface, self.ope_suivi_action)
            self.suivi_thermi_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.suivi_thermi_dialog.isVisible():
                self.suivi_thermi_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.suivi_thermi_dialog.show()

    def toggle_inventaire_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget des Inventaires de reproduction'''

        if not self.inventaire_dialog:
            self.hide_toogle_dialog()
            dialog = Inventaire_dialog(self.iface, self.ope_inventaire_action)
            self.inventaire_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.inventaire_dialog.isVisible():
                self.inventaire_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.inventaire_dialog.show()

    def toggle_station_dialog(self):
        '''Gère la fermeture et l'ouverture du QDockWidget des Stations'''

        if not self.station_dialog:
            self.hide_toogle_dialog()
            dialog = Station_dialog(self.iface, self.station_action)
            self.station_dialog = dialog
            self.gedopi_common = Gedopi_common(dialog)
        else:
            if self.station_dialog.isVisible():
                self.station_dialog.hide()
            else:
                self.hide_toogle_dialog()
                self.station_dialog.show()

    # def onClosePlugin(self):
        '''Nettoyage des éléments nécessaires ici lorsque le plugin est fermé'''

        # disconnects
        # self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # # Supprimez cette instruction si QDockWidget doit rester
        # # pour être réutilisé si le plugin est rouvert
        # # Commentez la prochaine instruction tant qu'elle provoque le crash de QGIS
        # # lors de la fermeture de la fenêtre dockée :
        # self.dockwidget = None
        # self.pluginIsActive = True

    def open_espePecheElec_dialog(self):
        '''Permet l'exécution et l'ouverture du dialog "Couche espèce (Pêche électrique)"'''
        dialog = EspePecheElec_dialog(self.iface)
        dialog.exec_()

    def open_about_dialog(self):
        '''Permet l'exécution et l'ouverture du Dialog "A Propos"'''

        dialog = About_dialog(self.iface)
        dialog.exec_()

    def open_help_dialog(self):
        '''Permet l'exécution et l'ouverture du Dialog "Aide"'''

        # message = "<h2>Ecrire votre message ici</h2>"
        # dialog = Help_dialog(self.iface, message)
        dialog = Help_dialog(self.iface)
        dialog.exec_()

    def open_version_dialog(self):
        '''Permet l'exécution et l'ouverture du Dialog "Note de version"'''

        dialog = Version_dialog(self.iface)
        dialog.exec_()

    def unload(self):
        '''Supprime les éléments de menu et les icônes de QGIS GUI.'''

        self.menu.deleteLater()

        listQDockWidget = self.iface.mainWindow().findChildren(QDockWidget)
        for elem in listQDockWidget:
            if (type(elem).__name__ == "Csv_dialog"):
                if (elem.isVisible()):
                    elem.close()
            if (type(elem).__name__ == "Bail_peche_dialog"):
                if (elem.isVisible()):
                    elem.close()
            if (type(elem).__name__ == "Peche_elec_dialog"):
                if (elem.isVisible()):
                    elem.close()
            if (type(elem).__name__ == "Suivi_thermi_dialog"):
                if (elem.isVisible()):
                    elem.close()
            if (type(elem).__name__ == "Inventaire_dialog"):
                if (elem.isVisible()):
                    elem.close()
            if (type(elem).__name__ == "Station_dialog"):
                if (elem.isVisible()):
                    elem.close()

    def run(self):
        '''Exécute la méthode qui charge et démarre le plugin.'''
        if not self.pluginIsActive:
            self.pluginIsActive = True

            # Qdockwidget peut ne pas exister si:
            #    - c'est la première exécution du plugin
            #    - si il est supprimé à la fermeture (voir méthode self.onClosePlugin)
            if self.dockwidget == None:
                # Créé le QDockWidget (après la traduction si existante) et garde la référence
                self.dockwidget = gedopiDockWidget()

            # # Décommentez pour fournir un nettoyage à la fermeture de dockwidget
            # self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # affiche le dockwidget
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
