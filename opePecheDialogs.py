# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du formulaire "Pêche électrique" du plugin.

# Import des modules Python, PyQt5 et QGIS nécessaire à l'exécution de ce fichier
import sys
import os
from functools import partial
from PyQt5.QtCore import (Qt, QFileInfo, QDate)
from PyQt5.QtGui import (QCursor, QPixmap)
from PyQt5.QtWidgets import (QApplication, QDataWidgetMapper, QDialog, QFileDialog, QDockWidget, QHeaderView, QMessageBox, QTableView)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel)
from qgis.core import (QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDataSourceUri, QgsExpression, QgsExpressionContext, QgsFeatureRequest,  QgsGeometry, QgsPoint, QgsRaster, QgsRasterLayer, QgsVectorDataProvider, QgsVectorLayer)
from qgis.gui import (QgsMapToolPan, QgsMessageBar, QgsMapToolEmitPoint, QgsVertexMarker)

# Initialise les ressources Qt à partir du fichier resources.py
from .resources_rc import *

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire
from opePecheElecForm import (Ui_dwcPecheMainForm)
from opeStationForm import (Ui_dlgStationForm)
from opeMoaAjoutForm import (Ui_dlgMoaAjoutForm)
from opeOperateurAjoutForm import (Ui_dlgOperateurAjoutForm)
from opePechePoissonForm import (Ui_dlgPecheSaisieForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

# Import du script de filtrage des pêches électriques
from .opePecheFiltrage import (Filtrage_peche_dialog)

class Peche_elec_dialog(QDockWidget, Ui_dwcPecheMainForm):
    '''
    Class principal du formulaire "Pêches électriques"

    :param QDockWidget: Permet d'ancrer le formulaire comme définit dans gedopiMenu
    :type QDockWidget: QDockWidget

    :param Ui_dwcPecheMainForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dwcPecheMainForm: class
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

        # Variables de connexion à la base de données
        self.db = None
        self.dbType = ""
        self.dbSchema = ""

        # Variables de stockage des données
        self.layer = None
        self.modelPeche = None
        self.mapper = None
        self.modelOperateur = None
        self.modelStation = None
        self.modelRiviere = None
        self.modelCondition = None
        self.modelMotif = None
        self.modelMoa = None
        self.modelPoisson = None

        # Variables diverses
        self.excelBool = False
        self.boolNew = False
        self.line = ""
        self.point_click_1 = ""
        self.point_click_2 = ""
        self.penteBool = False
        self.cheminRaster = os.path.dirname(os.path.abspath(__file__)) + "/data/system/raster"

        # Slot pour le filtrage cartographique
        self.slot_peche_select_changed = None
        slot = partial(self.peche_select_changed, 2)

        # Connexion des événements
        self.btnFiltreCartoManuel.clicked.connect(slot)
        self.btnFiltreAttributaire.clicked.connect(self.filtreAttributaire)
        self.btnDeleteFiltrage.clicked.connect(self.peche_annule_filtrage)

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.btnAjoutMoa.clicked.connect(self.ajoutMoa)
        self.btnSuppMoa.clicked.connect(self.suppMoa)
        self.btnAjoutOperateur.clicked.connect(self.ajoutOperateur)
        self.btnSuppOperateur.clicked.connect(self.suppOperateur)
        self.btnAjoutPoisson.clicked.connect(self.ajoutPeche)
        self.btnSuppPoisson.clicked.connect(self.suppPeche)

        self.btnZoom.clicked.connect(self.zoomPeche)
        self.btnSelection.clicked.connect(self.selectionPeche)
        self.btnExcel.clicked.connect(self.openTableur)
        self.btnAjoutFiche.clicked.connect(self.ajoutFiche)
        self.btnRetraitFiche.clicked.connect(self.retraitFiche)
        self.btnStation.clicked.connect(self.ficheStation)

        self.btnNouveau.clicked.connect(self.nouveau)
        self.btnModif.clicked.connect(self.modification)
        self.btnSupprimer.clicked.connect(self.supprimer)
        self.btnEnregistrer.clicked.connect(self.enregistrer)
        self.btnAnnuler.clicked.connect(self.annuler)

        self.btnPremier.clicked.connect(lambda: self.saveRecord("first"))
        self.btnPrec.clicked.connect(lambda: self.saveRecord("prev"))
        self.btnSuiv.clicked.connect(lambda: self.saveRecord("next"))
        self.btnDernier.clicked.connect(lambda: self.saveRecord("last"))

        self.btnPente.setCheckable(True)
        self.btnPente.clicked.connect(self.calculCoordonnee)

        self.chkVerrouAuto.stateChanged.connect(self.verrouillage)
        self.chkVerrouModif.stateChanged.connect(self.verrouillageModif)

        self.spnLongueur.valueChanged.connect(self.saisieAuto)
        self.spnLargeur.valueChanged.connect(self.saisieAuto)

        # Initialisation du nombre de page du formulaire
        self.row_courant = 0
        self.row_count = 0
        self.infoMessage = u"Gedopi - Pêche électrique"

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
        layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        if layer:
            layer.removeSelection()
            self.slot_peche_select_changed = partial(self.peche_select_changed, 1)
            layer.selectionChanged.connect(self.slot_peche_select_changed)

    def disconnect_event(self):
        '''
        Appelé par onVisibilityChange(), soit, quand le QDockWidget se ferme,
        déconnecte le filtrage et le rowChange()
        '''
        layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        if layer:
            layer.selectionChanged.disconnect(self.slot_peche_select_changed)
            self.mapper.currentIndexChanged.disconnect(self.rowChange)

    def peche_select_changed(self, origine):
        '''
        Gère le filtrage cartographique des enregistrements

        :param origine: définie si le filtrage est cartographique ou attributaire,
                obtenu via les partial(self.peche_select_changed, origine)
        :type origine: int
        '''
        if self.etat_courant != 10:
            layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
            if layer:
                if layer.selectedFeatureCount() != 0:

                    self.btnFiltreCartoManuel.setEnabled(True)
                    if (origine == 1 and self.chkFiltreCartoAuto.isChecked()) or (origine == 2):
                        if (layer.selectedFeatureCount() >= 1000) and (QGis.QGIS_VERSION_INT < 21203):
                            layer.removeSelection()
                            self.iface.messageBar().pushMessage("Erreur : ", u"Le nombre d'éléments sélectionnés est trop important ...", level=QgsMessageBar.CRITICAL, duration=3)
                        else:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Pêche électrique"
                            wparam = ""
                            for feature in layer.selectedFeatures():
                                expressContext = QgsExpressionContext()
                                expressContext.setFeature(feature)
                                wid = QgsExpression("$id").evaluate(expressContext)
                                wparam += str(wid) + ","
                            if (wparam != ""):
                                wparam = "(" + wparam[0:len(wparam) - 1] + ")"
                                if self.modelPeche:
                                    self.modelPeche.setFilter("opep_id in %s" % wparam)
                                    self.modelPeche.select()
                                    self.row_count = self.modelPeche.rowCount()
                                    self.mapper.toFirst()
                                    self.btnDeleteFiltrage.setEnabled(True)
                else:
                    self.btnFiltreCartoManuel.setEnabled(False)

    def peche_annule_filtrage(self):
        '''Annule le filtrage cartographique ou attributaire'''

        if self.modelPeche:
            self.infoMessage = u"Gedopi - Pêche électrique"
            self.modelPeche.setFilter("")
            self.modelPeche.select()
            self.row_count = self.modelPeche.rowCount()
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
        self.layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        self.layerCeau = self.gc.getLayerFromLegendByTableProps('cours_eau', 'ceau_geom', '')
        if self.layer:
            if self.layerCeau:
                return True
            else :
                self.iface.messageBar().pushMessage("Erreur : ", u"La couche des cours d'eau n'est pas chargé ...", level=QgsMessageBar.CRITICAL, duration = 5)
                return False
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des opérations de pêches électriques n'est pas chargée ...", level= QgsMessageBar.CRITICAL, duration = 5)
            return False

    def closeDatabase(self):
        '''Supprime certaines variables et déconnecte la base de données'''

        self.tbvOperateur.setModel(None)
        self.tbvMoa.setModel(None)
        self.mapper.setModel(None)

        del self.modelPeche
        del self.modelOperateur
        del self.modelStation
        del self.modelCondition
        del self.modelMotif
        del self.modelMoa
        del self.modelIpr
        del self.modelRiviere
        del self.modelPoisson

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
        self.infoMessage = u"Gedopi - Pêche électrique"
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

        self.cmbRiviere.currentIndexChanged.disconnect(self.changeCmbRiviere)

        self.modelPeche = QSqlRelationalTableModel(self, self.db)
        wrelation = "ope_peche_elec"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation

        self.modelPeche.setTable(wrelation)
        self.modelPeche.setSort(0, Qt.AscendingOrder)

        if (not self.modelPeche.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Pëche dans le setupModel() : \n" + self.modelPeche.lastError().text(), QMessageBox.Ok)

        self.row_count = self.modelPeche.rowCount()

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

            self.modelCondition = QSqlTableModel(self, self.db)
            wrelation = "condition_peche"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelCondition.setTable(wrelation)
            self.modelCondition.setSort(1, Qt.AscendingOrder)
            if (not self.modelCondition.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Condition dans le setupModel() : \n" + self.modelCondition.lastError().text(), QMessageBox.Ok)
            self.cmbCondition.setModel(self.modelCondition)
            self.cmbCondition.setModelColumn(1)

            self.modelMotif = QSqlTableModel(self, self.db)
            wrelation = "motif_peche"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelMotif.setTable(wrelation)
            self.modelMotif.setSort(1, Qt.AscendingOrder)
            if (not self.modelMotif.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Motif dans le setupModel() : \n" + self.modelMotif.lastError().text(), QMessageBox.Ok)
            self.cmbMotif.setModel(self.modelMotif)
            self.cmbMotif.setModelColumn(1)

            self.modelIpr = QSqlTableModel(self, self.db)
            wrelation = "ipr"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelIpr.setTable(wrelation)
            self.modelIpr.setSort(3, Qt.AscendingOrder)
            if (not self.modelIpr.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle IPR dans le setupModel() : \n" + self.modelIpr.lastError().text(), QMessageBox.Ok)
            self.cmbIpr.setModel(self.modelIpr)
            self.cmbIpr.setModelColumn(3)

        self.modelRiviere = QSqlTableModel(self, self.db)
        wrelation = "cours_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelRiviere.setTable(wrelation)
        self.modelRiviere.setFilter("ceau_nom != 'NR'")
        self.modelRiviere.setSort(2, Qt.AscendingOrder)
        if (not self.modelRiviere.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Rivière dans le changeCmbRiviere() : \n" + self.modelRiviere.lastError().text(), QMessageBox.Ok)

        self.cmbRiviere.setModel(self.modelRiviere)
        self.cmbRiviere.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        # Ajout de NR a la fin de la liste des cours d'eau
        riviereNR = "NR"
        self.cmbRiviere.addItem(riviereNR)

        self.modelCondition = QSqlQueryModel(self)
        self.modelMotif = QSqlQueryModel(self)
        self.modelIpr = QSqlQueryModel(self)
        self.modelStation = QSqlQueryModel(self)
        self.modelOperateur = QSqlQueryModel(self)
        self.modelOperation= QSqlQueryModel(self)

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.modelPeche)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

    # Remplissage des cases peche
        self.mapper.addMapping(self.leCodeOpe, self.modelPeche.fieldIndex("opep_ope_code"))
        self.mapper.addMapping(self.datePeche, self.modelPeche.fieldIndex("opep_date"))
        self.mapper.addMapping(self.chkComplete, self.modelPeche.fieldIndex("opep_complet_partielle"))
        self.mapper.addMapping(self.spnNbreAnode, self.modelPeche.fieldIndex("opep_nbre_anode"))
        self.mapper.addMapping(self.spnLongueur, self.modelPeche.fieldIndex("opep_longueur_prospec"))
        self.mapper.addMapping(self.spnLargeur, self.modelPeche.fieldIndex("opep_largeur_moy"))
        self.mapper.addMapping(self.spnSurfacePeche, self.modelPeche.fieldIndex("opep_surf_peche"))
        self.mapper.addMapping(self.spnProfondeur, self.modelPeche.fieldIndex("opep_profondeur_moy"))
        self.mapper.addMapping(self.spnPente, self.modelPeche.fieldIndex("opep_pente"))
        self.mapper.addMapping(self.txtObservation, self.modelPeche.fieldIndex("opep_observation"))
        self.mapper.addMapping(self.chkNtt, self.modelPeche.fieldIndex("opep_ntt_reel"))
        self.mapper.addMapping(self.spnNtt, self.modelPeche.fieldIndex("opep_ntt"))
        self.mapper.addMapping(self.spnIpr, self.modelPeche.fieldIndex("ipro_valeur"))

        # Opérateurs
        self.modelOperateur = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_operateur" #v_operateur est une vue dans postgresql
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelOperateur.setTable(wrelation)
        self.modelOperateur.setSort(0, Qt.AscendingOrder)

        self.modelOperateur.setHeaderData(self.modelOperateur.fieldIndex("mefe_nom"), Qt.Horizontal, u"Opérateur")

        if (not self.modelOperateur.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Opérateur dans le setupModel() : \n" + +self.modelOperateur.lastError().text(), QMessageBox.Ok)

        self.modelOperateur.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvOperateur.setModel(self.modelOperateur)
        self.tbvOperateur.setSelectionMode(QTableView.SingleSelection)
        self.tbvOperateur.setSelectionBehavior(QTableView.SelectRows)
        self.tbvOperateur.setColumnHidden(self.modelOperateur.fieldIndex("mefe_id"), True)
        self.tbvOperateur.setColumnHidden(self.modelOperateur.fieldIndex("opep_id"), True)
        self.tbvOperateur.resizeColumnsToContents()
        self.tbvOperateur.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tbvOperateur.horizontalHeader().setStretchLastSection(True)

        # Maître d'ouvrages
        self.modelMoa = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_moa_opep" #v_moa est une vue dans postgresql
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelMoa.setTable(wrelation)
        self.modelMoa.setSort(0, Qt.AscendingOrder)

        self.modelMoa.setHeaderData(self.modelMoa.fieldIndex("moa_nom"), Qt.Horizontal, u"Maître d'ouvrage")

        if (not self.modelMoa.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Maître d'ouvrage dans le setupModel() : \n" + self.modelMoa.lastError().text(), QMessageBox.Ok)

        self.modelMoa.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvMoa.setModel(self.modelMoa)
        self.tbvMoa.setSelectionMode(QTableView.SingleSelection)
        self.tbvMoa.setSelectionBehavior(QTableView.SelectRows)
        self.tbvMoa.setColumnHidden(self.modelMoa.fieldIndex("moa_id"), True)
        self.tbvMoa.setColumnHidden(self.modelMoa.fieldIndex("opep_id"), True)
        self.tbvMoa.resizeColumnsToContents()
        self.tbvMoa.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tbvMoa.horizontalHeader().setStretchLastSection(True)

        # Poissons pêchés
        self.modelPoisson = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_poisson_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelPoisson.setTable(wrelation)
        self.modelPoisson.setSort(0, Qt.AscendingOrder)

        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("esp_sigle"), Qt.Horizontal, u"Espèce")
        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("espe_population"), Qt.Horizontal, u"Population")
        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("espe_densite"), Qt.Horizontal, u"Densité")
        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("clde_val_correspond"), Qt.Horizontal, u"Correspondance (densité)")
        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("espe_biomasse"), Qt.Horizontal, u"Biomasse")
        self.modelPoisson.setHeaderData(self.modelPoisson.fieldIndex("clbi_val_correspond"), Qt.Horizontal, u"Correspondance (biomasse)")

        if (not self.modelPoisson.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Poisson dans le setupModel() : \n" + self.modelPoisson.lastError().text(), QMessageBox.Ok)

        self.modelPoisson.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvEspece.setModel(self.modelPoisson)
        self.tbvEspece.setSelectionMode(QTableView.SingleSelection)
        self.tbvEspece.setSelectionBehavior(QTableView.SelectRows)
        self.tbvEspece.setColumnHidden(self.modelPoisson.fieldIndex("esp_id"), True)
        self.tbvEspece.setColumnHidden(self.modelPoisson.fieldIndex("opep_id"), True)
        self.tbvEspece.resizeColumnsToContents()
        self.tbvEspece.horizontalHeader().setStretchLastSection(True)

        self.mapper.currentIndexChanged.connect(self.rowChange)

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        # Vérifie le verrouillage des champs impactés
        if self.chkVerrouAuto.isChecked() or self.chkVerrouModif.isChecked():
            self.verrouillage()
            self.verrouillageModif()

        # Vérification de la présence d'enregistrements
        if self.modelPeche.rowCount() == 0:
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
        self.datePeche.setDate(QDate(2000,1,1))
        self.chkComplete.setChecked(False)
        self.spnNbreAnode.setValue(0)
        self.spnLongueur.setValue(0)
        self.spnLargeur.setValue(0)
        self.spnSurfacePeche.setValue(0)
        self.spnProfondeur.setValue(0)
        self.spnPente.setValue(0)
        self.txtObservation.setText("")
        self.chkNtt.setChecked(False)
        self.spnNtt.setValue(0)
        self.spnIpr.setValue(0)
        self.chkVerrouAuto.setChecked(True)
        self.chkVerrouModif.setChecked(True)
        modelRaz = QSqlQueryModel()
        self.tbvOperateur.setModel(modelRaz)
        self.tbvMoa.setModel(modelRaz)
        self.tbvEspece.setModel(modelRaz)

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
        self.datePeche.setEnabled(active)
        self.chkComplete.setEnabled(active)
        self.spnNbreAnode.setEnabled(active)
        self.spnLongueur.setEnabled(active)
        self.spnLargeur.setEnabled(active)
        self.spnSurfacePeche.setEnabled(active)
        self.spnProfondeur.setEnabled(active)
        self.spnPente.setEnabled(active)
        self.txtObservation.setEnabled(active)
        self.chkNtt.setEnabled(active)
        self.spnNtt.setEnabled(active)
        self.spnIpr.setEnabled(active)
        self.tbvOperateur.setEnabled(active)
        self.cmbCondition.setEnabled(active)
        self.cmbIpr.setEnabled(active)
        self.cmbMotif.setEnabled(active)
        self.cmbRiviere.setEnabled(active)
        self.cmbStation.setEnabled(active)
        self.tbvEspece.setEnabled(active)
        self.tbvMoa.setEnabled(active)
        self.chkVerrouAuto.setEnabled(active)
        self.chkVerrouModif.setEnabled(active)

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
        self.btnExcel.setEnabled(active)
        self.btnAjoutFiche.setEnabled(False)
        self.btnRetraitFiche.setEnabled(False)
        self.btnStation.setEnabled(True)

        self.btnPente.setEnabled(False)

        self.btnAjoutMoa.setEnabled(active)
        self.btnSuppMoa.setEnabled(active)
        self.btnAjoutOperateur.setEnabled(active)
        self.btnSuppOperateur.setEnabled(active)
        self.btnAjoutPoisson.setEnabled(active)
        self.btnSuppPoisson.setEnabled(active)

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

        self.btnPremier.setEnabled(not active)
        self.btnPrec.setEnabled(not active)
        self.btnSuiv.setEnabled(not active)
        self.btnDernier.setEnabled(not active)

        self.btnZoom.setEnabled(not active)
        self.btnSelection.setEnabled(not active)
        self.btnExcel.setEnabled(not active)
        self.btnAjoutFiche.setEnabled(active)
        self.btnRetraitFiche.setEnabled(active)
        self.btnStation.setEnabled(True)

        self.btnAjoutMoa.setEnabled(not active)
        self.btnSuppMoa.setEnabled(not active)
        self.btnAjoutOperateur.setEnabled(not active)
        self.btnSuppOperateur.setEnabled(not active)
        self.btnAjoutPoisson.setEnabled(not active)
        self.btnSuppPoisson.setEnabled(not active)

        self.btnPente.setEnabled(active)

        self.btnNouveau.setEnabled(not active)
        self.btnModif.setEnabled(not active)
        self.btnSupprimer.setEnabled(not active)
        self.btnEnregistrer.setEnabled(active)
        self.btnAnnuler.setEnabled(active)

    def saveRecord(self, wfrom):
        '''Permet le passage d'un enregistrement à un autre en fonction du bouton de défilement'''

        row = self.mapper.currentIndex()

        if wfrom == "first":
            row = 0
        elif wfrom == "prev":
            row = 0 if row <= 1 else row - 1
        elif wfrom == "next":
            row += 1
            if row >= self.modelPeche.rowCount():
                row = self.modelPeche.rowCount() - 1
        elif wfrom == "last":
            row = self.modelPeche.rowCount() - 1

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
        self.btnSuiv.setEnabled(row < self.modelPeche.rowCount() - 1)

        self.cmbRiviere.currentIndexChanged.disconnect(self.changeCmbRiviere)

        record = self.modelPeche.record(row)
        wopep_ope_code = record.value(self.modelPeche.fieldIndex("opep_ope_code"))

        # Récupération de la clé de l'operation correspondante
        query = QSqlQuery(self.db)
        wrelation = "operation"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("select ope_sta_id from " + wrelation + " where ope_code = ?")
        query.addBindValue(wopep_ope_code)
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
            QMessageBox.critical(self, u"Remplissage du modèle ", u"Erreur au modèle Station dans le rowChange() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)

        self.cmbStation.setModel(self.modelStation)
        self.cmbStation.setModelColumn(1)

        # Sélection station
        result = self.cmbStation.model().match(self.cmbStation.model().index(0, 0), Qt.EditRole, wope_sta_id, -1, Qt.MatchExactly)
        if result:
            self.cmbStation.setCurrentIndex(result[0].row())

        # Filtrage condition
        record = self.modelPeche.record(row)
        wopep_cope_id = record.value(self.modelPeche.fieldIndex("opep_cope_id"))
        self.modelCondition.clear()
        wrelation = "condition_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelCondition.setQuery("select cope_id, cope_condition from " + wrelation + " order by cope_condition;", self.db)

        if self.modelCondition.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Condition dans le rowChange() : \n" + self.modelCondition.lastError().text(), QMessageBox.Ok)

        self.cmbCondition.setModel(self.modelCondition)
        self.cmbCondition.setModelColumn(1)

        # Sélection condition
        result = self.cmbCondition.model().match(self.cmbCondition.model().index(0, 0), Qt.EditRole, wopep_cope_id, -1, Qt.MatchExactly)
        if result:
            self.cmbCondition.setCurrentIndex(result[0].row())

        # Filtrage motif
        record = self.modelPeche.record(row)
        wopep_mope_id = record.value(self.modelPeche.fieldIndex("opep_mope_id"))
        self.modelMotif.clear()
        wrelation = "motif_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelMotif.setQuery("select mope_id, mope_motif from " + wrelation + " order by mope_motif;", self.db)

        if self.modelMotif.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Motif dans le rowChange() : \n" + self.modelMotif.lastError().text(), QMessageBox.Ok)

        self.cmbMotif.setModel(self.modelMotif)
        self.cmbMotif.setModelColumn(1)

        # Sélection motif
        result = self.cmbMotif.model().match(self.cmbMotif.model().index(0, 0), Qt.EditRole, wopep_mope_id, -1, Qt.MatchExactly)
        if result:
            self.cmbMotif.setCurrentIndex(result[0].row())

       # Filtrage IPR
        record = self.modelPeche.record(row)
        wopep_ipr_id = record.value(self.modelPeche.fieldIndex("opep_ipr_id"))
        self.modelIpr.clear()
        wrelation = "ipr"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelIpr.setQuery("select ipr_id, ipr_correspondance from " + wrelation + " order by ipr_correspondance;", self.db)

        if self.modelIpr.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle IPR dans le rowChange() : \n" + self.modelIpr.lastError().text(), QMessageBox.Ok)

        self.cmbIpr.setModel(self.modelIpr)
        self.cmbIpr.setModelColumn(1)

        # Sélection IPR
        result = self.cmbIpr.model().match(self.cmbIpr.model().index(0, 0), Qt.EditRole, wopep_ipr_id, -1, Qt.MatchExactly)
        if result:
            self.cmbIpr.setCurrentIndex(result[0].row())

        # Opérateurs
        id = record.value("opep_id")
        self.modelOperateur.setFilter("opep_id = %i" % id)

        # Maitres d'ouvrage
        id = record.value("opep_id")
        self.modelMoa.setFilter("opep_id = %i" % id)

        # Espèces pêchées
        id = record.value("opep_id")
        self.modelPoisson.setFilter("opep_id = %i" % id)

        self.afficheInfoRow()

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.verrouillage()
        self.verrouillageModif()

        # Vérifie la présence d'une géométrie
        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelPeche.record(row)
                wid = record.value("opep_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
                request = QgsFeatureRequest().setFilterFids([wid])

                it = layer.getFeatures(request)
                extent = None
                for x in it:
                    extent = x.geometry()
                if extent == None:
                    self.iface.messageBar().pushMessage("Attention : ", u"Cette pêche électrique ne possède pas de géométrie.", level= QgsMessageBar.WARNING, duration = 5)

    def zoomPeche(self):
        '''Permet de zoomer le canevas de la carte sur la pêche courante'''

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelPeche.record(row)
                wid = record.value("opep_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
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

    def selectionPeche(self):
        '''Permet de sélectionner la pêche correspondant à l'enregistrement courant'''

        if self.mapper:
            row = self.mapper.currentIndex()
            self.etat_courant = 10
            if row >= 0:
                record = self.modelPeche.record(row)
                wid = record.value("opep_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
                layer.removeSelection()
                layer.select(wid)
                self.etat_courant = 0

    def openTableur(self):
        '''Permet d'ouvrir le fichier liée à la pêche'''

        row = self.mapper.currentIndex()
        record = self.modelPeche.record(row)
        lienTableur = record.value(u"opep_excel")
        if lienTableur == "" or lienTableur == None:
            self.iface.messageBar().pushMessage("Info : ", u"Pas de fichier joint !", level= QgsMessageBar.INFO, duration = 5)
        else :
            try:
                os.startfile(lienTableur)
            except:
                self.iface.messageBar().pushMessage("Info : ", u"Le fichier est introuvable !", level= QgsMessageBar.WARNING, duration = 5)

    def ajoutFiche(self):
        '''Permet de joindre un fichier externe à la pêche'''

        openfile = ""
        openfile = QFileDialog.getOpenFileName(self)
        if openfile != "":
            self.cheminExcel = unicode(openfile)
            self.excelBool = True

    def retraitFiche(self):
        '''Permet de retirer un fichier externe à la pêche'''
        if QMessageBox.question(self, u"Délier", u"Etes-vous certain de vouloir délier le fichier ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.cheminExcel = ""
            self.excelBool = True

    def supprimer(self):
        '''Permet de supprimer la pêche courante ainsi que toutes les données liées (cascade)'''

        filtreCourant = self.modelPeche.filter()

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                if QMessageBox.question(self, "Suppression", u"Etes-vous certain de vouloir supprimer cette pêche électrique ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    record = self.modelPeche.record(row)
                    wid = record.value("opep_ope_code")

                    query = QSqlQuery(self.db)

                    wrelation = "operation"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                    query.addBindValue(wid)
                    if not query.exec_():
                        QMessageBox.critical(self, "Erreur", u"Impossible de supprimer cette pêche ...", QMessageBox.Ok)

                    if filtreCourant != "":
                        filtreCourant = filtreCourant.replace(str(wid), "NULL" )

                    self.setupModel()

                    if filtreCourant != "":
                        self.modelPeche.setFilter(filtreCourant)
                        self.row_count = self.modelPeche.rowCount()
                        if self.row_count != 0:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Pêche électrique"
                            self.mapper.toFirst()
                            self.btnDeleteFiltrage.setEnabled(True)

    def nouveau(self):
        '''Prépare le formulaire pour la saisie d'une nouvelle pêche'''

        self.boolNew = True
        layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        layer.removeSelection()
        self.peche_annule_filtrage()
        self.cmbRiviere.setCurrentIndex(-1)

        self.activeButtonsModif(True)
        self.clearFields()
        self.activeFields(True)

        # Initialise le champs date à la date du jour
        dateDay = QDate.currentDate()
        self.datePeche.setDate(dateDay)

        self.chkVerrouModif.setChecked(False)
        self.verrouillage()

    def annuler(self, repositionnement = True):
        '''Annule la saisie d'une nouvelle station'''

        self.activeButtonsModif(False)
        self.btnFiltreCartoManuel.setEnabled(False)
        self.btnDeleteFiltrage.setEnabled(False)

        self.mapper.revert()

        self.boolNew = False

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
        '''Enregistre la pêche nouvellement créée'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopep_station = wrecord.value(0)

            wopep_ope_code = self.leCodeOpe.text()

            value = self.datePeche.date()
            wopep_date  = QDate.toString(value, "yyyy-MM-dd")

            if self.chkComplete.isChecked() :
                wopep_complet = True
            else:
                wopep_complet = False

            wopep_anode = self.spnNbreAnode.value()

            wrecord = self.cmbCondition.model().record(self.cmbCondition.currentIndex())
            wopep_condition = wrecord.value(0)

            wrecord = self.cmbMotif.model().record(self.cmbMotif.currentIndex())
            wopep_motif = wrecord.value(0)

            wopep_longueur =self.spnLongueur.value()

            wopep_largeur = self.spnLargeur.value()

            wopep_surface = self.spnSurfacePeche.value()

            wopep_profondeur = self.spnProfondeur.value()

            wopep_pente = self.spnPente.value()

            wopep_comm = self.txtObservation.toPlainText()

            wopep_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopep_excel = ""
                else :
                    wopep_excel = self.cheminExcel
                    self.excelBool = False
            else :
                wopep_excel = ""

            if self.chkNtt.isChecked() :
                wopep_ntt = True
            else:
                wopep_ntt = False

            wopep_valntt = self.spnNtt.value()

            wopep_valipr = self.spnIpr.value()

            wrecord = self.cmbIpr.model().record(self.cmbIpr.currentIndex())
            wopep_ipr = wrecord.value(0)

            record = self.modelStation.record(self.cmbStation.currentIndex())
            wsta_id = record.value(0)
            queryCoord = QSqlQuery(self.db)
            wrelation = "station"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryCoord.prepare("SELECT sta_geom FROM " + wrelation + " WHERE sta_id = " + str(wsta_id))
            if not queryCoord.exec_():
                QMessageBox.critical(self, u"Erreur - Récupération de la géométrie de la Station", queryCoord.lastError().text(), QMessageBox.Ok)

            if queryCoord.exec_():
                if queryCoord.next():
                    wsta_geom = queryCoord.value(0)

            # Création du code opération
            queryFk = QSqlQuery(self.db)
            wrelation = "operation"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryFk.prepare("INSERT INTO " + wrelation + " (ope_code, ope_sta_id) VALUES (?, ?)")
            queryFk.addBindValue(wopep_ope_code)
            queryFk.addBindValue(wopep_station)
            if not queryFk.exec_():
                QMessageBox.critical(self, u"Erreur - création de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

            # Création de la requête d'enregistrement
            query = QSqlQuery(self.db)
            wrelation = "ope_peche_elec"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("INSERT INTO " + wrelation + " (opep_date, opep_complet_partielle, opep_nbre_anode, opep_longueur_prospec, opep_profondeur_moy, " +
            "opep_largeur_moy, opep_surf_peche, opep_ntt, opep_ntt_reel, opep_observation, opep_pente, opep_excel, opep_ope_code, opep_mope_id, opep_cope_id, opep_ipr_id, " +
            "ipro_valeur, opep_geom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )")
            query.addBindValue(wopep_date)
            query.addBindValue(wopep_complet)
            query.addBindValue(wopep_anode)
            query.addBindValue(wopep_longueur)
            query.addBindValue(wopep_profondeur)
            query.addBindValue(wopep_largeur)
            query.addBindValue(wopep_surface)
            query.addBindValue(wopep_valntt)
            query.addBindValue(wopep_ntt)
            query.addBindValue(wopep_comm)
            query.addBindValue(wopep_pente)
            query.addBindValue(wopep_excel)
            query.addBindValue(wopep_ope_code)
            query.addBindValue(wopep_motif)
            query.addBindValue(wopep_condition)
            query.addBindValue(wopep_ipr)
            query.addBindValue(wopep_valipr)
            query.addBindValue(wsta_geom)

            if not query.exec_():
                querySupp = QSqlQuery(self.db)
                wrelation = "operation"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                querySupp.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                querySupp.addBindValue(wopep_ope_code)
                if not querySupp.exec_():
                    QMessageBox.critical(self, u"Erreur - Suppression de l'opération", querySupp.lastError().text(), QMessageBox.Ok)

                QMessageBox.critical(self, u"Erreur - Création de la pêche", query.lastError().text(), QMessageBox.Ok)

            else:
                # Màj du nombre d'enregistrement
                self.row_count += 1
                if self.row_count == 1:
                    self.modelPeche.select()

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
            self.saveRecord("last") #renvoie sur le dernier enregistrement
            self.boolNew = False

    def modification(self):
        '''Permet la modification de la station courante'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopep_station = wrecord.value(0)

            wopep_ope_code = self.leCodeOpe.text()

            value = self.datePeche.date()
            wopep_date  = QDate.toString(value, "yyyy-MM-dd")

            if self.chkComplete.isChecked() :
                wopep_complet = True
            else:
                wopep_complet = False

            wopep_anode = self.spnNbreAnode.value()

            wrecord = self.cmbCondition.model().record(self.cmbCondition.currentIndex())
            wopep_condition = wrecord.value(0)

            wrecord = self.cmbMotif.model().record(self.cmbMotif.currentIndex())
            wopep_motif = wrecord.value(0)

            wopep_longueur =self.spnLongueur.value()

            wopep_largeur = self.spnLargeur.value()

            wopep_surface = self.spnSurfacePeche.value()

            wopep_profondeur = self.spnProfondeur.value()

            wopep_pente = self.spnPente.value()

            wopep_comm = self.txtObservation.toPlainText()

            wopep_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopep_excel = ""
                else :
                    wopep_excel = self.cheminExcel
                    self.excelBool = False
            else :
                row = self.mapper.currentIndex()
                record = self.modelPeche.record(row)
                self.cheminExcel = record.value(u"opep_excel")
                wopep_excel = self.cheminExcel

            if self.chkNtt.isChecked() :
                wopep_ntt = True
            else:
                wopep_ntt = False

            wopep_valntt = self.spnNtt.value()

            wopep_valipr = self.spnIpr.value()

            wrecord = self.cmbIpr.model().record(self.cmbIpr.currentIndex())
            wopep_ipr = wrecord.value(0)

            record = self.modelStation.record(self.cmbStation.currentIndex())
            wsta_id = record.value(0)
            queryCoord = QSqlQuery(self.db)
            wrelation = "station"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryCoord.prepare("SELECT sta_geom FROM " + wrelation + " WHERE sta_id = " + str(wsta_id))
            if not queryCoord.exec_():
                QMessageBox.critical(self, u"Erreur queryCoord- Récupération de la géométrie de la Station", queryCoord.lastError().text(), QMessageBox.Ok)

            if queryCoord.exec_():
                if queryCoord.next():
                    wsta_geom = queryCoord.value(0)
            else :
                wsta_geom = ""

            if wsta_geom != "":
                # Création de la requête de mise à jour
                if QMessageBox.question(self, "Enregistrer", u"Etes-vous certain de vouloir enregistrer les modifications ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

                    filtreCourant = self.modelPeche.filter()

                    queryFk = QSqlQuery(self.db)
                    wrelationFk = "operation"
                    if self.dbType == "postgres":
                        wrelationFk = self.dbSchema + "." + wrelationFk
                    queryFk.prepare("UPDATE " + wrelationFk + " SET ope_code = '" + str(wopep_ope_code) + "', ope_sta_id = " + str(wsta_id) + "WHERE ope_code = '" + self.codeOpe + "'")
                    if not queryFk.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification du code de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

                    query = QSqlQuery(self.db)
                    wrelation = "ope_peche_elec"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET opep_date = '" + wopep_date + "', opep_complet_partielle = " + str(wopep_complet) + ", opep_nbre_anode = " + str(wopep_anode) +
                    ", opep_longueur_prospec = " + str(wopep_longueur) + ", opep_profondeur_moy = " + str(wopep_profondeur) + ", opep_largeur_moy = " + str(wopep_largeur) +
                    ", opep_surf_peche = " + str(wopep_surface) + ", opep_ntt = " + str(wopep_valntt) + ", opep_ntt_reel = " + str(wopep_ntt) + ", opep_observation = '" + wopep_comm +
                    "', opep_pente = " + str(wopep_pente) + ", opep_excel = '" + wopep_excel + "', opep_ope_code = '" + wopep_ope_code + "', opep_mope_id = " + str(wopep_motif) +
                    ", opep_cope_id = " + str(wopep_condition) + ", opep_ipr_id = " + str(wopep_ipr) + ", ipro_valeur = " + str(wopep_valipr) +
                    ", opep_geom = '" + wsta_geom + "' WHERE opep_ope_code = '" + wopep_ope_code + "'")

                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification de la pêche", query.lastError().text(), QMessageBox.Ok)

            else:
                QMessageBox.critical(self, u"Erreur - Récupération de la géométrie de la Station", queryCoord.lastError().text(), QMessageBox.Ok)

            # Suppression des marqueurs sur le canevas
            if self.point_click_1 != "":
                self.mc.scene().removeItem(self.point_click_1)
                self.point_click_1 = ""
            if self.point_click_2 != "":
                self.mc.scene().removeItem(self.point_click_2)
                self.point_click_2 = ""

            # Basculement du formulaire vers la visualisation
            self.chkVerrouModif.setChecked(True)
            self.mc.refresh()
            # self.saveRecord("last") #renvoie sur le dernier enregistrement
            self.setupModel()

            if filtreCourant != "":
                self.modelPeche.setFilter(filtreCourant)
                self.row_count = self.modelPeche.rowCount()
                if self.row_count != 0:
                    self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Pêche électrique"
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
        else:
            saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

    def calculCoordonnee(self):
        '''Permet de récupérer le clic sur le canevas'''

        if self.spnLongueur.value() == 0:
            self.iface.messageBar().pushMessage("Attention : ", u"Pour calculer une pente vous devez saisir une longueur !", level = QgsMessageBar.WARNING, duration = 5)
            self.btnPente.setChecked(False)
        else:
            self.clic = 0
            self.pointOk = False
            self.penteBool = False
            if self.btnPente.isChecked():
                self.penteBool = True
                self.clickTool.canvasClicked.connect(self.handleMouseDown)
                self.mc.setMapTool(self.clickTool)
            else:
                self.mc.setMapTool(self.pan)

    def handleMouseDown(self, point):
        '''
        Récupère le point cliqué dans calculCoordonnee() et
        permet la saisie auto de certains champs du formulaire

        :param point: point issu du clic sur le canevas
        :type point: QgsPoint
        '''
        # Récupération des clics
        if self.penteBool == True:
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
                self.btnPente.setChecked(False)
                self.clickTool.canvasClicked.disconnect(self.saisieAuto)
                self.iface.messageBar().pushMessage("Erreur : ", u"Deux point déjà cliqués, réactiver le bouton pour recommencer !", level= QgsMessageBar.WARNING, duration = 5)

            # Reprojection des points si nécessaires
            if self.pointOk == True :
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                pt1 = ""
                pt2 = ""
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


                if pt1 != "" and pt2 != "":
                    # Import virtuel de la table cours_eau
                    uri = QgsDataSourceURI()
                    uri.setConnection("localhost", "5432", self.dbname, self.password, self.user)
                    uri.setDataSource("data", "cours_eau", "ceau_geom")
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

                    # Import virtuel du MNT
                    fileName = self.cheminRaster + "/mnt10_cantal.tif"
                    fileInfo = QFileInfo(fileName)
                    baseName = fileInfo.baseName()
                    rlayer = QgsRasterLayer(fileName, baseName)
                    if not rlayer.isValid():
                        self.iface.messageBar().pushMessage("Erreur : ", u"Layer failed to load !", level= QgsMessageBar.CRITICAL, duration = 5)
                    else :
                        # Récupération des valeurs d'altitudes aux deux points corrigés
                        ident_1 = rlayer.dataProvider().identify(QgsPoint(pt1), QgsRaster.IdentifyFormatValue)
                        ident_2 = rlayer.dataProvider().identify(QgsPoint(pt2), QgsRaster.IdentifyFormatValue)
                        if ident_1.isValid():
                          dico1 = ident_1.results()
                          alti_1 = dico1[1]
                        else:
                            self.iface.messageBar().pushMessage("Erreur : ", u"Altitude du point 1 non récupérée !", level= QgsMessageBar.CRITICAL, duration = 5)
                        if ident_2.isValid():
                          dico2 = ident_2.results()
                          alti_2 = dico2[1]
                        else:
                            self.iface.messageBar().pushMessage("Erreur : ", u"Altitude du point 2 non récupérée !", level= QgsMessageBar.CRITICAL, duration = 5)
                    pente = 0
                    # Calcul de la pente
                    pente = (abs(float(alti_1) - float(alti_2))/self.longueur)*100
                    if pente != 0:
                        self.spnPente.setValue(pente)
                    else:
                        self.spnPente.setValue(0)
                        self.iface.messageBar().pushMessage("Info : ", u"La pente calculée est de 0% !", level= QgsMessageBar.WARNING, duration = 5)

                else:
                    self.iface.messageBar().pushMessage("Erreur : ", u"Aucune coordonnée (erreur aux pt1 et / ou pt2) !", level= QgsMessageBar.CRITICAL, duration = 5)
                self.mc.setMapTool(self.pan)
                QApplication.restoreOverrideCursor()
                self.clic = 0
                self.pointOk = False
                self.penteBool = False
                self.btnPente.setChecked(False)
                self.clickTool.canvasClicked.disconnect()
            elif self.clic != 1 :
                self.iface.messageBar().pushMessage("Erreur : ", u"La récupération du ou des clic(s) a échouée !", level= QgsMessageBar.CRITICAL, duration = 5)

    def saisieAuto(self):
        '''Permet la saisie automatique de certains champs'''

        longueur = self.spnLongueur.value()
        self.longueur = longueur
        largeur = self.spnLargeur.value()
        surface = longueur * largeur
        self.spnSurfacePeche.setValue(surface)

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

        dialog = Filtrage_peche_dialog(self.db, self.dbType, self.dbSchema, self.modelPeche)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.row_count = self.modelPeche.rowCount()
            if self.row_count != 0:
                self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Pêche électrique"
                self.mapper.toFirst()
                self.btnDeleteFiltrage.setEnabled(True)

    def ajoutMoa(self):
        '''Permet l'ouverture de la fenêtre pour ajouter un maître d'ouvrage'''

        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")
        dialog = Ope_moa_ajout_dialog(self.db, self.dbType, self.dbSchema, wopep_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelMoa.setFilter("opep_id = %i" % wopep_id)

    def suppMoa(self):
        '''Permet de supprimer le maître d'ouvrage sélectionné'''

        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")

        index = self.tbvMoa.currentIndex()
        if not index.isValid():
            return
        if QMessageBox.question(self, u"Suppression du maître d'ouvrage", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            query = QSqlQuery(self.db)

            wope_code = self.leCodeOpe.text()
            wrelation = "ope_peche_elec"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("SELECT opep_id FROM " + wrelation + " WHERE opep_ope_code = '" + wope_code + "'")
            if query.exec_():
                if query.next():
                    wopep_id = query.value(0)

            wid = ""
            selection = self.tbvMoa.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            if wid != "":
                wrelation = "real_peche_elec"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("DELETE FROM " + wrelation + " WHERE rp_opep_id = '" + str(wopep_id) + "' and rp_moa_id = '" + str(wid) + "'")
            if not query.exec_():
                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce maître d'ouvrage ...", QMessageBox.Ok)
            self.modelMoa.setFilter("opep_id = %i" % wopep_id)

    def ajoutOperateur(self):
        '''Permet l'ouverture de la fenêtre pour ajouter un opérateur'''

        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")
        dialog = Ope_operateur_ajout_dialog(self.db, self.dbType, self.dbSchema, wopep_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelOperateur.setFilter("opep_id = %i" % wopep_id)

    def suppOperateur(self):
        '''Permet de supprimer l'opérateur sélectionné'''

        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")

        index = self.tbvOperateur.currentIndex()
        if not index.isValid():
            return
        if QMessageBox.question(self, u"Suppression de l'opérateur", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            query = QSqlQuery(self.db)

            wope_code = self.leCodeOpe.text()
            wrelation = "ope_peche_elec"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("SELECT opep_id FROM " + wrelation + " WHERE opep_ope_code = '" + wope_code + "'")
            if query.exec_():
                if query.next():
                    wopep_id = query.value(0)

            wid = ""
            selection = self.tbvOperateur.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            wrelation = "operateur_fede"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("DELETE FROM " + wrelation + " WHERE opfe_opep_id = '" + str(wopep_id) + "' and opfe_mefe_id = '" + str(wid) + "'")
            if not query.exec_():
                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer cet opérateur ...", QMessageBox.Ok)

            self.modelOperateur.setFilter("opep_id = %i" % wopep_id)

    def ajoutPeche(self):
        '''Permet l'ouverture de la fenêtre pour ajouter une espèce pêchée'''

        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")
        dialog = Ope_peche_ajout_dialog(self.db, self.dbType, self.dbSchema, wopep_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelPoisson.setFilter("opep_id = %i" % wopep_id)

    def suppPeche(self):
        '''Permet de supprimer une espèce pêchée, sélectionné'''
        record = self.modelPeche.record(self.row_courant)
        wopep_id = record.value("opep_id")

        index = self.tbvEspece.currentIndex()
        if not index.isValid():
            return
        if QMessageBox.question(self, u"Suppression de l'espèce", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            query = QSqlQuery(self.db)

            wope_code = self.leCodeOpe.text()
            wrelation = "ope_peche_elec"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("SELECT opep_id FROM " + wrelation + " WHERE opep_ope_code = '" + wope_code + "'")
            if query.exec_():
                if query.next():
                    wopep_id = query.value(0)

            wid = ""
            selection = self.tbvEspece.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            wrelation = "espece_peche"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("DELETE FROM " + wrelation + " WHERE espe_opep_id = '" + str(wopep_id) + "' and espe_esp_id = '" + str(wid) + "'")
            if not query.exec_():
                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer cette espèce ...", QMessageBox.Ok)
            self.modelPoisson.setFilter("opep_id = %i" % wopep_id)

    def verrouillage(self):
        '''Verrouille les champs de saisie automatique si coché'''

        if self.chkVerrouAuto.isChecked():
            self.spnSurfacePeche.setEnabled(False)
            self.spnPente.setEnabled(False)
        else:
            self.spnSurfacePeche.setEnabled(True)
            self.spnPente.setEnabled(True)

    def verrouillageModif(self):
        '''Verrouille les champs afin d'éviter les modifications intempestive'''

        if self.chkVerrouModif.isChecked():
            self.leCodeOpe.setEnabled(False)
            self.datePeche.setEnabled(False)
            self.chkComplete.setEnabled(False)
            self.spnNbreAnode.setEnabled(False)
            self.spnLongueur.setEnabled(False)
            self.spnLargeur.setEnabled(False)
            self.spnProfondeur.setEnabled(False)
            self.txtObservation.setEnabled(False)
            self.chkNtt.setEnabled(False)
            self.spnNtt.setEnabled(False)
            self.spnIpr.setEnabled(False)
            self.cmbCondition.setEnabled(False)
            self.cmbIpr.setEnabled(False)
            self.cmbMotif.setEnabled(False)
            self.cmbRiviere.setEnabled(False)
            self.cmbStation.setEnabled(False)
            self.btnPente.setEnabled(False)
            self.btnAjoutFiche.setEnabled(False)
            self.btnRetraitFiche.setEnabled(False)
            self.btnExcel.setEnabled(True)
            if self.boolNew == False:
                self.btnModif.setEnabled(False)
        else:
            self.leCodeOpe.setEnabled(True)
            self.datePeche.setEnabled(True)
            self.chkComplete.setEnabled(True)
            self.spnNbreAnode.setEnabled(True)
            self.spnLongueur.setEnabled(True)
            self.spnLargeur.setEnabled(True)
            self.spnProfondeur.setEnabled(True)
            self.txtObservation.setEnabled(True)
            self.chkNtt.setEnabled(True)
            self.spnNtt.setEnabled(True)
            self.spnIpr.setEnabled(True)
            self.cmbCondition.setEnabled(True)
            self.cmbIpr.setEnabled(True)
            self.cmbMotif.setEnabled(True)
            self.cmbRiviere.setEnabled(True)
            self.cmbStation.setEnabled(True)
            self.btnPente.setEnabled(True)
            self.btnAjoutFiche.setEnabled(True)
            self.btnRetraitFiche.setEnabled(True)
            self.btnExcel.setEnabled(False)
            if self.boolNew == False:
                self.btnModif.setEnabled(True)
            self.codeOpe = self.leCodeOpe.text()

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
    def __init__(self, db, dbType, dbSchema, wopep_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage de la combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wopep_id: identifiant de la pêche courante
        :type wopep_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ope_moa_ajout_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wopep_id = wopep_id
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
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Maître d'ouvrage dans le Ope_moa_ajout_dialog.__init__() : \n" + self.model.lastError().text(), QMessageBox.Ok)

        self.cmbMoa.setModel(self.model)
        self.cmbMoa.setModelColumn(1)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def accept(self):
        '''Enregistre le maître d'ouvrage comme lié à la pêche'''

        wrecord = self.cmbMoa.model().record(self.cmbMoa.currentIndex())
        wmoa = wrecord.value(0)

        query = QSqlQuery(self.db)

        wrelation = "real_peche_elec"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("INSERT INTO " + wrelation + " (rp_opep_id, rp_moa_id) VALUES (?, ?)")
        query.addBindValue(self.wopep_id)
        query.addBindValue(wmoa)
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur - Ajout du maître d'ouvrage", query.lastError().text(), QMessageBox.Ok)
        else:
            QDialog.accept(self)

class Ope_operateur_ajout_dialog(QDialog, Ui_dlgOperateurAjoutForm):
    '''
    Class de la fenêtre permettant d'ajouter un maître d'ouvrage

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgOperateurAjoutForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgOperateurAjoutForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wopep_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage de la combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wopep_id: identifiant de la pêche courante
        :type wopep_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ope_operateur_ajout_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wopep_id = wopep_id
        self.setupUi(self)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

        self.model = QSqlTableModel(self, self.db)

        wrelation = "membre_fede"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.model.setTable(wrelation)
        self.model.setSort(1, Qt.AscendingOrder)
        if (not self.model.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Membre fédération dans le Ope_operateur_ajout_dialog.__init__() : \n" + self.model.lastError().text(), QMessageBox.Ok)

        self.cmbOperateur.setModel(self.model)
        self.cmbOperateur.setModelColumn(1)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def accept(self):
        '''Enregistre l'opérateur comme lié à la pêche'''

        wrecord = self.cmbOperateur.model().record(self.cmbOperateur.currentIndex())
        woperateur = wrecord.value(0)

        query = QSqlQuery(self.db)

        wrelation = "operateur_fede"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("INSERT INTO " + wrelation + " (opfe_opep_id, opfe_mefe_id) VALUES (?, ?)")
        query.addBindValue(self.wopep_id)
        query.addBindValue(woperateur)
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur - Ajout de l'opérateur", query.lastError().text(), QMessageBox.Ok)
        else:
            QDialog.accept(self)

class Ope_peche_ajout_dialog(QDialog, Ui_dlgPecheSaisieForm):
    '''
    Class de la fenêtre permettant d'ajouter un maître d'ouvrage

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgPecheSaisieForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgPecheSaisieForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wopep_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage de la combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wopep_id: identifiant de la pêche courante
        :type wopep_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ope_peche_ajout_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wopep_id = wopep_id
        self.setupUi(self)
        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

        self.model = QSqlTableModel(self, self.db)

        wrelation = "espece"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.model.setTable(wrelation)
        self.model.setSort(1, Qt.AscendingOrder)
        if (not self.model.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Espèce dans le Ope_peche_ajout_dialog.__init__() : \n" +self.model.lastError().text(), QMessageBox.Ok)

        self.cmbEspece.setModel(self.model)
        self.cmbEspece.setModelColumn(1)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def accept(self):
        '''Enregistre l'espèce comme lié à la pêche'''

        wrecord = self.cmbEspece.model().record(self.cmbEspece.currentIndex())
        wespece = wrecord.value(0)

        wquantite = self.spnQuantite.value()

        wdensite = self.spnDensite.value()

        wbiomasse = self.spnBiomasse.value()

        query = QSqlQuery(self.db)

        wrelation = "espece_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("INSERT INTO " + wrelation + " (espe_esp_id, espe_opep_id, espe_population, espe_densite, espe_biomasse) VALUES (?, ?, ?, ?, ?)")
        query.addBindValue(wespece)
        query.addBindValue(self.wopep_id)
        query.addBindValue(wquantite)
        query.addBindValue(wdensite)
        query.addBindValue(wbiomasse)

        if not query.exec_():
            QMessageBox.critical(self, u"Erreur - Saisie d'une pêche", query.lastError().text(), QMessageBox.Ok)
        else:
            QDialog.accept(self)

class Fiche_station(QDialog, Ui_dlgStationForm):
    '''
    Class de la fenêtre permettant d'ajouter un maître d'ouvrage

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
