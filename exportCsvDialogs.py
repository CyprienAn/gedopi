# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du formulaire "Export CSV" du plugin.

# Import des modules Python, PyQt5 et QGIS nécessaire à l'exécution de ce fichier
import sys
import csv
import os
from PyQt5.QtCore import (Qt, QDate)
from PyQt5.QtGui import (QCursor)
from PyQt5.QtWidgets import (QApplication, QFileDialog, QDockWidget, QMessageBox)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlTableModel)
#from qgis.core import ()
from qgis.gui import (QgsMessageBar)

# Initialise les ressources Qt à partir du fichier resources.py
# import resources_rc

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire
from exportCsvForm import (Ui_dwcExportForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

class Csv_dialog(QDockWidget, Ui_dwcExportForm):
    '''
    Class principal du formulaire "Export CSV"

    :param QDockWidget: Permet d'ancrer le formulaire comme définit dans gedopiMenu
    :type QDockWidget: QDockWidget

    :param Ui_dwcBopeMainForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dwcBopeMainForm: class
    '''
    def __init__(self, iface, action):
        '''
        Constructeur, déclaration de variable, connection des événements et initialisation du formulaire

        :param iface: Une instance d'interface qui sera passée à cette classe
                qui fournit le crochet par lequel vous pouvez manipuler l'application QGIS
                au moment de l'exécution.
        :type iface: QgsInterface

        :param action: action obtenu lors du clic dans le menu,
                paramètre obtenu par gedopiMenu
        :type action: QAction
        '''
        QDockWidget.__init__(self)
        self.iface = iface
        self.mc = self.iface.mapCanvas()
        self.action = action
        self.setupUi(self)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self)

        # VisibilityChanged est un signal émit par QDockWidget lorsqu'il se ferme ou s'ouvre
        self.visibilityChanged.connect(self.onVisibilityChange)

        # Méthodes communes à d'autres formulaires (obtention des infos de connexion postgresql)
        self.gc = Gedopi_common(self)

        # Variables pour la connexion à la base de donnée
        self.db = None
        self.dbType = ""
        self.dbSchema = ""

        # Variables pour récupérer les données des tables
        self.layer = None
        self.mapper = None

        # Variables diverses
        self.leTel.setInputMask("#9999999999999")

        # Variables permettant de contrôler l'activation du bouton "Et" en fonction des critères
        self.possessionBool = False
        self.communeBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False
        self.clauseSelect = False

        # Variables de constitution de la requête
        self.wselect = ""
        self.wwhere = ""
        self.wwhereSelect = ""
        self.cfrom = ""
        self.wwherePossession = ""
        self.wwhereProprio = ""

        # Connexion des événements
        self.btnBopeEt.clicked.connect(self.et)
        self.btnBopeOu.clicked.connect(self.ou)
        self.btnBopePossede.clicked.connect(self.ajoutPossession)
        self.btnBopeCommune.clicked.connect(self.ajoutCommune)
        self.btnBopeAappma.clicked.connect(self.ajoutAappma)
        self.btnBopeCeau.clicked.connect(self.ajoutCeau)
        self.btnBopeSign.clicked.connect(self.ajoutDateSign)
        self.btnBopeFin.clicked.connect(self.ajoutDateFin)
        self.btnProprio.clicked.connect(self.ajoutProprio)
        self.btnAdresse.clicked.connect(self.ajoutAdresse)
        self.btnPecheEt.clicked.connect(self.et)
        self.btnPecheOu.clicked.connect(self.ou)
        self.btnPecheAappma.clicked.connect(self.ajoutAappma)
        self.btnPechePdpg.clicked.connect(self.ajoutPdpg)
        self.btnPecheCeau.clicked.connect(self.ajoutCeau)
        self.btnPecheMeau.clicked.connect(self.ajoutMeau)
        self.btnPecheAnnee.clicked.connect(self.ajoutAnnee)
        self.btnPecheEspece.clicked.connect(self.ajoutEspece)
        self.btnThermiEt.clicked.connect(self.et)
        self.btnThermiOu.clicked.connect(self.ou)
        self.btnThermiAappma.clicked.connect(self.ajoutAappma)
        self.btnThermiPdpg.clicked.connect(self.ajoutPdpg)
        self.btnThermiCeau.clicked.connect(self.ajoutCeau)
        self.btnThermiMeau.clicked.connect(self.ajoutMeau)
        self.btnThermiAnnee.clicked.connect(self.ajoutAnnee)
        self.btnReproEt.clicked.connect(self.et)
        self.btnReproOu.clicked.connect(self.ou)
        self.btnReproAappma.clicked.connect(self.ajoutAappma)
        self.btnReproPdpg.clicked.connect(self.ajoutPdpg)
        self.btnReproCeau.clicked.connect(self.ajoutCeau)
        self.btnReproMeau.clicked.connect(self.ajoutMeau)
        self.btnReproAnnee.clicked.connect(self.ajoutAnnee)
        self.btnPreviRequete.clicked.connect(self.previSql)
        self.btnRaz.clicked.connect(self.raz)
        self.btnPreviResu.clicked.connect(self.previResu)
        self.btnEnregistrer.clicked.connect(self.queryExport)

        self.tabWidget.currentChanged.connect(self.raz)

        # Initialisation du formulaire
        if self.verifiePresenceCouche() == True:
            self.raz()
            self.setupModel()
            self.btnPreviRequete.setEnabled(True)
            self.btnRaz.setEnabled(True)
            self.btnPreviResu.setEnabled(True)
            self.btnEnregistrer.setEnabled(True)
            self.txtSql.setEnabled(True)
            self.tabWidget.setTabEnabled(0, True)
            self.tabWidget.setTabEnabled(1, True)
            self.tabWidget.setTabEnabled(2, True)
            self.tabWidget.setTabEnabled(3, True)
        else :
            self.btnPreviRequete.setEnabled(False)
            self.btnRaz.setEnabled(False)
            self.btnPreviResu.setEnabled(False)
            self.btnEnregistrer.setEnabled(False)
            self.txtSql.setEnabled(False)
            self.iface.messageBar().pushMessage("Erreur : ", u"Les couches des droits de pêche, pêches élec, suivis thermique et inventaires repro ne sont pas chargées ...", level= QgsMessageBar.CRITICAL, duration = 5)

    def onVisibilityChange(self, visible):
        '''
        Lorsque le formulaire change de visibilité,
        soit les méthodes de déconnexion sont appelées,
        soit celles de connexion

        :param visible: émit par QDockWidget lors de la fermeture
                ou l'ouverture du formulaire
        :type visible: bool
        '''
        if not visible:
            self.action.setChecked(False)
            if self.db:
                self.closeDatabase()
                self.raz()
        else:
            if self.verifiePresenceCouche():
                self.setupModel()
                self.tabWidget.setCurrentIndex(0)

    def verifiePresenceCouche(self):
        '''
        Vérifie la présence des couches des parcelles, pêche élec, suivi thermique, inventaire repro et renvoi dans __init__, True ou False,
        active le setupModel si return True,
        verouille le formulaire si return False
        '''
        bopeTrue = False
        pecheTrue = False
        thermiTrue = False
        reproTrue = False

        self.layer = None
        self.layerBope = None
        self.layerPeche = None
        self.layerThermi = None
        self.layerRepro = None

        self.layerBope = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
        self.layerPeche = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        self.layerThermi = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
        self.layerRepro = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')

        if self.layerBope:
            bopeTrue = True
            self.layer = self.layerBope
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des parcelles n'est pas chargée ...", level= QgsMessageBar.WARNING, duration = 5)
            self.tabWidget.setTabEnabled(0, False)

        if self.layerPeche:
            pecheTrue = True
            self.layer = self.layerPeche
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des pêches électrique n'est pas chargée ...", level= QgsMessageBar.WARNING, duration = 5)
            self.tabWidget.setTabEnabled(1, False)

        if self.layerThermi:
            thermiTrue = True
            self.layer = self.layerThermi
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des suivis thermique n'est pas chargée ...", level= QgsMessageBar.WARNING, duration = 5)
            self.tabWidget.setTabEnabled(2, False)

        if self.layerRepro:
            reproTrue = True
            self.layer = self.layerRepro
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des inventaires repro n'est pas chargée ...", level= QgsMessageBar.WARNING, duration = 5)
            self.tabWidget.setTabEnabled(3, False)

        if bopeTrue == True or pecheTrue == True or thermiTrue == True or reproTrue == True :
            return True
        else :
            return False

    def closeDatabase(self):
        '''Supprime certaines variables et déconnecte la base de données'''

        del self.modelAappma
        del self.modelRiviere
        del self.modelCommune
        del self.modelEspece
        del self.modelMeau
        del self.modelPdpg

        self.raz()

        self.db.close()
        del self.db
        self.db = None
        QSqlDatabase.removeDatabase('db1')

    def setupModel(self):
        '''
        Initialise le formulaire en le connectant à la base de données
        et en attribuant aux différents champs leurs tables ou colonnes PostgreSQL
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.infoMessage = u"Gedopi - Droit de pêche"
        if not self.db:
            connectionParams = self.gc.getConnectionParameterFromDbLayer(self.layer)
            if (connectionParams['dbType'] == u'postgres' or connectionParams['dbType'] == u'postgis'):
                self.dbType = "postgres"
                self.db = QSqlDatabase.addDatabase("QPSQL", 'db1')
                self.db.setDatabaseName(connectionParams['dbname'])
                self.db.setUserName(connectionParams['user'])
                self.db.setPassword(connectionParams['password'])
                self.db.setHostName(connectionParams['host'])
                self.dbSchema = connectionParams['schema']

            if (not self.db.open()):
                QMessageBox.critical(self, "Erreur", u"Impossible de se connecter à la base de données ...", QMessageBox.Ok)
                QApplication.restoreOverrideCursor()
                return

        # Création du modèle des Communes et attribution aux combobox
        self.modelCommune = QSqlTableModel(self, self.db)
        wrelation = "commune"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelCommune.setTable(wrelation)
        self.modelCommune.setSort(2, Qt.AscendingOrder)
        if (not self.modelCommune.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Commune dans le setupModele() : \n" + self.modelCommune.lastError().text(), QMessageBox.Ok)
        self.cmbBopeCommune.setModel(self.modelCommune)
        self.cmbBopeCommune.setModelColumn(self.modelCommune.fieldIndex("com_nom"))

        # Création du modèle des AAPPMA et attribution aux combobox
        self.modelAappma= QSqlTableModel(self, self.db)
        wrelation = "aappma"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelAappma.setTable(wrelation)
        self.modelAappma.setSort(1, Qt.AscendingOrder)
        if (not self.modelAappma.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle AAPPMA dans le setupModele() : \n" + self.modelAappma.lastError().text(), QMessageBox.Ok)
        self.cmbBopeAappma.setModel(self.modelAappma)
        self.cmbBopeAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        self.cmbPecheAappma.setModel(self.modelAappma)
        self.cmbPecheAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        self.cmbThermiAappma.setModel(self.modelAappma)
        self.cmbThermiAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        self.cmbReproAappma.setModel(self.modelAappma)
        self.cmbReproAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        # Création du modèle des Rivières et attribution aux combobox
        self.modelRiviere = QSqlTableModel(self, self.db)
        wrelation = "cours_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelRiviere.setTable(wrelation)
        self.modelRiviere.setFilter("ceau_nom <> 'NR'")
        self.modelRiviere.setSort(2, Qt.AscendingOrder)
        if (not self.modelRiviere.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Rivière dans le setupModele() : \n" + self.modelRiviere.lastError().text(), QMessageBox.Ok)
        self.cmbBopeCeau.setModel(self.modelRiviere)
        self.cmbBopeCeau.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        self.cmbPecheCeau.setModel(self.modelRiviere)
        self.cmbPecheCeau.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        self.cmbThermiCeau.setModel(self.modelRiviere)
        self.cmbThermiCeau.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        self.cmbReproCeau.setModel(self.modelRiviere)
        self.cmbReproCeau.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        # Création du modèle des PDPG et attribution aux combobox
        self.modelPdpg = QSqlQueryModel(self)
        wrelation = "contexte_pdpg"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelPdpg.setQuery("select pdpg_id, pdpg_nom || ' ; ' || pdpg_code from " + wrelation + " order by pdpg_nom;", self.db)
        if self.modelPdpg.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle PDPG dans le setupModel() : \n" + self.modelPdpg.lastError().text(), QMessageBox.Ok)
        self.cmbPechePdpg.setModel(self.modelPdpg)
        self.cmbPechePdpg.setModelColumn(1)

        self.cmbThermiPdpg.setModel(self.modelPdpg)
        self.cmbThermiPdpg.setModelColumn(1)

        self.cmbReproPdpg.setModel(self.modelPdpg)
        self.cmbReproPdpg.setModelColumn(1)

        # Création du modèle des Masses d'eau et attribution aux combobox
        self.modelMeau = QSqlQueryModel(self)
        wrelation = "masse_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelMeau.setQuery("select meau_code, meau_code || ' ; ' || meau_nom from " + wrelation + " order by meau_code;", self.db)
        if self.modelMeau.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Masse d'eau dans le rowChange() : \n" + self.modelMeau.lastError().text(), QMessageBox.Ok)
        self.cmbPecheMeau.setModel(self.modelMeau)
        self.cmbPecheMeau.setModelColumn(1)

        self.cmbThermiMeau.setModel(self.modelMeau)
        self.cmbThermiMeau.setModelColumn(1)

        self.cmbReproMeau.setModel(self.modelMeau)
        self.cmbReproMeau.setModelColumn(1)

        # Création du modèle des Espèces et attribution aux combobox
        self.modelEspece = QSqlTableModel(self, self.db)
        wrelation = "espece"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelEspece.setTable(wrelation)
        self.modelEspece.setSort(2, Qt.AscendingOrder)
        if (not self.modelEspece.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Espèce dans le setupModele() : \n" + self.modelEspece.lastError().text(), QMessageBox.Ok)
        self.cmbPecheEspece.setModel(self.modelEspece)
        self.cmbPecheEspece.setModelColumn(self.modelEspece.fieldIndex("esp_nom"))

        QApplication.restoreOverrideCursor()

    def raz(self):
        '''Réinitialise toutes les variables de la fenêtre afin de recommencer une nouvelle requête'''
        self.possessionBool = False
        self.communeBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False
        self.clauseSelect = False

        self.wrq = ""
        self.txtSql.setText("")
        self.wwhere = ""
        self.wwhereSelect = ""
        self.cfrom = ""
        self.wselect = ""
        self.wwherePossession = ""
        self.wwhereProprio = ""
        self.requete = ""
        modelRaz = QSqlQueryModel()
        self.tbvPrevisu.setModel(modelRaz)
        self.savefile = ""
        self.cheminCsv = ""
        self.leNom.setText("")
        self.leMail.setText("")
        self.leTel.setText("")
        self.leAdresse.setText("")

        self.chkBopePossede.setChecked(False)
        self.dateBopeSign.setDate(QDate(2000,1,1))
        self.dateBopeFin.setDate(QDate(2000,1,1))
        self.datePecheAnnee.setDate(QDate(2000,1,1))
        self.dateThermiAnnee.setDate(QDate(2000,1,1))
        self.dateReproAnnee.setDate(QDate(2000,1,1))

        self.btnBopeEt.setEnabled(False)
        self.btnBopeOu.setEnabled(False)
        self.btnPecheEt.setEnabled(False)
        self.btnPecheOu.setEnabled(False)
        self.btnThermiEt.setEnabled(False)
        self.btnThermiOu.setEnabled(False)
        self.btnReproEt.setEnabled(False)
        self.btnReproOu.setEnabled(False)

        self.btnBopePossede.setEnabled(True)
        self.btnBopeCommune.setEnabled(True)
        self.btnBopeAappma.setEnabled(True)
        self.btnBopeCeau.setEnabled(True)
        self.btnBopeSign.setEnabled(True)
        self.btnBopeFin.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)
        self.btnPecheAappma.setEnabled(True)
        self.btnPechePdpg.setEnabled(True)
        self.btnPecheCeau.setEnabled(True)
        self.btnPecheMeau.setEnabled(True)
        self.btnPecheAnnee.setEnabled(True)
        self.btnPecheEspece.setEnabled(True)
        self.btnThermiAappma.setEnabled(True)
        self.btnThermiPdpg.setEnabled(True)
        self.btnThermiCeau.setEnabled(True)
        self.btnThermiMeau.setEnabled(True)
        self.btnThermiAnnee.setEnabled(True)
        self.btnReproAappma.setEnabled(True)
        self.btnReproPdpg.setEnabled(True)
        self.btnReproCeau.setEnabled(True)
        self.btnReproMeau.setEnabled(True)
        self.btnReproAnnee.setEnabled(True)

        self.chkSign.setChecked(True)
        self.chkFin.setChecked(False)
        self.chkPossede.setChecked(False)
        self.chkIntemporel.setChecked(False)
        self.chkAappma.setChecked(True)
        self.chkCeau.setChecked(True)
        self.chkParcelle.setChecked(True)
        self.chkSection.setChecked(True)
        self.chkCommune.setChecked(True)
        self.chkInsee.setChecked(True)
        self.chkPostal.setChecked(True)
        self.chkProprio.setChecked(True)
        self.chkAdresse.setChecked(False)
        self.chkTel.setChecked(False)
        self.chkMail.setChecked(False)

        self.chkDatePeche.setChecked(True)
        self.chkLongueurPeche.setChecked(True)
        self.chkProfondeur.setChecked(False)
        self.chkLargeurPeche.setChecked(False)
        self.chkSurfacePeche.setChecked(False)
        self.chkPente.setChecked(False)
        self.chkXYPeche.setChecked(True)
        self.chkNtt.setChecked(False)
        self.chkNttReel.setChecked(False)
        self.chkIpr.setChecked(False)
        self.chkIprCorrespond.setChecked(False)
        self.chkEspece.setChecked(True)
        self.chkBiomasse.setChecked(True)
        self.chkBioCorrespond.setChecked(False)
        self.chkDensite.setChecked(True)
        self.chkDenCorrespond.setChecked(False)
        self.chkComplet.setChecked(False)
        self.chkObservationPeche.setChecked(False)
        self.chkCeauPeche.setChecked(False)
        self.chkMotif.setChecked(False)
        self.chkCondition.setChecked(False)
        self.chkPdpgPeche.setChecked(False)
        self.chkMeauPeche.setChecked(False)
        self.chkMeauCodePeche.setChecked(False)
        self.chkCodePeche.setChecked(True)
        self.chkStationPeche.setChecked(False)
        self.chkDistancePeche.setChecked(False)
        self.chkAltitudePeche.setChecked(False)
        self.chkAappmaPeche.setChecked(False)
        self.chkSurfBVPeche.setChecked(False)
        self.chkMoaPeche.setChecked(False)

        self.chkDateDebut.setChecked(True)
        self.chkDateFin.setChecked(True)
        self.chkDuree.setChecked(False)
        self.chkTimin.setChecked(False)
        self.chkTimax.setChecked(False)
        self.chkAjmaxTi.setChecked(False)
        self.chkDAjmaxTi.setChecked(False)
        self.chkTmjMin.setChecked(False)
        self.chkTmjMax.setChecked(False)
        self.chkTmpMoy.setChecked(False)
        self.chkTmj30Max.setChecked(False)
        self.chkNbjTmj419.setChecked(False)
        self.chkP100Tmj419.setChecked(False)
        self.chkP100TmjInf4.setChecked(False)
        self.chkP100TmjSup19.setChecked(False)
        self.chkNbMaxTiCsfSup19.setChecked(False)
        self.chkNbMaxTiCsfSupEg25.setChecked(False)
        self.chkNbMaxTiCsfSupEg15.setChecked(False)
        self.chkD50Ponte.setChecked(False)
        self.chkNbjIncub.setChecked(False)
        self.chkD50Eclo.setChecked(False)
        self.chkNbjRsp.setChecked(False)
        self.chkD50Emg.setChecked(False)
        self.chkNbjPel.setChecked(False)
        self.chkNbTiSup15Pel.setChecked(False)
        self.chkNbMaxTiCsfSup15Pel.setChecked(False)
        self.chkNbTiInf15Pel.setChecked(False)
        self.chkNbMaxTiCsfInf15Pel.setChecked(False)
        self.chkCodeThermi.setChecked(True)
        self.chkStationThermi.setChecked(True)
        self.chkCeauThermi.setChecked(True)
        self.chkXYStationThermi.setChecked(True)
        self.chkXYSondeThermi.setChecked(True)
        self.chkDistanceThermi.setChecked(False)
        self.chkAltitudeThermi.setChecked(False)
        self.chkAappmaThermi.setChecked(False)
        self.chkSurfBVThermi.setChecked(False)
        self.chkMoaThermi.setChecked(False)
        self.chkMeauThermi.setChecked(False)
        self.chkPdpgThermi.setChecked(False)
        self.chkMeauCodeThermi.setChecked(False)

        self.chkDateRepro.setChecked(True)
        self.chkPassage.setChecked(False)
        self.chkSgf.setChecked(False)
        self.chkZfp.setChecked(False)
        self.chkFrayere.setChecked(True)
        self.chkSurfaceFrayere.setChecked(True)
        self.chkXYStationRepro.setChecked(True)
        self.chkXYAvalRepro.setChecked(True)
        self.chkBaran.setChecked(False)
        self.chkBaranCorrespond.setChecked(False)
        self.chkLargeurRepro.setChecked(False)
        self.chkLongueurRepro.setChecked(True)
        self.chkCeauRepro.setChecked(True)
        self.chkPdpgRepro.setChecked(False)
        self.chkMeauRepro.setChecked(False)
        self.chkMeauCodeRepro.setChecked(False)
        self.chkMoaRepro.setChecked(True)
        self.chkCodeRepro.setChecked(True)
        self.chkStationRepro.setChecked(True)
        self.chkDistanceRepro.setChecked(False)
        self.chkAltitudeRepro.setChecked(False)
        self.chkAappmaRepro.setChecked(False)
        self.chkSurfBVRepro.setChecked(False)

    def et(self):
        '''Change l'état des boutons et ajoute "and" à la requête'''

        self.btnBopeEt.setEnabled(False)
        self.btnBopeOu.setEnabled(False)
        self.btnPecheEt.setEnabled(False)
        self.btnPecheOu.setEnabled(False)
        self.btnThermiEt.setEnabled(False)
        self.btnThermiOu.setEnabled(False)
        self.btnReproEt.setEnabled(False)
        self.btnReproOu.setEnabled(False)

        self.btnBopeCeau.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)
        self.btnPecheEspece.setEnabled(True)

        if self.possessionBool == False:
            self.btnBopePossede.setEnabled(True)

        if self.communeBool == False:
            self.btnBopeCommune.setEnabled(True)

        if self.aappmaBool == False:
            self.btnBopeAappma.setEnabled(True)
            self.btnPecheAappma.setEnabled(True)
            self.btnThermiAappma.setEnabled(True)
            self.btnReproAappma.setEnabled(True)

        if self.anneeSignBool == False:
            self.btnBopeSign.setEnabled(True)

        if self.anneeFinBool == False:
            self.btnBopeFin.setEnabled(True)

        if self.pdpgBool == False:
            self.btnPechePdpg.setEnabled(True)
            self.btnThermiPdpg.setEnabled(True)
            self.btnReproPdpg.setEnabled(True)

        if self.ceauBool == False:
            self.btnPecheCeau.setEnabled(True)
            self.btnThermiCeau.setEnabled(True)
            self.btnReproCeau.setEnabled(True)

        if self.meauBool == False:
            self.btnPecheMeau.setEnabled(True)
            self.btnThermiMeau.setEnabled(True)
            self.btnReproMeau.setEnabled(True)

        if self.anneeBool == False:
            self.btnPecheAnnee.setEnabled(True)
            self.btnThermiAnnee.setEnabled(True)
            self.btnReproAnnee.setEnabled(True)

        self.wwhere += " AND "

    def ou(self):
        '''Change l'état des boutons et ajoute "or" à la requête'''

        self.btnBopeEt.setEnabled(False)
        self.btnBopeOu.setEnabled(False)
        self.btnPecheEt.setEnabled(False)
        self.btnPecheOu.setEnabled(False)
        self.btnThermiEt.setEnabled(False)
        self.btnThermiOu.setEnabled(False)
        self.btnReproEt.setEnabled(False)
        self.btnReproOu.setEnabled(False)

        self.btnBopePossede.setEnabled(True)
        self.btnBopeCommune.setEnabled(True)
        self.btnBopeAappma.setEnabled(True)
        self.btnBopeCeau.setEnabled(True)
        self.btnBopeSign.setEnabled(True)
        self.btnBopeFin.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)
        self.btnPecheAappma.setEnabled(True)
        self.btnPechePdpg.setEnabled(True)
        self.btnPecheCeau.setEnabled(True)
        self.btnPecheMeau.setEnabled(True)
        self.btnPecheAnnee.setEnabled(True)
        self.btnPecheEspece.setEnabled(True)
        self.btnThermiAappma.setEnabled(True)
        self.btnThermiPdpg.setEnabled(True)
        self.btnThermiCeau.setEnabled(True)
        self.btnThermiMeau.setEnabled(True)
        self.btnThermiAnnee.setEnabled(True)
        self.btnReproAappma.setEnabled(True)
        self.btnReproPdpg.setEnabled(True)
        self.btnReproCeau.setEnabled(True)
        self.btnReproMeau.setEnabled(True)
        self.btnReproAnnee.setEnabled(True)

        self.possessionBool = False
        self.communeBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False

        self.wwhere += " OR "

    def ajoutSelect(self):
        '''Création de la clause SELECT et FROM pour la requête SQL d'export en fonction de l'onglet actif dans le TabWidget'''

        self.clauseSelect = False

        if self.tabWidget.currentIndex() == 0:
            self.wselect = ""
            self.cfrom = ""
            self.wwhereSelect = ""
            self.cfrom = "data.droit_peche, data.aappma, data.bail_cours_eau, data.cours_eau, data.parcelle, data.section, data.commune, data.proprietaire "
            self.wwhereSelect = ("bope_apma_id = apma_id and bope_id = bce_bope_id and bce_ceau_id = ceau_id and bope_id = par_bope_id and par_sec_id = sec_id " +
            "and sec_com_insee = com_insee and bope_pro_id = pro_id")

            if self.chkAappma.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", apma_nom AS \"AAPPMA\""
                else:
                    self.wselect += "apma_nom AS \"AAPPMA\""

            if self.chkCeau.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ceau_nom AS \"COURS D'EAU\""
                else:
                    self.wselect += "ceau_nom AS \"COURS D'EAU\""

            if self.chkCommune.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", com_nom AS \"COMMUNE\""
                else:
                    self.wselect += "com_nom AS \"COMMUNE\""

            if self.chkPostal.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", com_postal AS \"CODE POSTAL\""
                else:
                    self.wselect += "com_postal AS \"CODE POSTAL\""

            if self.chkInsee.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", com_insee AS \"INSEE\""
                else:
                    self.wselect += "com_insee AS \"INSEE\""

            if self.chkParcelle.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", par_numero AS \"PARCELLE\""
                else:
                    self.wselect += "par_numero AS \"PARCELLE\""

            if self.chkSection.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sec_nom AS \"SECTION\""
                else:
                    self.wselect += "sec_nom AS \"SECTION\""

            if self.chkSign.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", bope_date_sign AS \"DATE DE SIGNATURE\""
                else:
                    self.wselect += "bope_date_sign AS \"DATE DE SIGNATURE\""

            if self.chkFin.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", bope_date_fin AS \"DATE DE FIN\""
                else:
                    self.wselect += "bope_date_fin AS \"DATE DE FIN\""

            if self.chkPossede.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", bope_existe AS \"EN POSSESSION\""
                else:
                    self.wselect += "bope_existe AS \"EN POSSESSION\""

            if self.chkIntemporel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", bope_infini AS \"INTEMPOREL\""
                else:
                    self.wselect += "bope_infini AS \"INTEMPOREL\""

            if self.chkProprio.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pro_nom AS \"PROPRIETAIRE\""
                else:
                    self.wselect += "pro_nom AS \"PROPRIETAIRE\""

            if self.chkAdresse.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pro_adresse AS \"ADRESSE\""
                else:
                    self.wselect += "pro_adresse AS \"ADRESSE\""

            if self.chkTel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pro_telephone AS \"TELEPHONE\""
                else:
                    self.wselect += "pro_telephone AS \"TELEPHONE\""

            if self.chkMail.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pro_mail AS \"EMAIL\""
                else:
                    self.wselect += "pro_mail AS \"EMAIL\""

        elif self.tabWidget.currentIndex() == 1:
            self.wselect = ""
            self.cfrom = ""
            self.wwhereSelect = ""
            self.cfrom = ("data.ope_peche_elec JOIN data.condition_peche ON condition_peche.cope_id = ope_peche_elec.opep_cope_id JOIN data.ipr ON ipr.ipr_id = ope_peche_elec.opep_ipr_id " +
            "JOIN data.motif_peche ON motif_peche.mope_id = ope_peche_elec.opep_mope_id JOIN data.espece_peche ON espece_peche.espe_opep_id = ope_peche_elec.opep_id " +
            "JOIN data.espece ON espece_peche.espe_esp_id = espece.esp_id JOIN data.real_peche_elec ON real_peche_elec.rp_opep_id = ope_peche_elec.opep_id " +
            "JOIN data.maitre_ouvrage ON maitre_ouvrage.moa_id = real_peche_elec.rp_moa_id JOIN data.operation ON operation.ope_code = ope_peche_elec.opep_ope_code " +
            "JOIN data.station ON station.sta_id = operation.ope_sta_id JOIN data.cours_eau ON cours_eau.ceau_id = station.sta_ceau_id " +
            "JOIN data.contexte_pdpg ON contexte_pdpg.pdpg_id = station.sta_pdpg_id " +
            "JOIN data.masse_eau ON masse_eau.meau_code = station.sta_meau_code JOIN data.aappma ON aappma.apma_id = station.sta_apma_id")

            if self.chkCeauPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", cours_eau.ceau_nom AS \"COURS D'EAU\""
                else:
                    self.wselect += "cours_eau.ceau_nom AS \"COURS D'EAU\""

            if self.chkDatePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_date AS \"DATE\""
                else:
                    self.wselect += "ope_peche_elec.opep_date AS \"DATE\""

            if self.chkCodePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", operation.ope_code AS \"CODE OPERATION\""
                else:
                    self.wselect += "operation.ope_code AS \"CODE OPERATION\""

            if self.chkMeauPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", masse_eau.meau_nom AS \"MASSE D'EAU\""
                else:
                    self.wselect += "masse_eau.meau_nom AS \"MASSE D'EAU\""

            if self.chkMeauCodePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", masse_eau.meau_code AS \"CODE MASSE D'EAU\""
                else:
                    self.wselect += "masse_eau.meau_code AS \"CODE MASSE D'EAU\""

            if self.chkPdpgPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", contexte_pdpg.pdpg_code AS \"PDPG\""
                else:
                    self.wselect += "contexte_pdpg.pdpg_code AS \"PDPG\""

            if self.chkAappmaPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", aappma.apma_nom AS \"AAPPMA\""
                else:
                    self.wselect += "aappma.apma_nom AS \"AAPPMA\""

            if self.chkStationPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_nom AS \"STATION\""
                else:
                    self.wselect += "station.sta_nom AS \"STATION\""

            if self.chkMoaPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", maitre_ouvrage.moa_nom AS \"MAITRE D'OUVRAGE\""
                else:
                    self.wselect += "maitre_ouvrage.moa_nom AS \"MAITRE D'OUVRAGE\""

            if self.chkComplet.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_complet_partielle AS \"PECHE COMPLETE\""
                else:
                    self.wselect += "ope_peche_elec.opep_complet_partielle AS \"PECHE COMPLETE\""

            if self.chkLongueurPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_longueur_prospec AS \"LONGUEUR\""
                else:
                    self.wselect += "ope_peche_elec.opep_longueur_prospec AS \"LONGUEUR\""

            if self.chkProfondeur.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_profondeur_moy AS \"PROFONDEUR\""
                else:
                    self.wselect += "ope_peche_elec.opep_profondeur_moy AS \"PROFONDEUR\""

            if self.chkLargeurPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_largeur_moy AS \"LARGEUR\""
                else:
                    self.wselect += "ope_peche_elec.opep_largeur_moy AS \"LARGEUR\""

            if self.chkSurfacePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_surf_peche AS \"SURFACE\""
                else:
                    self.wselect += "ope_peche_elec.opep_surf_peche AS \"SURFACE\""

            if self.chkPente.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_pente AS \"PENTE\""
                else:
                    self.wselect += "ope_peche_elec.opep_pente AS \"PENTE\""

            if self.chkXYPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_xl93_aval AS \"X (L93)\""
                else:
                    self.wselect += "station.sta_xl93_aval AS \"X (L93)\""

            if self.chkXYPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_yl93_aval AS \"Y (L93)\""
                else:
                    self.wselect += "station.sta_yl93_aval AS \"Y (L93)\""

            if self.chkDistancePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_distance_source AS \"DISTANCE SOURCE\""
                else:
                    self.wselect += "station.sta_distance_source AS \"DISTANCE SOURCe\""

            if self.chkAltitudePeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_altitude AS \"ALTITUDE\""
                else:
                    self.wselect += "station.sta_altitude AS \"ALTITUDE\""

            if self.chkSurfBVPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", station.sta_surf_bv_amont AS \"SURFACE BV AMONT\""
                else:
                    self.wselect += "station.sta_surf_bv_amont AS \"SURFACE BV AMONT\""

            if self.chkMotif.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", motif_peche.mope_motif AS \"MOTIF\""
                else:
                    self.wselect += "motif_peche.mope_motif AS \"MOTIF\""

            if self.chkCondition.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", condition_peche.cope_condition AS \"CONDITION\""
                else:
                    self.wselect += "condition_peche.cope_condition AS \"CONDITION\""

            if self.chkIpr.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.ipro_valeur AS \"IPR\""
                else:
                    self.wselect += "ope_peche_elec.ipro_valeur AS \"IPR\""

            if self.chkIprCorrespond.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ipr.ipr_correspondance AS \"CORRES IPR\""
                else:
                    self.wselect += "ipr.ipr_correspondance AS \"CORRES IPR\""

            if self.chkNtt.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_ntt AS \"NTT\""
                else:
                    self.wselect += "ope_peche_elec.opep_ntt AS \"NTT\""

            if self.chkNttReel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_ntt_reel AS \"NTT REEL\""
                else:
                    self.wselect += "ope_peche_elec.opep_ntt_reel AS \"NTT REEL\""

            if self.chkEspece.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", string_agg(espece.esp_sigle, ', '::text) AS \"ESPECE\""
                else:
                    self.wselect += "string_agg(espece.esp_sigle, ', '::text) AS \"ESPECE\""

            if self.chkBiomasse.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", placementBiomasse"
                else:
                    self.wselect += "placementBiomasse"

            if self.chkBioCorrespond.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", placementCorrespondanceBiomasse"
                else:
                    self.wselect += "placementCorrespondanceBiomasse"

            if self.chkDensite.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", placementDensite"
                else:
                    self.wselect += "placementDensite"

            if self.chkDenCorrespond.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", placementCorrespondanceDensite"
                else:
                    self.wselect += "placementCorrespondanceDensite"

            if self.chkObservationPeche.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_peche_elec.opep_observation AS \"OBSERVATION\""
                else:
                    self.wselect += "ope_peche_elec.opep_observation AS \"OBSERVATION\""

        elif self.tabWidget.currentIndex() == 2:
            self.wselect = ""
            self.cfrom = ""
            self.wwhereSelect = ""
            self.cfrom = "data.ope_suivi_thermi, data.operation, data.station, data.masse_eau, data.contexte_pdpg, data.cours_eau, data.aappma, data.real_suivi_thermi, data.maitre_ouvrage"
            self.wwhereSelect = ("ope_code = opest_ope_code and opest_id = rst_opest_id and rst_moa_id = moa_id and ope_sta_id = sta_id and sta_meau_code = meau_code " +
            "and sta_pdpg_id = pdpg_id and sta_ceau_id = ceau_id and sta_apma_id = apma_id")

            if self.chkCeauThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ceau_nom AS \"COURS D'EAU\""
                else:
                    self.wselect += "ceau_nom AS \"COURS D'EAU\""

            if self.chkDateDebut.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_date_debut AS \"DATE DE DEBUT\""
                else:
                    self.wselect += "opest_date_debut AS \"DATE DE DEBUt\""

            if self.chkDateFin.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_date_fin AS \"DATE DE FIN\""
                else:
                    self.wselect += "opest_date_fin AS \"DATE DE FIN\""

            if self.chkDuree.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_duree AS \"DUREE\""
                else:
                    self.wselect += "opest_duree AS \"DUREE\""

            if self.chkCodeThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_code AS \"CODE OPERATION\""
                else:
                    self.wselect += "ope_code AS \"CODE OPERATION\""

            if self.chkMeauThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", meau_nom AS \"MASSE D'EAU\""
                else:
                    self.wselect += "meau_nom AS \"MASSE D'EAU\""

            if self.chkMeauCodeThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", meau_code AS \"CODE MASSE D'EAU\""
                else:
                    self.wselect += "meau_code AS \"CODE MASSE D'EAU\""

            if self.chkPdpgThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pdpg_code AS \"PDPG\""
                else:
                    self.wselect += "pdpg_code AS \"PDPG\""

            if self.chkAappmaThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", apma_nom AS \"AAPPMA\""
                else:
                    self.wselect += "apma_nom AS \"AAPPMA\""

            if self.chkStationThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_nom AS \"STATION\""
                else:
                    self.wselect += "sta_nom AS \"STATION\""

            if self.chkMoaThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", moa_nom AS \"MAITRE D'OUVRAGE\""
                else:
                    self.wselect += "moa_nom AS \"MAITRE D'OUVRAGE\""

            if self.chkXYSondeThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ST_X(opest_geom) AS \"SONDE X (L93)\""
                else:
                    self.wselect += "ST_X(opest_geom) AS \"SONDE X (L93)\""

            if self.chkXYSondeThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ST_Y(opest_geom) AS \"SONDE Y (L93)\""
                else:
                    self.wselect += "ST_Y(opest_geom) AS \"SONDE Y (L93)\""

            if self.chkXYStationThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_xl93_aval AS \"STATION X (L93)\""
                else:
                    self.wselect += "sta_xl93_aval AS \"STATION X (L93)\""

            if self.chkXYStationThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_yl93_aval AS \"STATION Y (L93)\""
                else:
                    self.wselect += "sta_yl93_aval AS \"STATION Y (L93)\""

            if self.chkDistanceThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_distance_source AS \"DISTANCE SOURCE\""
                else:
                    self.wselect += "sta_distance_source AS \"DISTANCE SOURCE\""

            if self.chkAltitudeThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_altitude AS \"ALTITUDE\""
                else:
                    self.wselect += "sta_altitude AS \"ALTITUDE\""

            if self.chkSurfBVThermi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_surf_bv_amont AS \"SURFACE BV AMONT\""
                else:
                    self.wselect += "sta_surf_bv_amont AS \"SURFACE BV AMONT\""

            if self.chkTimin.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_ti_min AS \"TI MIN\""
                else:
                    self.wselect += "opest_ti_min AS \"TI MIN\""

            if self.chkTimax.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_ti_max AS \"TI MAX\""
                else:
                    self.wselect += "opest_ti_max AS \"TI MAX\""

            if self.chkAjmaxTi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_ajmax_ti AS \"AJMAX TI\""
                else:
                    self.wselect += "opest_ajmax_ti AS \"AJMAX TI\""

            if self.chkDAjmaxTi.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_d_ajmax_ti AS \"DATE AJMAX TI\""
                else:
                    self.wselect += "opest_d_ajmax_ti AS \"DATE AJMAX TI\""

            if self.chkTmjMin.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_tmj_min AS \"TMJ MIN\""
                else:
                    self.wselect += "opest_tmj_min AS \"TMJ MIN\""

            if self.chkTmjMax.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_tmj_max AS \"TMJ MAX\""
                else:
                    self.wselect += "opest_tmj_max AS \"TMJ MAX\""

            if self.chkTmpMoy.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_tmp_moy AS \"TMP MOY\""
                else:
                    self.wselect += "opest_tmp_moy AS \"TMP MOY\""

            if self.chkTmj30Max.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_tm30j_max AS \"TMJ 30 MAX\""
                else:
                    self.wselect += "opest_tm30j_max AS \"TMJ 30 MAX\""

            if self.chkNbjTmj419.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbj_tmj_4_19 AS \"NBJ TMJ 4-19\""
                else:
                    self.wselect += "opest_nbj_tmj_4_19 AS \"NBJ TMJ 4-19\""

            if self.chkP100Tmj419.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_p100j_tmj_4_19 AS \"%J TMJ 4-19\""
                else:
                    self.wselect += "opest_p100j_tmj_4_19 AS \"%J TMJ 4-19\""

            if self.chkP100TmjInf4.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_p100_tmj_inf_4 AS \"% TMJ <4\""
                else:
                    self.wselect += "opest_p100_tmj_inf_4 AS \"% TMJ <4\""

            if self.chkP100TmjSup19.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_p100_tmj_sup_19 AS \"% TMJ >19\""
                else:
                    self.wselect += "opest_p100_tmj_sup_19 AS \"% TMJ >19\""

            if self.chkNbMaxTiCsfSup19.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbmax_ti_csf_sup19 AS \"NBMAX TI CSF >19\""
                else:
                    self.wselect += "opest_nbmax_ti_csf_sup19 AS \"NBMAX TI CSF >19\""

            if self.chkNbMaxTiCsfSupEg25.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbmax_ti_csf_sup_eg25 AS \"NBMAX TI CSF >=25\""
                else:
                    self.wselect += "opest_nbmax_ti_csf_sup_eg25 AS \"NBMAX TI CSF >=25\""

            if self.chkNbMaxTiCsfSupEg15.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbmax_ti_csf_sup_eg15 AS \"NBMAX TI CSF >=15\""
                else:
                    self.wselect += "opest_nbmax_ti_csf_sup_eg15 AS \"NBMAX TI CSF >=15\""

            if self.chkD50Ponte.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_d50_ponte AS \"DATE MEDIANE DE PONTE\""
                else:
                    self.wselect += "opest_d50_ponte AS \"DATE MEDIANE DE PONTE\""

            if self.chkNbjIncub.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbj_incub AS \"NBJ D'INCUBATION\""
                else:
                    self.wselect += "opest_nbj_incub AS \"NBJ D'INCUBATION\""

            if self.chkD50Eclo.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_d50_eclo AS \"DATE MEDIANE D'ECLOSION\""
                else:
                    self.wselect += "opest_d50_eclo AS \"DATE MEDIANE D'ECLOSION\""

            if self.chkNbjRsp.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbj_rsp AS \"NBJ DE RESORPTION\""
                else:
                    self.wselect += "opest_nbj_rsp AS \"NBJ DE RESORPTION\""

            if self.chkD50Emg.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_d50_emg AS \"DATE MEDIANE D'EMERGENCE\""
                else:
                    self.wselect += "opest_d50_emg AS \"DATE MEDIANE D'EMERGENCE\""

            if self.chkNbjPel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbj_pel AS \"NBJ PEL\""
                else:
                    self.wselect += "opest_nbj_pel AS \"NBJ PEL\""

            if self.chkNbTiSup15Pel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nb_ti_sup15_pel AS \"NB TI >15 PEL\""
                else:
                    self.wselect += "opest_nb_ti_sup15_pel AS \"NB TI >15 PEL\""

            if self.chkNbMaxTiCsfSup15Pel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbmax_ti_csf_sup15_pel AS \"NBMAX TI CSF >15 PEL\""
                else:
                    self.wselect += "opest_nbmax_ti_csf_sup15_pel AS \"NBMAX TI CSF >15 PEL\""

            if self.chkNbTiInf15Pel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nb_ti_inf_1_5pel AS \"NB TI <1.5 PEL\""
                else:
                    self.wselect += "opest_nb_ti_inf_1_5pel AS \"NB TI <1.5 PEL\""

            if self.chkNbMaxTiCsfInf15Pel.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opest_nbmax_ti_csf_inf1_5_pel AS \"NBMAX TI CSF <1.5 PEL\""
                else:
                    self.wselect += "opest_nbmax_ti_csf_inf1_5_pel AS \"NBMAX TI CSF <1.5 PEL\""

        elif self.tabWidget.currentIndex() == 3:
            self.wselect = ""
            self.cfrom = ""
            self.wwhereSelect = ""
            self.cfrom = ("data.ope_inventaire_repro, data.operation, data.station, data.masse_eau, data.contexte_pdpg, data.cours_eau, data.aappma, " +
            "data.baran_s_zfp, data.real_inventaire, data.maitre_ouvrage")
            self.wwhereSelect = ("ope_code = opeir_ope_code and opeir_baran_id = baran_id and opeir_id = ri_opeir_id and ri_moa_id = moa_id and ope_sta_id = sta_id " +
            "and sta_meau_code = meau_code and sta_pdpg_id = pdpg_id and sta_ceau_id = ceau_id and sta_apma_id = apma_id")

            if self.chkCeauRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ceau_nom AS \"COURS D'EAU\""
                else:
                    self.wselect += "ceau_nom AS \"COURS D'EAU\""

            if self.chkDateRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_date AS \"DATE\""
                else:
                    self.wselect += "opeir_date AS \"DATE\""

            if self.chkCodeRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ope_code AS \"CODE OPERATION\""
                else:
                    self.wselect += "ope_code AS \"CODE OPERATION\""

            if self.chkMeauRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", meau_nom AS \"MASSE D'EAU\""
                else:
                    self.wselect += "meau_nom AS \"MASSE D'EAU\""

            if self.chkMeauCodeRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", meau_code AS \"CODE MASSE D'EAU\""
                else:
                    self.wselect += "meau_code AS \"CODE MASSE D'EAU\""

            if self.chkPdpgRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", pdpg_code AS \"PDPG\""
                else:
                    self.wselect += "pdpg_code AS \"PDPG\""

            if self.chkAappmaRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", apma_nom AS \"AAPPMA\""
                else:
                    self.wselect += "apma_nom AS \"AAPPMA\""

            if self.chkStationRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_nom AS \"STATION\""
                else:
                    self.wselect += "sta_nom AS \"STATION\""

            if self.chkMoaRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", moa_nom AS \"MAITRE D'OUVRAGE\""
                else:
                    self.wselect += "moa_nom AS \"MAITRE D'OUVRAGE\""

            if self.chkPassage.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_nbre_passage AS \"NBRE DE PASSAGE\""
                else:
                    self.wselect += "opeir_nbre_passage AS \"NBRE DE PASSAGE\""

            if self.chkLongueurRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_longueur AS \"LONGUEUR\""
                else:
                    self.wselect += "opeir_longueur AS \"LONGUEUR\""

            if self.chkLargeurRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_largeur_moy AS \"LARGEUR MOYENNE\""
                else:
                    self.wselect += "opeir_largeur_moy AS \"LARGEUR MOYENNE\""

            if self.chkXYAvalRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ST_X(ST_StartPoint(ST_GeometryN(ST_Multi(opeir_geom),1))) AS \"PT AVAL X (L93)\""
                else:
                    self.wselect += "ST_X(ST_StartPoint(ST_GeometryN(ST_Multi(opeir_geom),1))) AS \"PT AVAL X (L93)\""

            if self.chkXYAvalRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", ST_Y(ST_StartPoint(ST_GeometryN(ST_Multi(opeir_geom),1))) AS \"PT AVAL Y (L93)\""
                else:
                    self.wselect += "ST_Y(ST_StartPoint(ST_GeometryN(ST_Multi(opeir_geom),1))) AS \"PT AVAL Y (L93)\""

            if self.chkXYStationRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_xl93_aval AS \"STATION X (L93)\""
                else:
                    self.wselect += "sta_xl93_aval AS \"STATION X (L93)\""

            if self.chkXYStationRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_yl93_aval AS \"STATION Y (L93)\""
                else:
                    self.wselect += "sta_yl93_aval AS \"STATION Y (L93)\""

            if self.chkDistanceRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_distance_source AS \"DISTANCE SOURCE\""
                else:
                    self.wselect += "sta_distance_source AS \"DISTANCE SOURCE\""

            if self.chkAltitudeRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_altitude AS \"ALTITUDE\""
                else:
                    self.wselect += "sta_altitude AS \"ALTITUDE\""

            if self.chkSurfBVRepro.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", sta_surf_bv_amont AS \"SURFACE BV AMONT\""
                else:
                    self.wselect += "sta_surf_bv_amont AS \"SURFACE BV AMONT\""

            if self.chkSgf.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_sgf AS \"SGF\""
                else:
                    self.wselect += "opeir_sgf AS \"SGF\""

            if self.chkZfp.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_zfp AS \"ZFP\""
                else:
                    self.wselect += "opeir_zfp AS \"ZFP\""

            if self.chkFrayere.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_nbre_frayere AS \"NBRE DE FRAYERE\""
                else:
                    self.wselect += "opeir_nbre_frayere AS \"NBRE DE FRAYERE\""

            if self.chkSurfaceFrayere.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", opeir_surf_fray AS \"SURFACE DE FRAYERE\""
                else:
                    self.wselect += "opeir_surf_fray AS \"SURFACE DE FRAYERE\""

            if self.chkBaran.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", barope_valeur AS \"BARAN\""
                else:
                    self.wselect += "barope_valeur AS \"BARAN\""

            if self.chkBaranCorrespond.isChecked() == True :
                if self.wselect != "" :
                    self.wselect += ", baran_correspond AS \"CORRES Baran\""
                else:
                    self.wselect += "baran_correspond AS \"CORRES Baran\""

        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

        if self.wselect == "" :
            self.clauseSelect = False
        else:
            self.clauseSelect = True

    def ajoutPossession(self):
        '''Change l'état des boutons et ajoute un critère de possession à la requête'''

        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.possessionBool = True

        if self.chkBopePossede.isChecked() == True:
            self.wwherePossession = "bope_existe = True"
        else:
            self.wwherePossession = "bope_existe = False"

        self.wwhere += self.wwherePossession

    def ajoutCommune(self):
        '''Change l'état des boutons et ajoute un critère d'id à la requête'''

        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.communeBool = True

        wrecord = self.cmbBopeCommune.model().record(self.cmbBopeCommune.currentIndex())
        self.wbope_commune = wrecord.value(0)
        if self.cmbBopeCommune.currentText() != "":
            if self.wbope_commune != "":
                self.wwhere += "bope_id in (select bope_id from data.droit_peche, data.parcelle, data.section where bope_id = par_bope_id and par_sec_id = sec_id and sec_com_insee = '" + str(self.wbope_commune) +"')"

    def ajoutAappma(self):
        '''Change l'état des boutons et ajoute un critère d'aappma à la requête'''

        if self.tabWidget.currentIndex() == 0:
            self.btnBopeEt.setEnabled(True)
            self.btnBopeOu.setEnabled(True)

            self.btnBopePossede.setEnabled(False)
            self.btnBopeCommune.setEnabled(False)
            self.btnBopeAappma.setEnabled(False)
            self.btnBopeCeau.setEnabled(False)
            self.btnBopeSign.setEnabled(False)
            self.btnBopeFin.setEnabled(False)
            self.btnProprio.setEnabled(False)
            self.btnAdresse.setEnabled(False)

            self.aappmaBool = True

            wrecord = self.cmbBopeAappma.model().record(self.cmbBopeAappma.currentIndex())
            self.wbope_aappma = wrecord.value(0)
            if self.cmbBopeAappma.currentText() != "":
                if self.wbope_aappma != "":
                    self.wwhere += "bope_apma_id = '" + str(self.wbope_aappma) + "'"

        elif self.tabWidget.currentIndex() == 1:
            self.btnPecheEt.setEnabled(True)
            self.btnPecheOu.setEnabled(True)

            self.btnPecheAappma.setEnabled(False)
            self.btnPechePdpg.setEnabled(False)
            self.btnPecheCeau.setEnabled(False)
            self.btnPecheMeau.setEnabled(False)
            self.btnPecheAnnee.setEnabled(False)
            self.btnPecheEspece.setEnabled(False)

            self.aappmaBool = True

            wrecord = self.cmbPecheAappma.model().record(self.cmbPecheAappma.currentIndex())
            self.wpeche_aappma = wrecord.value(0)
            if self.cmbPecheAappma.currentText() != "":
                if self.wpeche_aappma != "":
                    self.wwhere += "opep_id in (select opep_id from data.ope_peche_elec, data.operation, data.station, data.aappma where opep_ope_code = ope_code and ope_sta_id = sta_id and sta_apma_id = '" + str(self.wpeche_aappma) + "')"

        elif self.tabWidget.currentIndex() == 2:
            self.btnThermiEt.setEnabled(True)
            self.btnThermiOu.setEnabled(True)

            self.btnThermiAappma.setEnabled(False)
            self.btnThermiPdpg.setEnabled(False)
            self.btnThermiCeau.setEnabled(False)
            self.btnThermiMeau.setEnabled(False)
            self.btnThermiAnnee.setEnabled(False)

            self.aappmaBool = True

            wrecord = self.cmbThermiAappma.model().record(self.cmbThermiAappma.currentIndex())
            self.wthermi_aappma = wrecord.value(0)
            if self.cmbThermiAappma.currentText() != "":
                if self.wthermi_aappma != "":
                    self.wwhere += "opest_id in (select opest_id from data.ope_suivi_thermi, data.operation, data.station, data.aappma where opest_ope_code = ope_code and ope_sta_id = sta_id and sta_apma_id = '" + str(self.wthermi_aappma) + "')"

        elif self.tabWidget.currentIndex() == 3:
            self.btnReproEt.setEnabled(True)
            self.btnReproOu.setEnabled(True)

            self.btnReproAappma.setEnabled(False)
            self.btnReproPdpg.setEnabled(False)
            self.btnReproCeau.setEnabled(False)
            self.btnReproMeau.setEnabled(False)
            self.btnReproAnnee.setEnabled(False)

            self.aappmaBool = True

            wrecord = self.cmbReproAappma.model().record(self.cmbReproAappma.currentIndex())
            self.wrepro_aappma = wrecord.value(0)
            if self.cmbReproAappma.currentText() != "":
                if self.wrepro_aappma != "":
                    self.wwhere += "opeir_id in (select opeir_id from data.ope_inventaire_repro, data.operation, data.station, data.aappma where opeir_ope_code = ope_code and ope_sta_id = sta_id and sta_apma_id = '" + str(self.wrepro_aappma) + "')"
        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

    def ajoutCeau(self):
        '''Change l'état des boutons et ajoute un critère de cours d'eau à la requête'''

        if self.tabWidget.currentIndex() == 0:
            self.btnBopeEt.setEnabled(True)
            self.btnBopeOu.setEnabled(True)

            self.btnBopePossede.setEnabled(False)
            self.btnBopeCommune.setEnabled(False)
            self.btnBopeAappma.setEnabled(False)
            self.btnBopeCeau.setEnabled(False)
            self.btnBopeSign.setEnabled(False)
            self.btnBopeFin.setEnabled(False)
            self.btnProprio.setEnabled(False)
            self.btnAdresse.setEnabled(False)

            wfrombce = "bail_cours_eau"
            if self.dbType == "postgres":
                self.wfromCeau = self.dbSchema + "." + wfrombce

            wrecord = self.cmbBopeCeau.model().record(self.cmbBopeCeau.currentIndex())
            self.wbope_ceau = wrecord.value(0)
            if self.cmbBopeCeau.currentText() != "":
                if self.wbope_ceau != "":
                    self.wwhere += "bope_id in (select distinct bce_bope_id from " + self.wfromCeau + " where bce_ceau_id = '" + str(self.wbope_ceau) + "')"

        elif self.tabWidget.currentIndex() == 1:
            self.btnPecheEt.setEnabled(True)
            self.btnPecheOu.setEnabled(True)

            self.btnPecheAappma.setEnabled(False)
            self.btnPechePdpg.setEnabled(False)
            self.btnPecheCeau.setEnabled(False)
            self.btnPecheMeau.setEnabled(False)
            self.btnPecheAnnee.setEnabled(False)
            self.btnPecheEspece.setEnabled(False)

            self.ceauBool = True

            wrecord = self.cmbPecheCeau.model().record(self.cmbPecheCeau.currentIndex())
            self.wpeche_ceau = wrecord.value(0)
            if self.cmbPecheCeau.currentText() != "":
                if self.wpeche_ceau != "":
                    self.wwhere += "opep_id in (select opep_id from data.ope_peche_elec, data.operation, data.station, data.cours_eau where opep_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = '" + str(self.wpeche_ceau) + "')"

        elif self.tabWidget.currentIndex() == 2:
            self.btnThermiEt.setEnabled(True)
            self.btnThermiOu.setEnabled(True)

            self.btnThermiAappma.setEnabled(False)
            self.btnThermiPdpg.setEnabled(False)
            self.btnThermiCeau.setEnabled(False)
            self.btnThermiMeau.setEnabled(False)
            self.btnThermiAnnee.setEnabled(False)

            self.ceauBool = True

            wrecord = self.cmbThermiCeau.model().record(self.cmbThermiCeau.currentIndex())
            self.wthermi_ceau = wrecord.value(0)
            if self.cmbThermiCeau.currentText() != "":
                if self.wthermi_ceau != "":
                    self.wwhere += "opest_id in (select opest_id from data.ope_suivi_thermi, data.operation, data.station, data.cours_eau where opest_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = '" + str(self.wthermi_ceau) + "')"

        elif self.tabWidget.currentIndex() == 3:
            self.btnReproEt.setEnabled(True)
            self.btnReproOu.setEnabled(True)

            self.btnReproAappma.setEnabled(False)
            self.btnReproPdpg.setEnabled(False)
            self.btnReproCeau.setEnabled(False)
            self.btnReproMeau.setEnabled(False)
            self.btnReproAnnee.setEnabled(False)

            self.ceauBool = True

            wrecord = self.cmbReproCeau.model().record(self.cmbReproCeau.currentIndex())
            self.wrepro_ceau = wrecord.value(0)
            if self.cmbReproCeau.currentText() != "":
                if self.wrepro_ceau != "":
                    self.wwhere += "opeir_id in (select opeir_id from data.ope_inventaire_repro, data.operation, data.station, data.cours_eau where opeir_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = '" + str(self.wrepro_ceau) + "')"
        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

    def ajoutPdpg(self):
        '''Change l'état des boutons et ajoute un critère de pdpg à la requête'''

        if self.tabWidget.currentIndex() == 1:
            self.btnPecheEt.setEnabled(True)
            self.btnPecheOu.setEnabled(True)

            self.btnPecheAappma.setEnabled(False)
            self.btnPechePdpg.setEnabled(False)
            self.btnPecheCeau.setEnabled(False)
            self.btnPecheMeau.setEnabled(False)
            self.btnPecheAnnee.setEnabled(False)
            self.btnPecheEspece.setEnabled(False)

            self.pdpgBool = True

            wrecord = self.cmbPechePdpg.model().record(self.cmbPechePdpg.currentIndex())
            self.wpeche_pdpg = wrecord.value(0)
            if self.cmbPechePdpg.currentText() != "":
                if self.wpeche_pdpg != "":
                    self.wwhere += "opep_id in (select opep_id from data.ope_peche_elec, data.operation, data.station, data.contexte_pdpg where opep_ope_code = ope_code and ope_sta_id = sta_id and sta_pdpg_id = '" + str(self.wpeche_pdpg) + "')"

        elif self.tabWidget.currentIndex() == 2:
            self.btnThermiEt.setEnabled(True)
            self.btnThermiOu.setEnabled(True)

            self.btnThermiAappma.setEnabled(False)
            self.btnThermiPdpg.setEnabled(False)
            self.btnThermiCeau.setEnabled(False)
            self.btnThermiMeau.setEnabled(False)
            self.btnThermiAnnee.setEnabled(False)

            self.pdpgBool = True

            wrecord = self.cmbThermiPdpg.model().record(self.cmbThermiPdpg.currentIndex())
            self.wthermi_pdpg = wrecord.value(0)
            if self.cmbThermiPdpg.currentText() != "":
                if self.wthermi_pdpg != "":
                    self.wwhere += "opest_id in (select opest_id from data.ope_suivi_thermi, data.operation, data.station, data.contexte_pdpg where opest_ope_code = ope_code and ope_sta_id = sta_id and sta_pdpg_id = '" + str(self.wthermi_pdpg) + "')"

        elif self.tabWidget.currentIndex() == 3:
            self.btnReproEt.setEnabled(True)
            self.btnReproOu.setEnabled(True)

            self.btnReproAappma.setEnabled(False)
            self.btnReproPdpg.setEnabled(False)
            self.btnReproCeau.setEnabled(False)
            self.btnReproMeau.setEnabled(False)
            self.btnReproAnnee.setEnabled(False)

            self.pdpgBool = True

            wrecord = self.cmbReproPdpg.model().record(self.cmbReproPdpg.currentIndex())
            self.wrepro_pdpg = wrecord.value(0)
            if self.cmbReproPdpg.currentText() != "":
                if self.wrepro_pdpg != "":
                    self.wwhere += "opeir_id in (select opeir_id from data.ope_inventaire_repro, data.operation, data.station, data.contexte_pdpg where opeir_ope_code = ope_code and ope_sta_id = sta_id and sta_pdpg_id = '" + str(self.wrepro_pdpg) + "')"
        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

    def ajoutMeau(self):
        '''Change l'état des boutons et ajoute un critère de masse d'eau à la requête'''

        if self.tabWidget.currentIndex() == 1:
            self.btnPecheEt.setEnabled(True)
            self.btnPecheOu.setEnabled(True)

            self.btnPecheAappma.setEnabled(False)
            self.btnPechePdpg.setEnabled(False)
            self.btnPecheCeau.setEnabled(False)
            self.btnPecheMeau.setEnabled(False)
            self.btnPecheAnnee.setEnabled(False)
            self.btnPecheEspece.setEnabled(False)

            self.meauBool = True

            wrecord = self.cmbPecheMeau.model().record(self.cmbPecheMeau.currentIndex())
            self.wpeche_meau = wrecord.value(0)
            if self.cmbPecheMeau.currentText() != "":
                if self.wpeche_meau != "":
                    self.wwhere += "opep_id in (select opep_id from data.ope_peche_elec, data.operation, data.station, data.cours_eau where opep_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = ceau_id and sta_meau_code = '" + str(self.wpeche_meau) + "')"

        elif self.tabWidget.currentIndex() == 2:
            self.btnThermiEt.setEnabled(True)
            self.btnThermiOu.setEnabled(True)

            self.btnThermiAappma.setEnabled(False)
            self.btnThermiPdpg.setEnabled(False)
            self.btnThermiCeau.setEnabled(False)
            self.btnThermiMeau.setEnabled(False)
            self.btnThermiAnnee.setEnabled(False)

            self.meauBool = True

            wrecord = self.cmbThermiMeau.model().record(self.cmbThermiMeau.currentIndex())
            self.wthermi_meau = wrecord.value(0)
            if self.cmbThermiMeau.currentText() != "":
                if self.wthermi_meau != "":
                    self.wwhere += "opest_id in (select opest_id from data.ope_suivi_thermi, data.operation, data.station, data.cours_eau where opest_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = ceau_id and sta_meau_code = '" + str(self.wthermi_meau) + "')"

        elif self.tabWidget.currentIndex() == 3:
            self.btnReproEt.setEnabled(True)
            self.btnReproOu.setEnabled(True)

            self.btnReproAappma.setEnabled(False)
            self.btnReproPdpg.setEnabled(False)
            self.btnReproCeau.setEnabled(False)
            self.btnReproMeau.setEnabled(False)
            self.btnReproAnnee.setEnabled(False)

            self.meauBool = True

            wrecord = self.cmbReproMeau.model().record(self.cmbReproMeau.currentIndex())
            self.wrepro_meau = wrecord.value(0)
            if self.cmbReproMeau.currentText() != "":
                if self.wrepro_meau != "":
                    self.wwhere += "opeir_id in (select opeir_id from data.ope_inventaire_repro, data.operation, data.station, data.cours_eau where opeir_ope_code = ope_code and ope_sta_id = sta_id and sta_ceau_id = ceau_id and sta_meau_code =  '" + str(self.wrepro_meau) + "')"
        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

    def ajoutAnnee(self):
        '''Change l'état des boutons et ajoute un critère d'année à la requête'''

        if self.tabWidget.currentIndex() == 1:
            self.btnPecheEt.setEnabled(True)
            self.btnPecheOu.setEnabled(True)

            self.btnPecheAappma.setEnabled(False)
            self.btnPechePdpg.setEnabled(False)
            self.btnPecheCeau.setEnabled(False)
            self.btnPecheMeau.setEnabled(False)
            self.btnPecheAnnee.setEnabled(False)
            self.btnPecheEspece.setEnabled(False)

            self.anneeBool = True

            self.wpeche_date = self.datePecheAnnee.date().toString("yyyy")
            if self.wpeche_date != "":
                self.wwhere += "date_part('year', opep_date) = '" + str(self.wpeche_date) + "'"

        elif self.tabWidget.currentIndex() == 2:
            self.btnThermiEt.setEnabled(True)
            self.btnThermiOu.setEnabled(True)

            self.btnThermiAappma.setEnabled(False)
            self.btnThermiPdpg.setEnabled(False)
            self.btnThermiCeau.setEnabled(False)
            self.btnThermiMeau.setEnabled(False)
            self.btnThermiAnnee.setEnabled(False)

            self.anneeBool = True

            self.wthermi_date = self.dateThermiAnnee.date().toString("yyyy")
            if self.wthermi_date != "":
                self.wwhere += "date_part('year', opest_date_debut) = '" + str(self.wthermi_date) + "'"

        elif self.tabWidget.currentIndex() == 3:
            self.btnReproEt.setEnabled(True)
            self.btnReproOu.setEnabled(True)

            self.btnReproAappma.setEnabled(False)
            self.btnReproPdpg.setEnabled(False)
            self.btnReproCeau.setEnabled(False)
            self.btnReproMeau.setEnabled(False)
            self.btnReproAnnee.setEnabled(False)

            self.anneeBool = True

            self.wrepro_date = self.dateReproAnnee.date().toString("yyyy")
            if self.wrepro_date != "":
                self.wwhere += "opeir_date ilike '%" + str(self.wrepro_date) + "%'"
        else :
            QMessageBox.critical(self, "Erreur", u"Aucun index valide...", QMessageBox.Ok)

    def ajoutEspece(self):
        '''Change l'état des boutons et ajoute un critère d'espèce à la requête'''

        self.btnPecheEt.setEnabled(True)
        self.btnPecheOu.setEnabled(True)

        self.btnPecheAappma.setEnabled(False)
        self.btnPechePdpg.setEnabled(False)
        self.btnPecheCeau.setEnabled(False)
        self.btnPecheMeau.setEnabled(False)
        self.btnPecheAnnee.setEnabled(False)
        self.btnPecheEspece.setEnabled(False)

        wrecord = self.cmbPecheEspece.model().record(self.cmbPecheEspece.currentIndex())
        self.wpeche_espece = wrecord.value(0)
        if self.cmbPecheEspece.currentText() != "":
            if self.wpeche_espece != "":
                self.wwhere += "opep_id in (select espe_opep_id from data.espece_peche where espe_esp_id = '" + str(self.wpeche_espece) +"')"

    def ajoutDateSign(self):
        '''Change l'état des boutons et ajoute un critère de date de signature à la requête'''

        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.anneeSignBool = True

        self.wbope_date_sign = self.dateBopeSign.date().toString("yyyy")
        if self.wbope_date_sign != "":
            self.wwhere += "date_part('year', bope_date_sign) = '" + str(self.wbope_date_sign) + "'"

    def ajoutDateFin(self):
        '''Change l'état des boutons et ajoute un critère de date d'expiration à la requête'''

        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.anneeFinBool = True

        self.wbope_date_fin = self.dateBopeFin.date().toString("yyyy")
        if self.wbope_date_fin != "":
            self.wwhere += "date_part('year', bope_date_fin) = '" + str(self.wbope_date_fin) + "'"

    def ajoutProprio(self):
        '''
        Change l'état des boutons et ajoute un critère de nom de propriétaire
        et / ou de mail
        et / ou de téléphone à la requête
        '''
        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.wwhereProprio = ""
        self.wnom = self.leNom.text()
        if "'" in self.wnom and "''" not in self.wnom:
            self.wnom = self.wnom.replace("'", "''")
        self.wmail = self.leMail.text()
        self.wtel = self.leTel.text()
        if self.leNom.text() != "":
            if self.wnom != "":
                self.wwhereProprio += " bope_id in (select bope_id from data.droit_peche, data.proprietaire where bope_pro_id = pro_id and pro_nom ilike '%" + self.wnom + "%')"
        if self.leMail.text() != "":
            if self.wmail != "":
                if self.wnom != "":
                    self.wwhereProprio += " and "
                self.wwhereProprio += " bope_id in (select bope_id from data.droit_peche, data.proprietaire where bope_pro_id = pro_id and pro_mail = '" + self.wmail + "')"
        if self.leTel.text() != "":
            if self.wtel != "":
                if self.wnom != "" or self.wmail != "":
                    self.wwhereProprio += " and "
                self.wwhereProprio += " bope_id in (select bope_id from data.droit_peche, data.proprietaire where bope_pro_id = pro_id and pro_telephone = '" + str(self.wtel) + "')"

        if self.wwhereProprio != "":
            self.wwhere += self.wwhereProprio

        self.leNom.setText("")
        self.leMail.setText("")
        self.leTel.setText("")
        self.leNom.setFocus()

    def ajoutAdresse(self):
        '''Change l'état des boutons et ajoute un critère d'adresse à la requête'''

        self.btnBopeEt.setEnabled(True)
        self.btnBopeOu.setEnabled(True)

        self.btnBopePossede.setEnabled(False)
        self.btnBopeCommune.setEnabled(False)
        self.btnBopeAappma.setEnabled(False)
        self.btnBopeCeau.setEnabled(False)
        self.btnBopeSign.setEnabled(False)
        self.btnBopeFin.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.wadresse = self.leAdresse.text()
        if "'" in self.wadresse and "''" not in self.wadresse:
            self.wadresse = self.wadresse.replace("'", "''")
        if self.leAdresse.text() != "" :
            if self.wadresse != "" :
                self.wwhere += " bope_id in (select distinct bope_id from data.droit_peche, data.proprietaire where (bope_pro_id = pro_id ) and (pro_adresse ilike '%" + self.wadresse + "%'))"
        else :
            if self.leAdresse.text() == "":
                if  self.wadresse == "":
                    self.wwhere += " bope_id in (select distinct bope_id from data.droit_peche, data.proprietaire where (bope_pro_id = pro_id )"

        self.leAdresse.setText("")
        self.leAdresse.setFocus()

    def creaRequete(self):
        '''Regroupe les différentes variables contenant les clauses de la requête SQL et les concatène pour en faire une requête exécutable'''

        self.ajoutSelect()

        if self.tabWidget.currentIndex() == 1 and (self.chkBiomasse.isChecked() == True or self.chkBioCorrespond.isChecked() == True or self.chkDensite.isChecked() == True or self.chkDenCorrespond.isChecked() == True):
            prewwhere = self.wwhere
            prewwhereSelect = self.wwhereSelect
            self.wgroupBy = ""
            dicoEspece = {}
            prewrq = ""
            prewrq = "SELECT DISTINCT esp_id, esp_sigle FROM " + self.cfrom

            if prewwhere != "":
                #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
                operateurs = ["AND", "OR"]
                fin_where = prewwhere[-5:]
                for ext in operateurs:
                    if ext in fin_where:
                        prewwhere = prewwhere[:-4]

            if prewwhere != "" and prewwhereSelect != "":
                prewrq += " WHERE " + prewwhere + " AND " + prewwhereSelect
            elif prewwhere == "" and prewwhereSelect != "":
                prewrq += " WHERE " + prewwhereSelect
            elif prewwhere != "" and prewwhereSelect == "":
                prewrq += " WHERE " + prewwhere

            prewrq += " GROUP BY  esp_id, esp_sigle ORDER BY esp_sigle"

            preQuery = QSqlQuery(self.db)
            preQuery.prepare(prewrq)
            if preQuery.exec_():
                while preQuery.next():
                    dicoEspece[preQuery.value(0)] = preQuery.value(1)
            else:
                QMessageBox.critical(self, u"Erreur récup espèces", preQuery.lastError().text(), QMessageBox.Ok)

            numColumn = 0
            for id, sigle in dicoEspece.items():
                if self.chkBiomasse.isChecked() == True :
                    self.wselect = self.wselect.replace("placementBiomasse", "placementBiomasse" + str(numColumn) + "placementBiomasse")
                    self.wselect = self.wselect.replace("placementBiomasse" + str(numColumn), ", \"join" + sigle + "\".espe_biomasse as \"BIOMASSE_" + sigle + "\"")
                    self.wgroupBy += ", \"join" + sigle + "\".espe_biomasse"

                if self.chkBioCorrespond.isChecked() == True :
                    self.wselect = self.wselect.replace("placementCorrespondanceBiomasse", "placementCorrespondanceBiomasse" + str(numColumn) + "placementCorrespondanceBiomasse")
                    self.wselect = self.wselect .replace("placementCorrespondanceBiomasse" + str(numColumn), ", \"join" + sigle + "\".clbi_val_correspond as \"CORBIO_" + sigle + "\"")
                    self.wgroupBy += ", \"join" + sigle + "\".clbi_val_correspond"

                if self.chkDensite.isChecked() == True :
                    self.wselect = self.wselect.replace("placementDensite", "placementDensite" + str(numColumn) + "placementDensite")
                    self.wselect = self.wselect.replace("placementDensite" + str(numColumn), ", \"join" + sigle + "\".espe_densite as \"DENSITE_" + sigle + "\"")
                    self.wgroupBy += ", \"join" + sigle + "\".espe_densite"

                if self.chkDenCorrespond.isChecked() == True :
                    self.wselect = self.wselect.replace("placementCorrespondanceDensite", "placementCorrespondanceDensite" + str(numColumn) + "placementCorrespondanceDensite")
                    self.wselect = self.wselect.replace("placementCorrespondanceDensite" + str(numColumn), ", \"join" + sigle + "\".clde_val_correspond as \"CORDEN_" + sigle + "\"")
                    self.wgroupBy += ", \"join" + sigle + "\".clde_val_correspond"

                self.cfrom += " FULL JOIN data.f_poisson_params(" + str(id) + ") as \"join" + sigle + "\" ON operation.ope_code = \"join" + sigle + "\".ope_code"

                numColumn +=1

            self.wselect = self.wselect.replace("placementBiomasse", "")
            self.wselect = self.wselect.replace("placementCorrespondanceBiomasse", "")
            self.wselect = self.wselect.replace("placementDensite", "")
            self.wselect = self.wselect.replace("placementCorrespondanceDensite", "")
            self.wselect = self.wselect.replace(", ,", ", ")

            self.wrq = ""

            # Construit la clause SELECT et ajoute la clause FROM à la requête
            self.wrq = "SELECT DISTINCT " + self.wselect + " FROM " + self.cfrom

            # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
            if self.wwhere != "":
                #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
                operateurs = ["AND", "OR"]
                fin_where = self.wwhere[-5:]
                for ext in operateurs:
                    if ext in fin_where:
                        self.wwhere = self.wwhere[:-4]

                self.wrq += " WHERE " + self.wwhere

            self.wrq += (" GROUP BY ope_peche_elec.opep_date, ope_peche_elec.opep_longueur_prospec, ope_peche_elec.opep_profondeur_moy, ope_peche_elec.opep_largeur_moy, " +
            "ope_peche_elec.opep_surf_peche, ope_peche_elec.opep_pente, station.sta_xl93_aval, station.sta_yl93_aval, ope_peche_elec.opep_ntt, ope_peche_elec.opep_ntt_reel, " +
            "ope_peche_elec.ipro_valeur, ipr.ipr_correspondance, ope_peche_elec.opep_complet_partielle, ope_peche_elec.opep_observation, cours_eau.ceau_nom, motif_peche.mope_motif, " +
            "condition_peche.cope_condition, contexte_pdpg.pdpg_code, masse_eau.meau_nom, masse_eau.meau_code, operation.ope_code, station.sta_nom, station.sta_distance_source, " +
            "station.sta_altitude, aappma.apma_nom, station.sta_surf_bv_amont, maitre_ouvrage.moa_nom")
            if self.wgroupBy != "":
                self.wrq += self.wgroupBy

        else:
            self.wrq = ""

            # Construit la clause SELECT et ajoute la clause FROM à la requête
            self.wrq = "SELECT DISTINCT " + self.wselect + " FROM " + self.cfrom

            # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
            if self.wwhere != "":
                #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
                operateurs = ["AND", "OR"]
                fin_where = self.wwhere[-5:]
                for ext in operateurs:
                    if ext in fin_where:
                        self.wwhere = self.wwhere[:-4]

            if self.wwhere != "" and self.wwhereSelect != "":
                self.wrq += " WHERE " + self.wwhere + " AND " + self.wwhereSelect
            elif self.wwhere == "" and self.wwhereSelect != "":
                self.wrq += " WHERE " + self.wwhereSelect
            elif self.wwhere != "" and self.wwhereSelect == "":
                self.wrq += " WHERE " + self.wwhere

            if self.tabWidget.currentIndex() == 1:
                self.wrq += (" GROUP BY opep_date, opep_longueur_prospec, opep_profondeur_moy, opep_largeur_moy, opep_surf_peche, opep_pente, sta_xl93_aval, sta_yl93_aval, " +
                "opep_ntt, opep_ntt_reel, ipro_valeur, espe_biomasse, clbi_val_correspond, espe_densite, clde_val_correspond, opep_complet_partielle, opep_observation, ceau_nom, " +
                "mope_motif, cope_condition, pdpg_code, meau_nom, meau_code, ope_code, sta_nom, sta_distance_source, sta_altitude, apma_nom, sta_surf_bv_amont, moa_nom")

    def previSql(self):
        '''Permet de prévisualiser la requête avant de l'éxecuter'''
        self.txtSql.setText("")
        self.creaRequete()

        if self.clauseSelect == True:
            # Affiche la requête
            self.txtSql.setText(self.wrq)
        else:
            QMessageBox.information(self, u"Prévisualisation impossible", u"Aucun champs sélectionné pour l'export...", QMessageBox.Ok)

    def previResu(self):
        '''Permet d'éxecuter la requête'''

        erreur = False
        interdit = ["update", "delete", "insert", "intersect", "duplicate", "truncate", "create", "drop", "alter"] # Le mot 'merge' a été retiré de la liste car il est contenu dans le mot 'eMERGEnce' utilisé en header du fichier SQL
        if self.txtSql.toPlainText() != "":
            self.requete = self.txtSql.toPlainText()
        else:
            self.creaRequete()
            self.requete = self.wrq

        if self.clauseSelect == True:
            # Vérifie la non présence de mot pouvant endommager la base de données
            testRequete = self.requete.lower()
            for mot in interdit:
                if mot in testRequete:
                    erreur = True
            if erreur == True :
                QMessageBox.critical(self, u"Erreur SQL", u"Vous essayez d'exécuter une requête qui peut endommager la base de données !", QMessageBox.Ok)
            # Après récupération du contenu de la zone de texte ou de la variable, exécute la requête pour prévisualiser le résultat
            else:
                query = QSqlQuery(self.db)
                query.prepare(self.requete)
                if query.exec_():
                    self.tableQuery = QSqlQueryModel()
                    self.tableQuery.setQuery(query)
                    self.tbvPrevisu.setModel(self.tableQuery)
                else:
                    QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)
        else:
            QMessageBox.information(self, u"Prévisualisation résultat", u"Aucun champs sélectionné pour l'export...", QMessageBox.Ok)

    def queryExport(self):
        '''Permet d'exporter le résultat de la requête en format CSV, séparateur  ";" '''

        erreur = False
        interdit = ["update", "delete", "insert", "intersect", "duplicate", "truncate", "create", "drop", "alter"] # Le mot 'merge' a été retiré de la liste car il est contenu dans le mot 'eMERGEnce' utilisé en header du fichier SQL
        if self.txtSql.toPlainText() != "":
            self.requete = self.txtSql.toPlainText()
        else:
            self.creaRequete()
            self.requete = self.wrq


        if self.clauseSelect == True:
            # Vérifie la non présence de mot pouvant endommager la base de données
            testRequete = self.requete.lower()
            for mot in interdit:
                if mot in testRequete:
                    erreur = True
            if erreur == True :
                QMessageBox.critical(self, u"Erreur SQL", u"Vous essayez d'exécuter une requête qui peut endommager la base de données !", QMessageBox.Ok)
            # Après récupération du contenu de la zone de texte ou de la variable, exécute la requête pour prévisualiser le résultat
            else:
                savefile = ""
                self.cheminCsv = ""
                # Récupération du chemin où enregistrer l'export
                savefile = QFileDialog.getSaveFileName(self, "Save File", "", u"Texte CSV délimitateur ';' (*.csv)")
                if savefile != "":
                    self.cheminCsv = unicode(savefile)

                if self.cheminCsv != "":
                    query = QSqlQuery(self.db)
                    query.prepare(self.requete)
                    if query.exec_():
                        # Exécution de la requête et attribution à un QSqlQueryModel()
                        exportQuery = QSqlQueryModel()
                        exportQuery.setQuery(query)

                        # Ouverture eet/ou création du fichier
                        with open(self.cheminCsv, 'wb') as exportFile: # --> V2 de QGIS
                        # with open(self.cheminCsv, newline = '') as exportFile:  # --> Pour la V3 de QGIS
                            writer = csv.writer(exportFile, delimiter = ';')

                            # Si il n'y a pas de header, on peut supprimer cette section
                            listsTmpData = []
                            for column in range(exportQuery.columnCount()):
                                    listsTmpData.append(str(exportQuery.headerData(column, Qt.Horizontal)))
                                    # listsTmpData.append(unicode(exportQuery.headerData(column, Qt.Horizontal))) # --> Pour la V3 de QGIS
                            writer.writerow(listsTmpData)

                            # Ecrit le document
                            for row in range(exportQuery.rowCount()):
                                listsTmpData = []
                                for column in range(exportQuery.columnCount()):
                                    # Try / Except pour essayer d'écrire la valeur avec son encodage par défaut, si le Try échou, le Except réessaye en remplacant le caractère problématique par '?'
                                    try :
                                        valeur = exportQuery.record(row).value(column)
                                        # Converti les QDate en string
                                        if isinstance(valeur, QDate):
                                            valeur = valeur.toString("dd-MM-yyyy")
                                        # Remplace les ';' par des ',', le fichier étant CSV ';'
                                        if ";" in str(valeur):
                                            valeur = valeur.replace(";", ",")
                                        if str(valeur) == "NULL":
                                            valeur = ""
                                        listsTmpData.append(str(valeur))
                                        # listsTmpData.append(str(exportQuery.record(row).value(column)))
                                    except:
                                        valeur = exportQuery.record(row).value(column)
                                         # Converti les QDate en string
                                        if isinstance(valeur, QDate):
                                            valeur = valeur.toString("dd-MM-yyyy")
                                        # Remplace les ';' par des ',', le fichier étant CSV ';'
                                        valeur = str(valeur.encode('ascii', 'replace'))
                                        if ";" in valeur:
                                            valeur = valeur.replace(";", ",")
                                        if valeur == "NULL":
                                            valeur = ""
                                        listsTmpData.append(valeur)
                                        # listsTmpData.append(str(exportQuery.record(row).value(column).encode('ascii', 'replace')))

                                        # Le Try / Except n'est normalement plus nécessaire en V3 de QGIS grâce à l'unicode
                                        # listsTmpData.append(unicode(exportQuery.record(row).value(column))) # --> Pour la V3 de QGIS
                                writer.writerow(listsTmpData)

                        self.iface.messageBar().pushMessage("Export : ", u"L'export est terminé ...", level= QgsMessageBar.INFO, duration = 5)
                    else:
                        QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Export impossible", u"Aucun champs sélectionné pour l'export...", QMessageBox.Ok)
