# -*- coding: utf-8 -*-
# Ce script permet l'ouverture et la fermeture des Dialogs d'information (A propos, Note de version, Aide).

# Import des modules Python et PyQt5 nécessaire à l'exécution de ce fichier
import sys
import os
from PyQt5.QtWidgets import (QDialog)

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire aux Dialogs d'information
from aboutForm import (Ui_aboutForm)
from versionForm import (Ui_versionForm)
from helpForm import (Ui_helpForm)

class About_dialog(QDialog, Ui_aboutForm):
    '''Gére le fonctionnement interne du Dialog "A Propos" après son ouverture via le menu'''

    def __init__(self, iface):
        '''
        Constructeur.

        :param iface: Une instance d'interface qui sera passée à cette classe
                qui fournit le crochet par lequel vous pouvez manipuler l'application QGIS
                au moment de l'exécution.
        :type iface: QgsInterface
        '''
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.onAccept)

    def onAccept(self):
        '''Envoi le signal permettant la fermeture de la fenêtre'''
        self.accept()

class Version_dialog(QDialog, Ui_versionForm):
    def __init__(self, iface):
        '''
        Constructeur.

        :param iface: Une instance d'interface qui sera passée à cette classe
                qui fournit le crochet par lequel vous pouvez manipuler l'application QGIS
                au moment de l'exécution.
        :type iface: QgsInterface
        '''
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.onAccept)

    def onAccept(self):
        '''Envoi le signal permettant la fermeture de la fenêtre'''
        self.accept()

class Help_dialog(QDialog, Ui_helpForm):
    def __init__(self, iface):
        '''
        Constructeur.

        :param iface: Une instance d'interface qui sera passée à cette classe
                qui fournit le crochet par lequel vous pouvez manipuler l'application QGIS
                au moment de l'exécution.
        :type iface: QgsInterface
        '''
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.onAccept)

    def onAccept(self):
        '''Envoi le signal permettant la fermeture de la fenêtre'''
        self.accept()
