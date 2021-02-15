# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du formulaire "Inventaires de reproduction" du plugin.

# Import des modules Python, PyQt5 et QGIS nécessaire à l'exécution de ce fichier
import sys
import os
from functools import partial
from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QCursor, QPixmap)
from PyQt5.QtWidgets import (QApplication, QDataWidgetMapper, QDialog, QFileDialog, QDockWidget, QHeaderView, QMessageBox, QTableView)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel)
from qgis.core import (QgsPointXY, QgsTracer, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDataSourceUri, QgsExpression, QgsExpressionContext, QgsFeatureRequest,  QgsGeometry, QgsPoint, QgsRaster, QgsRasterLayer, QgsVectorDataProvider, QgsVectorLayer)
from qgis.gui import (QgsMapToolPan, QgsMessageBar, QgsMapToolEmitPoint, QgsVertexMarker)

# Initialise les ressources Qt à partir du fichier resources.py
from .resources_rc import *

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire
from opeInventaireForm import (Ui_dwcInventMainForm)
from opeStationForm import (Ui_dlgStationForm)
from opeMoaAjoutForm import (Ui_dlgMoaAjoutForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

# Import du script de filtrage des inventaires
from .opeInventaireFiltrage import (Filtrage_inventaire_dialog)

class Inventaire_dialog(QDockWidget, Ui_dwcInventMainForm):
    '''
    Class principal du formulaire "Inventaires de reproduction"

    :param QDockWidget: Permet d'ancrer le formulaire comme définit dans gedopiMenu
    :type QDockWidget: QDockWidget

    :param Ui_dwcInventMainForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dwcInventMainForm: class
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

        # Création des variables qui permettront de switcher entre
        # L'outil pour récupérer le clic sur le canevas
        # Et l'outil de défilement de la carte
        self.clickTool = QgsMapToolEmitPoint(self.mc)
        self.pan = QgsMapToolPan(self.mc)

        # Méthodes communes
        self.gc = Gedopi_common(self)

        # Variables pour la connexion à la base de données
        self.db = None
        self.dbType = ""
        self.dbSchema = ""

        # Variables pour récupérer les données des tables
        self.layer = None
        self.modelInventaire = None
        self.mapper = None
        self.modelStation = None
        self.modelRiviere = None
        self.modelBaran = None
        self.modelMoa = None

        # Variables diverses
        self.excelBool = False
        self.boolNew = False
        self.saisieAutoBool = False
        self.line = ""
        self.point_click_1 = ""
        self.point_click_2 = ""
        self.wopeir_geom = ""

        # Slot pour le filtrage cartographique
        self.slot_inventaire_select_changed = None
        slot = partial(self.inventaire_select_changed, 2)

        # Connexion des événements
        self.btnFiltreCartoManuel.clicked.connect(slot)
        self.btnFiltreAttributaire.clicked.connect(self.filtreAttributaire)
        self.btnDeleteFiltrage.clicked.connect(self.inventaire_annule_filtrage)

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.btnGeom.setCheckable(True)
        self.btnGeom.clicked.connect(self.calculCoordonnee)

        self.btnAjoutMoa.clicked.connect(self.ajoutMoa)
        self.btnSuppMoa.clicked.connect(self.suppMoa)

        self.btnZoom.clicked.connect(self.zoomInventaire)
        self.btnSelection.clicked.connect(self.selectionInventaire)
        self.btnStation.clicked.connect(self.ficheStation)
        self.btnExcel.clicked.connect(self.openTableur)
        self.btnAjoutFiche.clicked.connect(self.ajoutFiche)
        self.btnRetraitFiche.clicked.connect(self.retraitFiche)

        self.btnNouveau.clicked.connect(self.nouveau)
        self.btnModif.clicked.connect(self.modification)
        self.btnSupprimer.clicked.connect(self.supprimer)
        self.btnEnregistrer.clicked.connect(self.enregistrer)
        self.btnAnnuler.clicked.connect(self.annuler)

        self.btnPremier.clicked.connect(lambda: self.saveRecord("first"))
        self.btnPrec.clicked.connect(lambda: self.saveRecord("prev"))
        self.btnSuiv.clicked.connect(lambda: self.saveRecord("next"))
        self.btnDernier.clicked.connect(lambda: self.saveRecord("last"))

        self.chkVerrouModif.stateChanged.connect(self.verrouillageModif)
        self.chkVerrouAuto.stateChanged.connect(self.verrouillage)

        # Initialisation du nombre de page du formulaire
        self.row_courant = 0
        self.row_count = 0
        self.infoMessage = u"Gedopi - Inventaire de reproduction"

        self.etat_courant = 0

        # Initialisation du formulaire
        if self.verifiePresenceCouche():
            self.setupModel()
        else:
            self.clearFields()
            self.activeFields(False)
            self.activeButtons(False)

    def init_event(self):
        '''
        Appelé par setupModel(), supprime la sélection en cours si existante
        et supprime le filtrage en cours si existant
        '''
        layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
        if layer:
            layer.removeSelection()
            self.slot_inventaire_select_changed = partial(self.inventaire_select_changed, 1)
            layer.selectionChanged.connect(self.slot_inventaire_select_changed)

    def disconnect_event(self):
        '''
        Appelé par onVisibilityChange(), soit, quand le QDockWidget se ferme,
        déconnecte le filtrage et le rowChange()
        '''
        layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
        if layer:
            layer.selectionChanged.disconnect(self.slot_inventaire_select_changed)
            self.mapper.currentIndexChanged.disconnect(self.rowChange)

    def inventaire_select_changed(self, origine):
        '''
        Gère le filtrage cartographique des enregistrements

        :param origine: définie si le filtrage est cartographique ou attributaire,
                obtenu via les partial(self.inventaire_select_changed, origine)
        :type origine: int
        '''
        if self.etat_courant != 10:
            layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
            if layer:
                if layer.selectedFeatureCount() != 0:
                    self.btnFiltreCartoManuel.setEnabled(True)
                    if (origine == 1 and self.chkFiltreCartoAuto.isChecked()) or (origine == 2):
                        if (layer.selectedFeatureCount() >= 1000) and (QGis.QGIS_VERSION_INT < 21203):
                            layer.removeSelection()
                            self.iface.messageBar().pushMessage("Erreur : ", u"Le nombre d'éléments sélectionnés est trop important ...", level=QgsMessageBar.CRITICAL, duration=3)
                        else:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Inventaire de reproduction"
                            wparam = ""
                            for feature in layer.selectedFeatures():
                                expressContext = QgsExpressionContext()
                                expressContext.setFeature(feature)
                                wid = QgsExpression("$id").evaluate(expressContext)
                                wparam += str(wid) + ","
                            if (wparam != ""):
                                wparam = "(" + wparam[0:len(wparam) - 1] + ")"
                                if self.modelInventaire:
                                    self.modelInventaire.setFilter("opeir_id in %s" % wparam)
                                    self.modelInventaire.select()
                                    self.row_count = self.modelInventaire.rowCount()
                                    self.mapper.toFirst()
                                    self.btnDeleteFiltrage.setEnabled(True)
                else:
                    self.btnFiltreCartoManuel.setEnabled(False)

    def inventaire_annule_filtrage(self):
        '''Annule le filtrage cartographique ou attributaire'''

        if self.modelInventaire:
            self.infoMessage = u"Gedopi - Inventaire de reproduction"
            self.modelInventaire.setFilter("")
            self.modelInventaire.select()
            self.row_count = self.modelInventaire.rowCount()
            self.mapper.toFirst()
            self.btnDeleteFiltrage.setEnabled(False)

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
                self.disconnect_event()
        else:
            if self.verifiePresenceCouche():
                self.setupModel()

    def verifiePresenceCouche(self):
        '''
        Vérifie la présence de différentes couches et renvoi dans __init__, True ou False,
        active le setupModel si return True,
        verouille le formulaire si return False
        '''
        self.layer = None
        self.layerCeau = None
        self.layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
        self.layerCeau = self.gc.getLayerFromLegendByTableProps('cours_eau', 'ceau_geom', '')
        if self.layer:
            if self.layerCeau:
                return True
            else :
                self.iface.messageBar().pushMessage("Erreur : ", u"La couche des cours d'eau n'est pas chargé ...", level=QgsMessageBar.CRITICAL, duration = 5)
                return False
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des opérations d'inventaires de reproduction n'est pas chargée ...", level= QgsMessageBar.CRITICAL, duration = 5)
            return False

    def closeDatabase(self):
        '''Supprime certaines variables et déconnecte la base de données'''

        self.tbvMoa.setModel(None)
        self.mapper.setModel(None)

        del self.modelInventaire
        del self.modelBaran
        del self.modelRiviere
        del self.modelStation

        self.db.close()
        del self.db
        self.db = None
        QSqlDatabase.removeDatabase('db1')

        # Supprime le vertex du canevas si existant
        if self.point_click_1 != "":
            self.mc.scene().removeItem(self.point_click_1)
            self.point_click_1 = ""
        if self.point_click_2 != "":
            self.mc.scene().removeItem(self.point_click_2)
            self.point_click_2 = ""

    def setupModel(self):
        '''
        Initialise le formulaire en le connectant à la base de données
        et en attribuant aux différents champs leurs tables ou colonnes PostgreSQL
        '''
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.infoMessage = u"Gedopi - Inventaire de reproduction"
        if not self.db:
            self.init_event()
            connectionParams = self.gc.getConnectionParameterFromDbLayer(self.layer)
            if (connectionParams['dbType'] == u'postgres' or connectionParams['dbType'] == u'postgis'):
                self.dbType = "postgres"
                self.db = QSqlDatabase.addDatabase("QPSQL", 'db1')
                self.db.setDatabaseName(connectionParams['dbname'])
                self.db.setUserName(connectionParams['user'])
                self.db.setPassword(connectionParams['password'])
                self.db.setHostName(connectionParams['host'])
                self.dbSchema = connectionParams['schema']
                self.user = connectionParams['user']
                self.password = connectionParams['password']
                self.dbname = connectionParams['dbname']

            if (not self.db.open()):
                QMessageBox.critical(self, "Erreur", u"Impossible de se connecter à la base de données ...", QMessageBox.Ok)
                QApplication.restoreOverrideCursor()
                return

        # Déconnexion du filtrage auto des stations
        self.cmbRiviere.currentIndexChanged.disconnect(self.changeCmbRiviere)

        self.modelInventaire = QSqlRelationalTableModel(self, self.db)
        wrelation = "ope_inventaire_repro"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation

        self.modelInventaire.setTable(wrelation)
        self.modelInventaire.setSort(0, Qt.AscendingOrder)

        if (not self.modelInventaire.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Inventaire dans le setupModel() : \n" + self.modelInventaire.lastError().text(), QMessageBox.Ok)

        self.row_count = self.modelInventaire.rowCount()

        if self.row_count == 0:
            self.modelStation = QSqlTableModel(self, self.db)
            wrelation = "station"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelStation.setTable(wrelation)
            self.modelStation.setSort(0, Qt.AscendingOrder)
            if (not self.modelStation.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Station dans le setupModel() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)
            self.cmbStation.setModel(self.modelStation)
            self.cmbStation.setModelColumn(0)

            self.modelBaran = QSqlTableModel(self, self.db)
            wrelation = "baran_s_zfp"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelBaran.setTable(wrelation)
            self.modelBaran.setSort(3, Qt.AscendingOrder)
            if (not self.modelBaran.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Baran dans le setupModel() : \n" + self.modelBaran.lastError().text(), QMessageBox.Ok)
            self.cmbBaran.setModel(self.modelBaran)
            self.cmbBaran.setModelColumn(3)

        self.modelRiviere = QSqlTableModel(self, self.db)
        wrelation = "cours_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelRiviere.setTable(wrelation)
        self.modelRiviere.setFilter("ceau_nom <> 'NR'")
        self.modelRiviere.setSort(2, Qt.AscendingOrder)
        if (not self.modelRiviere.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Rivière dans le setupModel() : \n" + self.modelRiviere.lastError().text(), QMessageBox.Ok)

        self.cmbRiviere.setModel(self.modelRiviere)
        self.cmbRiviere.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        # Ajout de NR a la fin de la liste des cours d'eau
        riviereNR = "NR"
        self.cmbRiviere.addItem(riviereNR)

        self.modelStation = QSqlQueryModel(self)
        self.modelBaran = QSqlQueryModel(self)

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.modelInventaire)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

        # Remplissage des cases inventaire
        self.mapper.addMapping(self.leCodeOpe, self.modelInventaire.fieldIndex("opeir_ope_code"))
        self.mapper.addMapping(self.txtDate, self.modelInventaire.fieldIndex("opeir_date"))
        self.mapper.addMapping(self.spnPassage, self.modelInventaire.fieldIndex("opeir_nbre_passage"))
        self.mapper.addMapping(self.spnLongueur, self.modelInventaire.fieldIndex("opeir_longueur"))
        self.mapper.addMapping(self.spnLargeur, self.modelInventaire.fieldIndex("opeir_largeur_moy"))
        self.mapper.addMapping(self.spnSgf, self.modelInventaire.fieldIndex("opeir_sgf"))
        self.mapper.addMapping(self.spnZfp, self.modelInventaire.fieldIndex("opeir_zfp"))
        self.mapper.addMapping(self.spnNbreFrayere, self.modelInventaire.fieldIndex("opeir_nbre_frayere"))
        self.mapper.addMapping(self.spnSurfFrayere, self.modelInventaire.fieldIndex("opeir_surf_fray"))
        self.mapper.addMapping(self.spnBaran, self.modelInventaire.fieldIndex("barope_valeur"))

        # Maître d'ouvrages
        self.modelMoa = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_moa_opeir" #v_moa est une vue dans postgresql
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelMoa.setTable(wrelation)
        self.modelMoa.setSort(0, Qt.AscendingOrder)

        # self.modelMoa.setHeaderData(self.modelMoa.fieldIndex("moa_id"), Qt.Horizontal, "ID")
        self.modelMoa.setHeaderData(self.modelMoa.fieldIndex("moa_nom"), Qt.Horizontal, u"Maître d'ouvrage")

        if (not self.modelMoa.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Maître d'ouvrage dans le setupModel() : \n" + self.modelMoa.lastError().text(), QMessageBox.Ok)

        self.modelMoa.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvMoa.setModel(self.modelMoa)
        self.tbvMoa.setSelectionMode(QTableView.SingleSelection)
        self.tbvMoa.setSelectionBehavior(QTableView.SelectRows)
        self.tbvMoa.setColumnHidden(self.modelMoa.fieldIndex("moa_id"), True)
        self.tbvMoa.setColumnHidden(self.modelMoa.fieldIndex("opeir_id"), True)
        self.tbvMoa.resizeColumnsToContents()
        self.tbvMoa.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tbvMoa.horizontalHeader().setStretchLastSection(True)

        self.mapper.currentIndexChanged.connect(self.rowChange)

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        # Vérifie le verrouillage des champs impactés
        if self.chkVerrouAuto.isChecked() or self.chkVerrouModif.isChecked():
            self.verrouillage()
            self.verrouillageModif()

        # Vérification de la présence d'enregistrements
        if self.modelInventaire.rowCount() == 0:
            self.clearFields()
            self.activeFields(False)
            self.activeButtons(False)
        else:
            self.activeFields(True)
            self.activeButtons(True)
            self.mapper.toFirst()
        QApplication.restoreOverrideCursor()

    def clearFields(self):
        '''Vide les différents champs de saisie au démarrage du formulaire et si aucun enregistrement n'est trouvé'''

        self.leCodeOpe.setText("")
        self.txtDate.setText("")
        self.spnPassage.setValue(0)
        self.spnLongueur.setValue(0)
        self.spnLargeur.setValue(0)
        self.spnSgf.setValue(0)
        self.spnZfp.setValue(0)
        self.spnNbreFrayere.setValue(0)
        self.spnSurfFrayere.setValue(0)
        self.spnBaran.setValue(0)
        self.chkVerrouModif.setChecked(True)
        self.chkVerrouAuto.setChecked(True)
        modelRaz = QSqlQueryModel()
        self.tbvMoa.setModel(modelRaz)

    def activeFields(self, active):
        '''
        Active ou désactive les différents widgets de saisie en fonction de la visibilité du formulaire

        :param active: valeur True ou False en fonction de si le formulaire est affiché,
                valeur issue du QDockWidget.visibilityChanged
                ou définie par les self.activeFields(bool)
        :type active: bool
        '''

        # Certains objets ont pour paramètre False à la place de not active
        #afin d'éviter leur activation si visibilityChanged renvoie active = False
        self.leCodeOpe.setEnabled(active)
        self.txtDate.setEnabled(active)
        self.spnPassage.setEnabled(active)
        self.spnLongueur.setEnabled(not active)
        self.spnLargeur.setEnabled(active)
        self.spnSgf.setEnabled(active)
        self.spnZfp.setEnabled(active)
        self.spnNbreFrayere.setEnabled(active)
        self.spnSurfFrayere.setEnabled(active)
        self.spnBaran.setEnabled(active)
        self.cmbBaran.setEnabled(active)
        self.cmbRiviere.setEnabled(active)
        self.cmbStation.setEnabled(active)
        self.tbvMoa.setEnabled(active)
        self.chkVerrouModif.setEnabled(active)
        self.chkVerrouAuto.setEnabled(active)

    def activeButtons(self, active):
        '''
        Active ou désactive les différents boutons en fonction de la visibilité du formulaire

        :param active: valeur True ou False en fonction de si le formulaire est affiché,
                valeur issue du QDockWidget.visibilityChanged
                ou définie par les self.activeButtons(bool)
        :type active: bool
        '''

        # Certains objets ont pour paramètre False à la place de not active
        #afin d'éviter leur activation si visibilityChanged renvoie active = False
        self.btnFiltreCartoManuel.setEnabled(False)
        self.chkFiltreCartoAuto.setEnabled(active)
        self.btnFiltreAttributaire.setEnabled(active)
        self.btnDeleteFiltrage.setEnabled(False)

        self.btnGeom.setEnabled(False)

        self.btnNouveau.setEnabled(True)
        self.btnModif.setEnabled(False)
        self.btnSupprimer.setEnabled(active)
        self.btnEnregistrer.setEnabled(False)
        self.btnAnnuler.setEnabled(False)

        self.btnPremier.setEnabled(active)
        self.btnPrec.setEnabled(active)
        self.btnSuiv.setEnabled(active)
        self.btnDernier.setEnabled(active)

        self.btnZoom.setEnabled(active)
        self.btnSelection.setEnabled(active)
        self.btnStation.setEnabled(active)
        self.btnExcel.setEnabled(active)
        self.btnAjoutFiche.setEnabled(not active)
        self.btnRetraitFiche.setEnabled(not active)

        self.btnAjoutMoa.setEnabled(active)
        self.btnSuppMoa.setEnabled(active)

    def activeButtonsModif(self, active):
        '''
        Active ou désactive les différents boutons en fonction de la visibilité du formulaire

        :param active: valeur True ou False en fonction de si le formulaire est affiché,
                valeur issue du QDockWidget.visibilityChanged
                ou définie par les self.activeButtons(bool)
        :type active: bool
        '''

        # Certains objets ont pour paramètre False à la place de not active
        #afin d'éviter leur activation si visibilityChanged renvoie active = False
        self.btnFiltreCartoManuel.setEnabled(not active)
        self.chkFiltreCartoAuto.setEnabled(not active)
        self.btnFiltreAttributaire.setEnabled(not active)
        self.btnDeleteFiltrage.setEnabled(not active)

        self.btnGeom.setEnabled(active)

        self.btnPremier.setEnabled(not active)
        self.btnPrec.setEnabled(not active)
        self.btnSuiv.setEnabled(not active)
        self.btnDernier.setEnabled(not active)

        self.btnNouveau.setEnabled(not active)
        self.btnModif.setEnabled(not active)
        self.btnSupprimer.setEnabled(not active)
        self.btnEnregistrer.setEnabled(active)
        self.btnAnnuler.setEnabled(active)

        self.btnZoom.setEnabled(not active)
        self.btnSelection.setEnabled(not active)
        self.btnStation.setEnabled(not active)
        self.btnExcel.setEnabled(not active)
        self.btnAjoutFiche.setEnabled(active)
        self.btnRetraitFiche.setEnabled(active)

        self.btnAjoutMoa.setEnabled(not active)
        self.btnSuppMoa.setEnabled(not active)

    def saveRecord(self, wfrom):
        '''Permet le passage d'un enregistrement à un autre en fonction du bouton de défilement'''

        row = self.mapper.currentIndex()

        if wfrom == "first":
            row = 0
        elif wfrom == "prev":
            row = 0 if row <= 1 else row - 1
        elif wfrom == "next":
            row += 1
            if row >= self.modelInventaire.rowCount():
                row = self.modelInventaire.rowCount() - 1
        elif wfrom == "last":
            row = self.modelInventaire.rowCount() - 1

        self.mapper.setCurrentIndex(row)
        if self.row_count == 1:
            self.rowChange(0)

    def afficheInfoRow(self):
        '''Affiche en titre du QDockWidget, le nom du formulaire ainsi que l'enregistrement en courant / le nombre total'''

        self.setWindowTitle(self.infoMessage + " (" + str(self.row_courant + 1) + " / " + str(self.row_count) + ")")

    def changeCmbRiviere(self, newInd):
        '''
        Filtre la combobox station en fonction de la rivière affichée dans celle des cours d'eau

        :param newInd: index courant dans la combobox
        :type newInd: int
        '''
        record = self.modelRiviere.record(newInd)
        wceau_id = record.value(self.modelRiviere.fieldIndex("ceau_id"))

        # Permet la création d'opération sur des rivières "NR"
        if self.cmbRiviere.currentText() == 'NR':
            self.modelStation.clear()
            wrelation = "station"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelStation.setQuery("select sta_id, sta_id || ' ; ' || sta_nom from " + wrelation + " where sta_ceau_id in (select ceau_id from data.cours_eau where ceau_nom = 'NR') order by sta_id;", self.db)
            if self.modelStation.lastError().isValid():
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Station dans le changeCmbRiviere() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)

            self.cmbStation.setModel(self.modelStation)
            self.cmbStation.setModelColumn(1)

            # Remplissage de la combo avec les parcelles de la 1ère section
            self.cmbStation.setCurrentIndex(0)

        elif self.cmbRiviere.currentIndex() == -1:
            self.cmbStation.setCurrentIndex(-1)

        else:
            self.modelStation.clear()
            wrelation = "station"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelStation.setQuery("select sta_id, sta_id || ' ; ' || sta_nom from " + wrelation + " where sta_ceau_id = '%s' order by sta_id;" % str(wceau_id), self.db)
            if self.modelStation.lastError().isValid():
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Station dans le changeCmbRiviere() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)

            self.cmbStation.setModel(self.modelStation)
            self.cmbStation.setModelColumn(1)

            # Remplissage de la combo avec les parcelles de la 1ère section
            self.cmbStation.setCurrentIndex(0)

    def rowChange(self, row):
        '''
        Permet la mise à jour des champs lorsque l'enregistrement change

        :param row: le numéro de l'enregistrement courant,
                obtenu d'après saveRecord()
        :type row: int
        '''
        # Recoche des verrous
        self.chkVerrouAuto.setChecked(True)
        self.chkVerrouModif.setChecked(True)

        # Boutons de navigation
        self.row_courant = row
        self.btnPrec.setEnabled(row > 0)
        self.btnSuiv.setEnabled(row < self.modelInventaire.rowCount() - 1)

        # Déconnexion du filtrage auto des stations
        self.cmbRiviere.currentIndexChanged.disconnect(self.changeCmbRiviere)

        # Record de l'inventaire courant
        record = self.modelInventaire.record(row)
        wopeir_ope_code = record.value(self.modelInventaire.fieldIndex("opeir_ope_code"))

        # Récupération de la clé de l'operation correspondante
        query = QSqlQuery(self.db)
        wrelation = "operation"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("select ope_sta_id from " + wrelation + " where ope_code = ?")
        query.addBindValue(wopeir_ope_code)
        wope_sta_id = ""
        if query.exec_():
            if query.next():
                wope_sta_id = query.value(0)
                self.currentStation = wope_sta_id

        # Récupération de la clé de la riviere correspondante
        query = QSqlQuery(self.db)
        wrelation = "station"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("select sta_ceau_id from " + wrelation + " where sta_id = ?")
        query.addBindValue(wope_sta_id)
        wsta_ceau_id = ""
        if query.exec_():
            if query.next():
                wsta_ceau_id = query.value(0)

        # Sélection de la rivière
        result = self.cmbRiviere.model().match(self.cmbRiviere.model().index(0, 0), Qt.EditRole, wsta_ceau_id, -1, Qt.MatchExactly)
        if result:
            self.cmbRiviere.setCurrentIndex(result[0].row())
        else:
            indexNR = self.cmbRiviere.count()
            self.cmbRiviere.setCurrentIndex(indexNR - 1)

        # Filtrage station
        self.modelStation.clear()
        wrelation = "station"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelStation.setQuery("select sta_id, sta_id || ' ; ' || sta_nom from " + wrelation + " where sta_ceau_id = '%s' order by sta_id;" % str(wsta_ceau_id), self.db)
        if self.modelStation.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Station dans le rowChange() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)

        self.cmbStation.setModel(self.modelStation)
        self.cmbStation.setModelColumn(1)

        # Sélection station
        result = self.cmbStation.model().match(self.cmbStation.model().index(0, 0), Qt.EditRole, wope_sta_id, -1, Qt.MatchExactly)
        if result:
            self.cmbStation.setCurrentIndex(result[0].row())

       # Filtrage baran
        record = self.modelInventaire.record(row)
        wopeir_baran_id = record.value(self.modelInventaire.fieldIndex("opeir_baran_id"))
        self.modelBaran.clear()
        wrelation = "baran_s_zfp"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelBaran.setQuery("select baran_id, baran_correspond from " + wrelation + " order by baran_correspond;", self.db)

        if self.modelBaran.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Baran dans le rowChange() : \n" + self.modelBaran.lastError().text(), QMessageBox.Ok)

        self.cmbBaran.setModel(self.modelBaran)
        self.cmbBaran.setModelColumn(1)

        # Sélection baran
        result = self.cmbBaran.model().match(self.cmbBaran.model().index(0, 0), Qt.EditRole, wopeir_baran_id, -1, Qt.MatchExactly)
        if result:
            self.cmbBaran.setCurrentIndex(result[0].row())

        # Maitres d'ouvrage
        id = record.value("opeir_id")
        self.modelMoa.setFilter("opeir_id = %i" % id)

        self.afficheInfoRow()

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.verrouillageModif()

        # Vérifie la présence d'une géométrie
        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelInventaire.record(row)
                wid = record.value("opeir_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
                request = QgsFeatureRequest().setFilterFids([wid])

                it = layer.getFeatures(request)
                extent = None
                for x in it:
                    extent = x.geometry()
                if extent == None:
                    self.iface.messageBar().pushMessage("Attention : ", u"Cet inventaire de reproduction ne possède pas de géométrie.", level= QgsMessageBar.WARNING, duration = 5)

    def zoomInventaire(self):
        '''Permet de zoomer le canevas de la carte sur l'inventaire courante'''

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelInventaire.record(row)
                wid = record.value("opeir_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
                request = QgsFeatureRequest().setFilterFids([wid])

                it = layer.getFeatures(request)
                extent = None
                for x in it:
                    extent = x.geometry().boundingBox()
                if extent:
                    if self.mc.hasCrsTransformEnabled():
                        crsDest = self.mc.mapSettings().destinationCrs()
                        crsSrc = layer.crs()
                        xform = QgsCoordinateTransform(crsSrc, crsDest)
                        extent = xform.transform(extent)

                    self.mc.setExtent(extent.buffer(50))
                    self.mc.refresh()

    def selectionInventaire(self):
        '''Permet de sélectionner l'inventaire correspondant à l'enregistrement courant'''

        if self.mapper:
            row = self.mapper.currentIndex()
            self.etat_courant = 10
            if row >= 0:
                record = self.modelInventaire.record(row)
                wid = record.value("opeir_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
                layer.removeSelection()
                layer.select(wid)
                self.etat_courant = 0

    def openTableur(self):
        '''Permet d'ouvrir le fichier liée à l'inventaire'''

        row = self.mapper.currentIndex()
        record = self.modelInventaire.record(row)
        lienTableur = record.value(u"opeir_excel")
        if lienTableur == "" or lienTableur == None:
            self.iface.messageBar().pushMessage("Info : ", u"Pas de fichier joint !", level= QgsMessageBar.INFO, duration = 5)
        else :
            try:
                os.startfile(lienTableur)
            except:
                self.iface.messageBar().pushMessage("Info : ", u"Le fichier est introuvable !", level= QgsMessageBar.WARNING, duration = 5)

    def ajoutFiche(self):
        '''Permet de joindre un fichier externe à l'inventaire'''

        openfile = ""
        openfile = QFileDialog.getOpenFileName(self)
        if openfile != "":
            self.cheminExcel = unicode(openfile)
            self.excelBool = True

    def retraitFiche(self):
        '''Permet de retirer un fichier externe à l'inventaire'''
        if QMessageBox.question(self, u"Délier", u"Etes-vous certain de vouloir délier le fichier ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            self.cheminExcel = ""
            self.excelBool = True

    def supprimer(self):
        '''Permet de supprimer l'inventaire courante ainsi que toutes les données liées (cascade)'''

        filtreCourant = self.modelInventaire.filter()

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                if QMessageBox.question(self, "Suppression", u"Etes-vous certain de vouloir supprimer cette inventaire ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    record = self.modelInventaire.record(row)
                    wid = record.value("opeir_ope_code")

                    query = QSqlQuery(self.db)

                    wrelation = "operation"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                    query.addBindValue(wid)
                    if not query.exec_():
                        QMessageBox.critical(self, "Erreur", u"Impossible de supprimer cette inventaire ...", QMessageBox.Ok)

                    if filtreCourant != "":
                        filtreCourant = filtreCourant.replace(str(wid), "NULL" )

                    self.setupModel()

                    if filtreCourant != "":
                        self.modelInventaire.setFilter(filtreCourant)
                        self.row_count = self.modelInventaire.rowCount()
                        if self.row_count != 0:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Inventaire de reproduction"
                            self.mapper.toFirst()
                            self.btnDeleteFiltrage.setEnabled(True)

    def nouveau(self):
        '''Prépare le formulaire pour la saisie d'un nouvel inventaire'''

        self.boolNew = True
        self.line = ""
        layer = self.gc.getLayerFromLegendByTableProps('ope_inventaire_repro', 'opeir_geom', '')
        layer.removeSelection()
        self.inventaire_annule_filtrage()
        self.cmbRiviere.setCurrentIndex(-1)

        self.activeButtonsModif(True)
        self.clearFields()
        self.activeFields(True)

        self.chkVerrouModif.setChecked(False)
        self.verrouillage()

    def annuler(self, repositionnement = True):
        '''Annule la saisie d'une nouvelle station'''

        self.activeButtonsModif(False)
        self.btnFiltreCartoManuel.setEnabled(False)
        self.btnDeleteFiltrage.setEnabled(False)

        self.mapper.revert()

        self.boolNew = False
        self.line = ""

        if self.row_count == 0:
            self.clearFields()
            self.activeFields(False)
            self.activeButtons(False)
        else:
            if repositionnement:
                self.rowChange(self.row_courant)
            else:
                self.setupModel()
                self.chkVerrouModif.setChecked(True)
                self.chkVerrouAuto.setChecked(True)

        if self.point_click_1 != "":
            self.mc.scene().removeItem(self.point_click_1)
            self.point_click_1 = ""
        if self.point_click_2 != "":
            self.mc.scene().removeItem(self.point_click_2)
            self.point_click_2 = ""

    def enregistrer(self):
        '''Enregistre l'inventaire nouvellement créé'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbRiviere.model().record(self.cmbRiviere.currentIndex())
            wopeir_riviere = wrecord.value(0)

            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopeir_station = wrecord.value(0)

            wopeir_code = self.leCodeOpe.text()
            wopeir_dates = self.txtDate.toPlainText()
            wopeir_passage = self.spnPassage.value()
            wopeir_longueur = self.spnLongueur.value()
            wopeir_largeur = self.spnLargeur.value()
            wopeir_sgf = self.spnSgf.value()
            wopeir_zfp = self.spnZfp.value()
            wopeir_nbreFrayere = self.spnNbreFrayere.value()
            wopeir_surfFrayere = self.spnSurfFrayere.value()
            wbarope_valeur = self.spnBaran.value()
            wopeir_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopeir_excel = ""
                else :
                    wopeir_excel = self.cheminExcel
                    self.excelBool = False
            else :
                wopeir_excel = ""

            wrecord = self.cmbBaran.model().record(self.cmbBaran.currentIndex())
            wopeir_baran = wrecord.value(0)

            if self.line != "":
                line = self.line.exportToWkt()
                line = line.replace('LineString', 'MultiLineString(')

                wopeir_geom= "ST_GeomFromText(' "+ str(line) + ")', 2154)"

            # Création du code opération
            queryFk = QSqlQuery(self.db)
            wrelation = "operation"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryFk.prepare("INSERT INTO " + wrelation + " (ope_code, ope_sta_id) VALUES (?, ?)")
            queryFk.addBindValue(wopeir_code)
            queryFk.addBindValue(wopeir_station)
            if not queryFk.exec_():
                QMessageBox.critical(self, u"Erreur - création de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

            # Création de la requête d'enregistrement
            query = QSqlQuery(self.db)
            wrelation = "ope_inventaire_repro"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("INSERT INTO " + wrelation + " (opeir_date, opeir_nbre_passage, opeir_sgf, opeir_zfp, opeir_nbre_frayere, opeir_surf_fray, opeir_longueur, opeir_largeur_moy, " +
            "opeir_excel, opeir_ope_code, opeir_baran_id, barope_valeur, opeir_geom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " + wopeir_geom + ")")
            query.addBindValue(wopeir_dates)
            query.addBindValue(wopeir_passage)
            query.addBindValue(wopeir_sgf)
            query.addBindValue(wopeir_zfp)
            query.addBindValue(wopeir_nbreFrayere)
            query.addBindValue(wopeir_surfFrayere)
            query.addBindValue(wopeir_longueur)
            query.addBindValue(wopeir_largeur)
            query.addBindValue(wopeir_excel)
            query.addBindValue(wopeir_code)
            query.addBindValue(wopeir_baran)
            query.addBindValue(wbarope_valeur)
            if not query.exec_():
                querySupp = QSqlQuery(self.db)
                wrelation = "operation"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                querySupp.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                querySupp.addBindValue(wopeir_code)
                if not querySupp.exec_():
                    QMessageBox.critical(self, u"Erreur - Suppression de l'opération", querySupp.lastError().text(), QMessageBox.Ok)

                QMessageBox.critical(self, u"Erreur - Création de l'inventaire", query.lastError().text(), QMessageBox.Ok)
            else:
                # Màj du nombre d'enregistrement
                self.row_count += 1
                if self.row_count == 1:
                    self.modelInventaire.select()

            # Suppression du marqueur sur le canevas
            if self.point_click_1 != "":
                self.mc.scene().removeItem(self.point_click_1)
                self.point_click_1 = ""
            if self.point_click_2 != "":
                self.mc.scene().removeItem(self.point_click_2)
                self.point_click_2 = ""

            # Basculement du formulaire vers la visualisation
            self.annuler(False)
            self.mc.refresh()
            self.setupModel()
            self.boolNew = False
            self.line = ""
            self.saisieAutoBool = False
            wopeir_geom = ""
            self.saveRecord("last") #renvoie sur le dernier enregistrement

    def modification(self):
        '''Permet la modification de la station courante'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbRiviere.model().record(self.cmbRiviere.currentIndex())
            wopeir_riviere = wrecord.value(0)

            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopeir_station = wrecord.value(0)

            wopeir_code = self.leCodeOpe.text()
            wopeir_dates = self.txtDate.toPlainText()
            wopeir_passage = self.spnPassage.value()
            wopeir_longueur = self.spnLongueur.value()
            wopeir_largeur = self.spnLargeur.value()
            wopeir_sgf = self.spnSgf.value()
            wopeir_zfp = self.spnZfp.value()
            wopeir_nbreFrayere = self.spnNbreFrayere.value()
            wopeir_surfFrayere = self.spnSurfFrayere.value()
            wbarope_valeur = self.spnBaran.value()
            wopeir_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopeir_excel = ""
                else :
                    wopeir_excel = self.cheminExcel
                    self.excelBool = False
            else :
                row = self.mapper.currentIndex()
                record = self.modelInventaire.record(row)
                self.cheminExcel = record.value(u"opeir_excel")
                wopeir_excel = self.cheminExcel

            wrecord = self.cmbBaran.model().record(self.cmbBaran.currentIndex())
            wopeir_baran = wrecord.value(0)

            # Création de la requête de mise à jour
            if QMessageBox.question(self, "Enregistrer", u"Etes-vous certain de vouloir enregistrer les modifications ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

                filtreCourant = self.modelInventaire.filter()

                # Si modification de la géométrie (saisieAuto)
                if self.saisieAutoBool == True:
                    if self.line != "":
                        line = self.line.exportToWkt()
                        line = line.replace('LineString', 'MultiLineString(')

                        wopeir_geom= "ST_GeomFromText(' "+ str(line) + ")', 2154)"
                        # Requête de Màj du code opération
                        queryFk = QSqlQuery(self.db)
                        wrelation = "operation"
                        if self.dbType == "postgres":
                            wrelation = self.dbSchema + "." + wrelation
                        queryFk.prepare("UPDATE " + wrelation + " SET ope_code = '" + wopeir_code + "', ope_sta_id = " + str(wopeir_station) + " WHERE ope_code = '" + self.codeOpe + "'")
                        if not queryFk.exec_():
                            QMessageBox.critical(self, u"Erreur - Modification du code de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

                        query = QSqlQuery(self.db)
                        wrelation = "ope_inventaire_repro"
                        if self.dbType == "postgres":
                            wrelation = self.dbSchema + "." + wrelation
                        query.prepare("UPDATE " + wrelation + " SET opeir_date = '" + wopeir_dates + "', opeir_nbre_passage = " + str(wopeir_passage) + ", opeir_sgf = " + str(wopeir_sgf) +
                        ", opeir_zfp = " + str(wopeir_zfp) + ", opeir_nbre_frayere = " + str(wopeir_nbreFrayere) + ", opeir_surf_fray = " + str(wopeir_surfFrayere) + ", opeir_longueur = " + str(wopeir_longueur) +
                        ", opeir_largeur_moy = " + str(wopeir_largeur) + ", opeir_excel = '" + wopeir_excel + "', opeir_ope_code = '" + wopeir_code + "', opeir_baran_id = " + str(wopeir_baran) +
                        ", barope_valeur = " + str(wbarope_valeur) + ", opeir_geom = " + wopeir_geom + " WHERE opeir_ope_code = '" + wopeir_code + "'")

                        if not query.exec_():
                            self.saisieAutoBool = False
                            QMessageBox.critical(self, u"Erreur - Modification de l'inventaire et de sa géométrie", query.lastError().text(), QMessageBox.Ok)
                    else:
                        QMessageBox.critical(self, u"Erreur - Modification du placement de l'inventaire", query.lastError().text(), QMessageBox.Ok)

                    # Suppression des marqueurs sur le canevas
                    if self.point_click_1 != "":
                        self.mc.scene().removeItem(self.point_click_1)
                        self.point_click_1 = ""
                    if self.point_click_2 != "":
                        self.mc.scene().removeItem(self.point_click_2)
                        self.point_click_2 = ""
                # Si seul les atttributs sont modifiés
                else :
                    queryFk = QSqlQuery(self.db)
                    wrelation = "operation"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    queryFk.prepare("UPDATE " + wrelation + " SET ope_code = '" + wopeir_code + "', ope_sta_id = " + str(wopeir_station) + " WHERE ope_code = '" + self.codeOpe + "'")
                    if not queryFk.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification du code de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

                    query = QSqlQuery(self.db)
                    wrelation = "ope_inventaire_repro"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET opeir_date = '" + wopeir_dates + "', opeir_nbre_passage = " + str(wopeir_passage) + ", opeir_sgf = " + str(wopeir_sgf) +
                    ", opeir_zfp = " + str(wopeir_zfp) + ", opeir_nbre_frayere = " + str(wopeir_nbreFrayere) + ", opeir_surf_fray = " + str(wopeir_surfFrayere) + ", opeir_longueur = " + str(wopeir_longueur) +
                    ", opeir_largeur_moy = " + str(wopeir_largeur) + ", opeir_excel = '" + wopeir_excel + "', opeir_ope_code = '" + wopeir_code + "', opeir_baran_id = " + str(wopeir_baran) +
                    ", barope_valeur = " + str(wbarope_valeur) + " WHERE opeir_ope_code = '" + wopeir_code + "'")

                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification de l'inventaire", query.lastError().text(), QMessageBox.Ok)

                # Basculement du formulaire vers la visualisation
                self.chkVerrouModif.setChecked(True)
                self.mc.refresh()
                self.setupModel()
                self.saisieAutoBool = False
                self.line = ""
                wopeir_geom = ""
                # self.saveRecord("last") #renvoie sur le dernier enregistrement

                if filtreCourant != "":
                    self.modelInventaire.setFilter(filtreCourant)
                    self.row_count = self.modelInventaire.rowCount()
                    if self.row_count != 0:
                        self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Inventaire de reproduction"
                        self.mapper.toFirst()
                        self.btnDeleteFiltrage.setEnabled(True)

    def validation_saisie(self):
        '''Avant enregistrement, cette méthode doit valider la saisie'''

        if self.cmbRiviere.currentText() == "***" or self.cmbRiviere.currentText() == "":
            self.iface.messageBar().pushMessage("Erreur : ", u"Vous n'avez pas sélectionné de rivière ...", level=QgsMessageBar.CRITICAL, duration=5)
            saisieOk = False
        elif self.cmbStation.currentText() == "":
            self.iface.messageBar().pushMessage("Erreur : ", u"Aucune station séléctionnée ...", level=QgsMessageBar.CRITICAL, duration=5)
            saisieOk = False
        elif self.leCodeOpe.text() == "":
            self.iface.messageBar().pushMessage("Erreur : ", u"Aucun code opération saisie ...", level=QgsMessageBar.CRITICAL, duration=5)
            saisieOk = False
        elif self.line == "" and self.saisieAutoBool == True:
            self.iface.messageBar().pushMessage("Erreur : ", u"Vous n'avez pas placé l'inventaire ...", level=QgsMessageBar.CRITICAL, duration=5)
            saisieOk = False
        else:
            saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

    def calculCoordonnee(self):
        '''Permet de récupérer le clic sur le canevas'''

        self.iface.messageBar().pushMessage("Info : ", u"L'inventaire se trace de l'aval vers l'amont ...", level=QgsMessageBar.INFO, duration=5)
        self.clic = 0
        self.pointOk = False
        if self.btnGeom.isChecked():
            self.clickTool.canvasClicked.connect(self.saisieAuto)
            self.mc.setMapTool(self.clickTool)
        else:
            self.mc.setMapTool(self.pan)

    def saisieAuto(self, point):
        '''
        Récupère le point cliqué dans calculCoordonnee() et
        permet la saisie auto de certains champs du formulaire

        :param point: point issu du clic sur le canevas
        :type point: QgsPoint
        '''
        # Initialise et réinitialise les variables en cas de passage multiple
        self.saisieAutoBool = True
        self.line = ""

        # Récupération des clics pour calcul de la géométrie
        if self.clic == 0:
            self.layerPoint_1 = QgsPoint(point)
            self.clic += 1
            self.point_click_1 = QgsVertexMarker(self.mc)
            self.point_click_1.setCenter(self.layerPoint_1)
        elif self.clic == 1:
            self.layerPoint_2 = QgsPoint(point)
            self.clic += 1
            self.point_click_2 = QgsVertexMarker(self.mc)
            self.point_click_2.setCenter(self.layerPoint_2)
            self.pointOk = True
        else :
            self.pointOk = False
            self.clic = 0
            self.mc.setMapTool(self.pan)
            self.btnGeom.setChecked(False)
            self.clickTool.canvasClicked.disconnect(self.saisieAuto)
            self.iface.messageBar().pushMessage("Erreur : ", u"Deux point déjà cliqués, réactiver le bouton pour recommencer !", level= QgsMessageBar.WARNING, duration = 5)

        # Si saisie des 2 points ok
        if self.pointOk == True :
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            pt1 = ""
            pt2 = ""

            # Reprojection des points si nécessaires
            epsgBase = str(self.mc.mapSettings().destinationCrs().authid())
            epsgSrc = int(epsgBase.replace('EPSG:', ''))
            if epsgSrc != 2154:
                crsSrc = QgsCoordinateReferenceSystem(epsgSrc)
                crsDest = QgsCoordinateReferenceSystem(2154)
                xform = QgsCoordinateTransform(crsSrc, crsDest)
                pt1 = xform.transform(self.layerPoint_1)
                self.layerPoint_1 = xform.transform(self.layerPoint_1)
                pt2 = xform.transform(self.layerPoint_2)
                self.layerPoint_2 = xform.transform(self.layerPoint_2)
                pt1 = QgsPoint(pt1).wellKnownText()
                pt2 = QgsPoint(pt2).wellKnownText()
            else:
                pt1 = self.layerPoint_1
                pt2 = self.layerPoint_2
                pt1 = QgsPoint(pt1).wellKnownText()
                pt2 = QgsPoint(pt2).wellKnownText()

            # Sélection des cours d'eau dans les 6km autours du point 1
            if pt1 != "" and pt2 != "":
                wclick_geom= "ST_GeomFromText(' "+ str(pt1) + "', 2154)"
                wclick_geom_ceau = "ST_Buffer(" + wclick_geom + ", 6000)"
                query = QSqlQuery(self.db)
                wrelation = "cours_eau"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                requete = "select ceau_id from " + wrelation + " where ST_Intersects(ceau_geom , " + wclick_geom_ceau + ")"
                query.prepare(requete)
                ceau_intersect = ""
                i = 0
                if query.exec_():
                    i = int(query.size())
                    if i != 0:
                        while i > 0:
                            if query.next():
                                if ceau_intersect == "":
                                    ceau_intersect = str(query.value(0))
                                else :
                                    ceau_intersect = str(ceau_intersect) + ", " + str(query.value(0))
                                i -= 1

                # Import virtuel de la couche des cours d'eau
                uri = QgsDataSourceURI()
                uri.setConnection("localhost", "5432", self.dbname, self.password, self.user)
                uri.setDataSource("data", "cours_eau", "ceau_geom", "ceau_id IN (" + ceau_intersect + ")")
                vlayer = QgsVectorLayer(uri.uri(), "riviere", "postgres")

                if not vlayer.isValid():
                    self.iface.messageBar().pushMessage("Erreur : ", u"Layer failed Rivière to load !", level= QgsMessageBar.CRITICAL, duration = 5)
                else:
                    if self.point_click_1 != "":
                        self.mc.scene().removeItem(self.point_click_1)
                        self.point_click_1 = ""
                    if self.point_click_2 != "":
                        self.mc.scene().removeItem(self.point_click_2)
                        self.point_click_2 = ""

                    # Recalcul de la position des points afin de les accrocher à la rivière la plus proche
                    shortestDist_1 = float("inf")
                    shortestDist_2 = float("inf")
                    for f in vlayer.getFeatures():
                        dist_1 = f.geometry().distance(QgsGeometry.fromPoint(self.layerPoint_1))
                        dist_2 = f.geometry().distance(QgsGeometry.fromPoint(self.layerPoint_2))
                        if dist_1 < shortestDist_1:
                            shortestDist_1 = dist_1
                            pt1 = f.geometry().nearestPoint( QgsGeometry.fromPoint(self.layerPoint_1))
                            pt1 = pt1.vertexAt(0)

                        if dist_2 < shortestDist_2:
                            shortestDist_2 = dist_2
                            pt2 = f.geometry().nearestPoint( QgsGeometry.fromPoint(self.layerPoint_2))
                            pt2 = pt2.vertexAt(0)
                    self.point_click_2 = QgsVertexMarker(self.mc)
                    self.point_click_2.setCenter(pt2)

                    self.point_click_1 = QgsVertexMarker(self.mc)
                    self.point_click_1.setCenter(pt1)

                    # Calcul du chemin entre les deux points en suivant le cours d'eau
                    list = []
                    list.append(vlayer)
                    couche = QgsTracer()
                    couche.setLayers(list)
                    point_fin = couche.findShortestPath(pt1, pt2)
                    if point_fin[1] == 1:
                        self.iface.messageBar().pushMessage("ErrTooManyFeatures : ", "Max feature count threshold was reached while reading features !", level= QgsMessageBar.CRITICAL, duration = 5)
                        self.line = ""
                        self.clic = 0
                        self.pointOk = False
                    elif point_fin[1] == 2:
                        self.iface.messageBar().pushMessage("ErrPoint1 : ", "Start point cannot be joined to the grap !", level= QgsMessageBar.CRITICAL, duration = 5)
                        self.line = ""
                        self.clic = 0
                        self.pointOk = False
                    elif point_fin[1] == 3:
                        self.iface.messageBar().pushMessage("ErrPoint2 : ", "End point cannot be joined to the graph !", level= QgsMessageBar.CRITICAL, duration = 5)
                        self.line = ""
                        self.clic = 0
                        self.pointOk = False
                    elif point_fin[1] == 4:
                        self.iface.messageBar().pushMessage("ErrNoPath : ", "Points are not connected in the graph !", level= QgsMessageBar.CRITICAL, duration = 5)
                        self.line = ""
                        self.clic = 0
                        self.pointOk = False
                    elif point_fin[1] == 0:
                        list_point = point_fin[0]
                        self.line = QgsGeometry.fromPolyline(list_point)
                    else :
                        self.line = ""
                        self.clic = 0
                        self.pointOk = False
                        self.iface.messageBar().pushMessage("Erreur : ", u"Fail at findShortestPath !", level= QgsMessageBar.CRITICAL, duration = 5)
                if self.line != "":
                    longueur = self.line.length()
                    self.spnLongueur.setValue(longueur)
                else :
                    self.iface.messageBar().pushMessage("Erreur : ", u"Chemin entre les deux points non trouvé !", level= QgsMessageBar.CRITICAL, duration = 5)
            else:
                self.iface.messageBar().pushMessage("Erreur : ", u"Aucune coordonnée (erreur aux pt1 et pt2) !", level= QgsMessageBar.CRITICAL, duration = 5)

            # Restauration de l'état avant saisieAuto(
            self.mc.setMapTool(self.pan)
            QApplication.restoreOverrideCursor()
            self.clic = 0
            self.pointOk = False
            self.btnGeom.setChecked(False)
            self.clickTool.canvasClicked.disconnect(self.saisieAuto)
        elif self.clic != 1 :
            self.iface.messageBar().pushMessage("Erreur : ", u"La récupération du ou des clic(s) a échouée !", level= QgsMessageBar.CRITICAL, duration = 5)

    def ficheStation(self):
        '''Permet l'ouverture d'une fenêtre affichant toutes les infos de la station'''

        wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
        wsta_id = wrecord.value(0)
        if str(wsta_id) == "NULL" or wsta_id == -1:
            self.iface.messageBar().pushMessage("Info : ", u"Aucune station sélectionée !", level= QgsMessageBar.INFO, duration = 5)
        else:
            dialog = Fiche_station(self.db, self.dbType, self.dbSchema, wsta_id)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.exec_()

    def filtreAttributaire(self):
        '''Permet l'ouverture de la fenêtre de filtre attributaire'''

        dialog = Filtrage_inventaire_dialog(self.db, self.dbType, self.dbSchema, self.modelInventaire)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.row_count = self.modelInventaire.rowCount()
            if self.row_count != 0:
                self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Inventaire de reproduction"
                self.mapper.toFirst()
                self.btnDeleteFiltrage.setEnabled(True)

    def ajoutMoa(self):
        '''Permet l'ouverture de la fenêtre pour ajouter un maître d'ouvrage'''

        record = self.modelInventaire.record(self.row_courant)
        wopeir_id = record.value("opeir_id")
        dialog = Ope_moa_ajout_dialog(self.db, self.dbType, self.dbSchema, wopeir_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelMoa.setFilter("opeir_id = %i" % wopeir_id)

    def suppMoa(self):
        '''Permet de supprimer le maître d'ouvrage sélectionné'''

        record = self.modelInventaire.record(self.row_courant)
        wopeir_id = record.value("opeir_id")

        index = self.tbvMoa.currentIndex()
        if not index.isValid():
            return
        if QMessageBox.question(self, u"Suppression du maître d'ouvrage", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            query = QSqlQuery(self.db)

            wope_code = self.leCodeOpe.text()
            wrelation = "ope_inventaire_repro"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("SELECT opeir_id FROM " + wrelation + " WHERE opeir_ope_code = '" + wope_code + "'")
            if query.exec_():
                if query.next():
                    wopeir_id = query.value(0)

            wid = ""
            selection = self.tbvMoa.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            wrelation = "real_inventaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("DELETE FROM " + wrelation + " WHERE ri_opeir_id = '" + str(wopeir_id) + "' and ri_moa_id = '" + str(wid) + "'")
            if not query.exec_():
                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce maître d'ouvrage ...", QMessageBox.Ok)
            self.modelMoa.setFilter("opeir_id = %i" % wopeir_id)

    def verrouillage(self):
        '''Verrouille les champs de saisie automatique si coché'''

        if self.chkVerrouAuto.isChecked():
            self.spnLongueur.setEnabled(False)
        else:
            self.spnLongueur.setEnabled(True)

    def verrouillageModif(self):
        '''Verrouille les champs afin d'éviter les modifications intempestive'''

        self.line = ""
        self.saisieAutoBool = False
        if self.chkVerrouModif.isChecked():
            self.leCodeOpe.setEnabled(False)
            self.txtDate.setEnabled(False)
            self.spnPassage.setEnabled(False)
            self.spnLargeur.setEnabled(False)
            self.spnSgf.setEnabled(False)
            self.spnZfp.setEnabled(False)
            self.spnNbreFrayere.setEnabled(False)
            self.spnSurfFrayere.setEnabled(False)
            self.spnBaran.setEnabled(False)
            self.cmbBaran.setEnabled(False)
            self.cmbRiviere.setEnabled(False)
            self.cmbStation.setEnabled(False)
            self.btnGeom.setEnabled(False)
            self.btnAjoutFiche.setEnabled(False)
            self.btnRetraitFiche.setEnabled(False)
            self.btnExcel.setEnabled(True)
            if self.boolNew == False:
                self.btnModif.setEnabled(False)
        else:
            self.leCodeOpe.setEnabled(True)
            self.txtDate.setEnabled(True)
            self.spnPassage.setEnabled(True)
            self.spnLargeur.setEnabled(True)
            self.spnSgf.setEnabled(True)
            self.spnZfp.setEnabled(True)
            self.spnNbreFrayere.setEnabled(True)
            self.spnSurfFrayere.setEnabled(True)
            self.spnBaran.setEnabled(True)
            self.cmbBaran.setEnabled(True)
            self.cmbRiviere.setEnabled(True)
            self.cmbStation.setEnabled(True)
            self.btnGeom.setEnabled(True)
            self.codeOpe = self.leCodeOpe.text()
            self.btnAjoutFiche.setEnabled(True)
            self.btnRetraitFiche.setEnabled(True)
            self.btnExcel.setEnabled(False)
            if self.boolNew == False:
                self.btnModif.setEnabled(True)

        if self.point_click_1 != "":
            self.mc.scene().removeItem(self.point_click_1)
            self.point_click_1 = ""
        if self.point_click_2 != "":
            self.mc.scene().removeItem(self.point_click_2)
            self.point_click_2 = ""

class Ope_moa_ajout_dialog(QDialog, Ui_dlgMoaAjoutForm):
    '''
    Class de la fenêtre permettant d'ajouter un maître d'ouvrage

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgMoaAjoutForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgMoaAjoutForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wopeir_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage de la combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wopeir_id: identifiant de l'inventaire courant
        :type wopeir_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ope_moa_ajout_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wopeir_id = wopeir_id
        self.setupUi(self)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

        self.model = QSqlTableModel(self, self.db)

        wrelation = "maitre_ouvrage"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.model.setTable(wrelation)
        self.model.setSort(1, Qt.AscendingOrder)
        if (not self.model.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Station dans le Ope_moa_ajout_dialog.__init__() : \n" + self.model.lastError().text(), QMessageBox.Ok)

        self.cmbMoa.setModel(self.model)
        self.cmbMoa.setModelColumn(1)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def accept(self):
        '''Enregistre le maître d'ouvrage comme lié à l'inventaire'''

        wrecord = self.cmbMoa.model().record(self.cmbMoa.currentIndex())
        wmoa = wrecord.value(0)

        query = QSqlQuery(self.db)

        wrelation = "real_inventaire"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("INSERT INTO " + wrelation + " (ri_opeir_id, ri_moa_id) VALUES (?, ?)")
        query.addBindValue(self.wopeir_id)
        query.addBindValue(wmoa)
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur - Ajout du maître d'ouvrage", query.lastError().text(), QMessageBox.Ok)
        else:
            QDialog.accept(self)

class Fiche_station(QDialog, Ui_dlgStationForm):
    '''
    Class de la fenêtre permettant de créer un nouveau propriétaire

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgStationForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgStationForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wsta_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des champs

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wsta_id: identifiant de la station courante
        :type wsta_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Fiche_station, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wsta_id = wsta_id
        self.setupUi(self)
        self.btnFermer.clicked.connect(self.reject)

        query = QSqlQuery(self.db)
        wrelation = "v_station"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("SELECT sta_id, sta_altitude, sta_xl93_aval, sta_yl93_aval, pdpg, apma_nom, sta_distance_source, sta_surf_bv_amont, meau_nom, ceau_nom, sta_photo, sta_nom FROM " + wrelation + " WHERE sta_id = " + str(self.wsta_id))
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur", query.lastError().text(), QMessageBox.Ok)

        if query.exec_():
            if query.next():
                wid = query.value(0)
                waltitude = query.value(1)
                wx = query.value(2)
                wy = query.value(3)
                wpdpg = query.value(4)
                waappma = query.value(5)
                wdistance = query.value(6)
                wsurface = query.value(7)
                wmce = query.value(8)
                wriviere = query.value(9)
                wphoto = query.value(10)
                wnom = query.value(11)

                self.leId.setText(str(wid))
                self.leAltitude.setText(str(waltitude))
                self.leX.setText(str(wx))
                self.leY.setText(str(wy))
                self.lePdpg.setText(wpdpg)
                self.leAappma.setText(waappma)
                self.leDistance.setText(str(wdistance))
                self.leSurface.setText(str(wsurface))
                self.leMeau.setText(wmce)
                self.leRiviere.setText(wriviere)
                self.lePhoto.setText(wphoto)
                self.leNom.setText(wnom)

        chemin = unicode(self.lePhoto.text())
        if chemin != "" or chemin != "***":
            size = self.size()
            self.pixmap = QPixmap (chemin)
            self.pixmap = self.pixmap.scaledToHeight(250, Qt.SmoothTransformation)
            self.lblPhoto.setPixmap(QPixmap(self.pixmap))
        if chemin == "***":
            self.lblPhoto.setText("Aucune photo pour cette station")

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)
