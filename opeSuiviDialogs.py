# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du formulaire "Suivis thermiques" du plugin.

# Import des modules Python, PyQt5 et QGIS nécessaire à l'exécution de ce fichier
import sys
import os
import csv
from functools import partial
from PyQt5.QtCore import (Qt, QDate)
from PyQt5.QtGui import (QCursor, QPixmap)
from PyQt5.QtWidgets import (QApplication, QDataWidgetMapper, QDialog, QFileDialog, QDockWidget, QHeaderView, QMessageBox, QTableView)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel)
from qgis.core import (QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDataSourceUri, QgsExpression, QgsExpressionContext, QgsFeatureRequest,  QgsGeometry, QgsProject, QgsPoint, QgsRaster, QgsRasterLayer, QgsVectorDataProvider, QgsVectorLayer)
from qgis.gui import (QgsMapToolPan, QgsMessageBar, QgsMapToolEmitPoint, QgsVertexMarker)

# Initialise les ressources Qt à partir du fichier resources.py
from .resources_rc import *

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")


# Import des scripts Python des interfaces graphiques nécessaire
from opeSuiviThermiForm import (Ui_dwcThermiMainForm)
from opeStationForm import (Ui_dlgStationForm)
from opeMoaAjoutForm import (Ui_dlgMoaAjoutForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

# Import du script de filtrage des suivis thermiques
from .opeSuiviFiltrage import (Filtrage_thermi_dialog)

class Suivi_thermi_dialog(QDockWidget, Ui_dwcThermiMainForm):
    '''
    Class principal du formulaire "Suivis thermiques"

    :param QDockWidget: Permet d'ancrer le formulaire comme définit dans gedopiMenu
    :type QDockWidget: QDockWidget

    :param Ui_dwcThermiMainForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dwcThermiMainForm: class
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
        self.pan= QgsMapToolPan(self.mc)

        # Méthodes communes
        self.gc = Gedopi_common(self)

        # Variables de connexion à la base de données
        self.db = None
        self.dbType = ""
        self.dbSchema = ""

        # Variables de stockage des données
        self.layer = None
        self.modelThermi = None
        self.mapper = None
        self.modelStation = None
        self.modelRiviere = None
        self.modelMoa = None

        # Variables diverses
        self.excelBool = False
        self.boolNew = False
        self.saisieAutoBool = False
        self.point_click = ""
        self.pointThermi = ""
        self.cheminCsv = ""
        self.wthermi_geom = ""
        self.creaGeom = False

        # Slot pour le filtrage cartographique
        self.slot_thermi_select_changed = None
        slot = partial(self.thermi_select_changed, 2)

        # Connexion des événements
        self.btnFiltreCartoManuel.clicked.connect(slot)
        self.btnFiltreAttributaire.clicked.connect(self.filtreAttributaire)
        self.btnDeleteFiltrage.clicked.connect(self.thermi_annule_filtrage)

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.btnAjoutMoa.clicked.connect(self.ajoutMoa)
        self.btnSuppMoa.clicked.connect(self.suppMoa)

        self.btnCoordonnee.clicked.connect(self.calculCoordonnee)
        self.btnCoordonnee.setCheckable(True)

        self.btnImpCsv.clicked.connect(self.importCsv)

        self.btnZoom.clicked.connect(self.zoomThermi)
        self.btnSelection.clicked.connect(self.selectionThermi)
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

        self.chkVerrouAuto.stateChanged.connect(self.verrouillage)
        self.chkVerrouModif.stateChanged.connect(self.verrouillageModif)

        # Initialisation du nombre de page du formulaire
        self.row_courant = 0
        self.row_count = 0
        self.infoMessage = u"Gedopi - Suivi thermique"

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
        layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
        if layer:
            layer.removeSelection()
            self.slot_thermi_select_changed = partial(self.thermi_select_changed, 1)
            layer.selectionChanged.connect(self.slot_thermi_select_changed)

    def disconnect_event(self):
        '''
        Appelé par onVisibilityChange(), soit, quand le QDockWidget se ferme,
        déconnecte le filtrage et le rowChange()
        '''
        layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
        if layer:
            layer.selectionChanged.disconnect(self.slot_thermi_select_changed)
            self.mapper.currentIndexChanged.disconnect(self.rowChange)

    def thermi_select_changed(self, origine):
        '''
        Gère le filtrage cartographique des enregistrements

        :param origine: définie si le filtrage est cartographique ou attributaire,
                obtenu via les partial(self.thermi_select_changed, origine)
        :type origine: int
        '''
        if self.etat_courant != 10:
            layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
            if layer:
                if layer.selectedFeatureCount() != 0:
                    self.btnFiltreCartoManuel.setEnabled(True)
                    if (origine == 1 and self.chkFiltreCartoAuto.isChecked()) or (origine == 2):
                        if (layer.selectedFeatureCount() >= 1000) and (QGis.QGIS_VERSION_INT < 21203):
                            layer.removeSelection()
                            self.iface.messageBar().pushMessage("Erreur : ", u"Le nombre d'éléments sélectionnés est trop important ...", level=QgsMessageBar.CRITICAL, duration=3)
                        else:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Suivi thermique"
                            wparam = ""
                            for feature in layer.selectedFeatures():
                                expressContext = QgsExpressionContext()
                                expressContext.setFeature(feature)
                                wid = QgsExpression("$id").evaluate(expressContext)
                                wparam += str(wid) + ","
                            if (wparam != ""):
                                wparam = "(" + wparam[0:len(wparam) - 1] + ")"
                                if self.modelThermi:
                                    self.modelThermi.setFilter("opest_id in %s" % wparam)
                                    self.modelThermi.select()

                                    self.row_count = self.modelThermi.rowCount()
                                    self.mapper.toFirst()
                                    self.btnDeleteFiltrage.setEnabled(True)
                else:
                    self.btnFiltreCartoManuel.setEnabled(False)

    def thermi_annule_filtrage(self):
        '''Annule le filtrage cartographique ou attributaire'''

        if self.modelThermi:
            self.infoMessage = u"Gedopi - Suivi thermique"
            self.modelThermi.setFilter("")
            self.modelThermi.select()
            self.row_count = self.modelThermi.rowCount()
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
        self.layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
        if self.layer:
            return True
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des opérations de suivis thermiques n'est pas chargée ...", level= QgsMessageBar.CRITICAL, duration = 5)
            return False

    def closeDatabase(self):
        '''Supprime certaines variables et déconnecte la base de données'''

        self.tbvMoa.setModel(None)
        self.mapper.setModel(None)

        del self.modelThermi
        del self.modelRiviere
        del self.modelStation
        del self.modelMoa

        # Supprime le vertex du canevas si existant
        if self.point_click != "":
            self.mc.scene().removeItem(self.point_click)
            self.point_click = ""
        self.point_click = ""

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
        self.infoMessage = u"Gedopi - Suivi thermique"
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

        self.modelThermi = QSqlRelationalTableModel(self, self.db)
        wrelation = "ope_suivi_thermi"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation

        self.modelThermi.setTable(wrelation)
        self.modelThermi.setSort(0, Qt.AscendingOrder)

        if (not self.modelThermi.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Thermi dans le setupModel() : \n" + self.modelThermi.lastError().text(), QMessageBox.Ok)

        self.row_count = self.modelThermi.rowCount()

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

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.modelThermi)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

    # Remplissage des cases suivi_thermi
        self.mapper.addMapping(self.leCodeOpe, self.modelThermi.fieldIndex("opest_ope_code"))
        self.mapper.addMapping(self.dateDebut, self.modelThermi.fieldIndex("opest_date_debut"))
        self.mapper.addMapping(self.dateFin, self.modelThermi.fieldIndex("opest_date_fin"))
        self.mapper.addMapping(self.spnDuree, self.modelThermi.fieldIndex("opest_duree"))
        self.mapper.addMapping(self.spnTiMax, self.modelThermi.fieldIndex("opest_ti_max"))
        self.mapper.addMapping(self.spnTiMin, self.modelThermi.fieldIndex("opest_ti_min"))
        self.mapper.addMapping(self.spnAjmaxTi, self.modelThermi.fieldIndex("opest_ajmax_ti"))
        self.mapper.addMapping(self.dateAjmaxTi, self.modelThermi.fieldIndex("opest_d_ajmax_ti"))
        self.mapper.addMapping(self.spnTmjMin, self.modelThermi.fieldIndex("opest_tmj_min"))
        self.mapper.addMapping(self.spnTmjMax, self.modelThermi.fieldIndex("opest_tmj_max"))
        self.mapper.addMapping(self.spnTmpMoy, self.modelThermi.fieldIndex("opest_tmp_moy"))
        self.mapper.addMapping(self.spnTm30jMax, self.modelThermi.fieldIndex("opest_tm30j_max"))
        self.mapper.addMapping(self.spnNbjTmj4_19, self.modelThermi.fieldIndex("opest_nbj_tmj_4_19"))
        self.mapper.addMapping(self.spnTmj4_19, self.modelThermi.fieldIndex("opest_p100j_tmj_4_19"))
        self.mapper.addMapping(self.spnTmjInf4, self.modelThermi.fieldIndex("opest_p100_tmj_inf_4"))
        self.mapper.addMapping(self.spnTmjSup19, self.modelThermi.fieldIndex("opest_p100_tmj_sup_19"))
        self.mapper.addMapping(self.spnCsfSup19, self.modelThermi.fieldIndex("opest_nbmax_ti_csf_sup19"))
        self.mapper.addMapping(self.spnCsfSupeg25, self.modelThermi.fieldIndex("opest_nbmax_ti_csf_sup_eg25"))
        self.mapper.addMapping(self.spnCsfSupeg15, self.modelThermi.fieldIndex("opest_nbmax_ti_csf_sup_eg15"))
        self.mapper.addMapping(self.datePonte, self.modelThermi.fieldIndex("opest_d50_ponte"))
        self.mapper.addMapping(self.spnIncubation, self.modelThermi.fieldIndex("opest_nbj_incub"))
        self.mapper.addMapping(self.dateEclosion, self.modelThermi.fieldIndex("opest_d50_eclo"))
        self.mapper.addMapping(self.spnResorption, self.modelThermi.fieldIndex("opest_nbj_rsp"))
        self.mapper.addMapping(self.dateEmergence, self.modelThermi.fieldIndex("opest_d50_emg"))
        self.mapper.addMapping(self.spnNbjPel, self.modelThermi.fieldIndex("opest_nbj_pel"))
        self.mapper.addMapping(self.spnSup15pel, self.modelThermi.fieldIndex("opest_nb_ti_sup15_pel"))
        self.mapper.addMapping(self.spnCsfSup15pel, self.modelThermi.fieldIndex("opest_nbmax_ti_csf_sup15_pel"))
        self.mapper.addMapping(self.spnInf1_5pel, self.modelThermi.fieldIndex("opest_nb_ti_inf_1_5pel"))
        self.mapper.addMapping(self.spnCsfInf1_5pel, self.modelThermi.fieldIndex("opest_nbmax_ti_csf_inf1_5_pel"))

        # Maître d'ouvrages
        self.modelMoa = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_moa_opest" #v_moa est une vue dans postgresql
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
        self.tbvMoa.setColumnHidden(self.modelMoa.fieldIndex("opest_id"), True)
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
        if self.modelThermi.rowCount() == 0:
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

        self.dateDebut.setDate(QDate(2000,1,1))
        self.dateFin.setDate(QDate(2000,1,1))
        self.spnDuree.setValue(0)
        self.spnTiMax.setValue(0)
        self.spnTiMin.setValue(0)
        self.spnAjmaxTi.setValue(0)
        self.dateAjmaxTi.setDate(QDate(2000,1,1))
        self.spnTmjMin.setValue(0)
        self.spnTmjMax.setValue(0)
        self.spnTmpMoy.setValue(0)
        self.spnTm30jMax.setValue(0)
        self.spnNbjTmj4_19.setValue(0)
        self.spnTmj4_19.setValue(0)
        self.spnTmjInf4.setValue(0)
        self.spnTmjSup19.setValue(0)
        self.spnCsfSup19.setValue(0)
        self.spnCsfSupeg25.setValue(0)
        self.spnCsfSupeg15.setValue(0)
        self.datePonte.setDate(QDate(2000,1,1))
        self.spnIncubation.setValue(0)
        self.dateEclosion.setDate(QDate(2000,1,1))
        self.spnResorption.setValue(0)
        self.dateEmergence.setDate(QDate(2000,1,1))
        self.spnNbjPel.setValue(0)
        self.spnSup15pel.setValue(0)
        self.spnCsfSup15pel.setValue(0)
        self.spnInf1_5pel.setValue(0)
        self.spnCsfInf1_5pel.setValue(0)
        self.leCodeOpe.setText("")
        self.chkVerrouAuto.setChecked(True)
        self.chkVerrouModif.setChecked(True)
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
        self.dateDebut.setEnabled(active)
        self.dateFin.setEnabled(active)
        self.spnDuree.setEnabled(active)
        self.spnTiMax.setEnabled(active)
        self.spnTiMin.setEnabled(active)
        self.spnAjmaxTi.setEnabled(active)
        self.dateAjmaxTi.setEnabled(active)
        self.spnTmjMin.setEnabled(active)
        self.spnTmjMax.setEnabled(active)
        self.spnTmpMoy.setEnabled(active)
        self.spnTm30jMax.setEnabled(active)
        self.spnNbjTmj4_19.setEnabled(active)
        self.spnTmj4_19.setEnabled(active)
        self.spnTmjInf4.setEnabled(active)
        self.spnTmjSup19.setEnabled(active)
        self.spnCsfSup19.setEnabled(active)
        self.spnCsfSupeg25.setEnabled(active)
        self.spnCsfSupeg15.setEnabled(active)
        self.datePonte.setEnabled(active)
        self.spnIncubation.setEnabled(active)
        self.dateEclosion.setEnabled(active)
        self.spnResorption.setEnabled(active)
        self.dateEmergence.setEnabled(active)
        self.spnNbjPel.setEnabled(active)
        self.spnSup15pel.setEnabled(active)
        self.spnCsfSup15pel.setEnabled(active)
        self.spnInf1_5pel.setEnabled(active)
        self.spnCsfInf1_5pel.setEnabled(active)
        self.cmbRiviere.setEnabled(active)
        self.cmbStation.setEnabled(active)
        self.leCodeOpe.setEnabled(active)
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

        self.btnImpCsv.setEnabled(False)

        self.btnNouveau.setEnabled(True)
        self.btnModif.setEnabled(active)
        self.btnSupprimer.setEnabled(active)
        self.btnEnregistrer.setEnabled(False)
        self.btnAnnuler.setEnabled(False)
        self.btnCoordonnee.setEnabled(False)

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

        self.btnCoordonnee.setEnabled(active)

        self.btnImpCsv.setEnabled(active)

        self.btnPremier.setEnabled(not active)
        self.btnPrec.setEnabled(not active)
        self.btnSuiv.setEnabled(not active)
        self.btnDernier.setEnabled(not active)

        self.btnZoom.setEnabled(not active)
        self.btnSelection.setEnabled(not active)
        self.btnStation.setEnabled(not active)
        self.btnExcel.setEnabled(not active)
        self.btnAjoutFiche.setEnabled(active)
        self.btnRetraitFiche.setEnabled(active)

        self.btnAjoutMoa.setEnabled(not active)
        self.btnSuppMoa.setEnabled(not active)

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
            if row >= self.modelThermi.rowCount():
                row = self.modelThermi.rowCount() - 1
        elif wfrom == "last":
            row = self.modelThermi.rowCount() - 1

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
        self.btnSuiv.setEnabled(row < self.modelThermi.rowCount() - 1)

        self.cmbRiviere.currentIndexChanged.disconnect(self.changeCmbRiviere)

        record = self.modelThermi.record(row)
        wopest_ope_code = record.value(self.modelThermi.fieldIndex("opest_ope_code"))

       # Récupération de la clé de l'operation correspondante
        query = QSqlQuery(self.db)
        wrelation = "operation"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("select ope_sta_id from " + wrelation + " where ope_code = ?")
        query.addBindValue(wopest_ope_code)
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
            QMessageBox.critical(self, u"Remplissage du modèl", u"Erreur au modèle Station dans le rowChange() : \n" + self.modelStation.lastError().text(), QMessageBox.Ok)

        self.cmbStation.setModel(self.modelStation)
        self.cmbStation.setModelColumn(1)

        # Sélection station
        result = self.cmbStation.model().match(self.cmbStation.model().index(0, 0), Qt.EditRole, wope_sta_id, -1, Qt.MatchExactly)
        if result:
            self.cmbStation.setCurrentIndex(result[0].row())

        # Maitres d'ouvrage
        id = record.value("opest_id")
        self.modelMoa.setFilter("opest_id = %i" % id)

        self.afficheInfoRow()

        self.cmbRiviere.currentIndexChanged.connect(self.changeCmbRiviere)

        self.verrouillage()
        self.verrouillageModif()

        # Vérifie la présence d'une géométrie
        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelThermi.record(row)
                wid = record.value("opest_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
                request = QgsFeatureRequest().setFilterFids([wid])

                it = layer.getFeatures(request)
                extent = None
                for x in it:
                    extent = x.geometry()
                if extent == None:
                    self.iface.messageBar().pushMessage("Attention : ", u"Ce suivi thermique ne possède pas de géométrie.", level= QgsMessageBar.WARNING, duration = 5)

    def zoomThermi(self):
        '''Permet de zoomer le canevas de la carte sur le suivi courant'''

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelThermi.record(row)
                wid = record.value("opest_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
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

    def selectionThermi(self):
        '''Permet de sélectionner le suivi correspondant à l'enregistrement courant'''

        if self.mapper:
            row = self.mapper.currentIndex()
            self.etat_courant = 10
            if row >= 0:
                record = self.modelThermi.record(row)
                wid = record.value("opest_id")

                layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
                layer.removeSelection()
                layer.select(wid)
                self.etat_courant = 0

    def openTableur(self):
        '''Permet d'ouvrir le fichier liée à la pêche'''

        row = self.mapper.currentIndex()
        record = self.modelThermi.record(row)
        lienTableur = record.value(u"opest_excel")
        if lienTableur == "" or lienTableur == None:
            self.iface.messageBar().pushMessage("Info : ", u"Pas de fichier joint !", level= QgsMessageBar.INFO, duration = 5)
        else :
            try:
                os.startfile(lienTableur)
            except:
                self.iface.messageBar().pushMessage("Info : ", u"Le fichier est introuvable !", level= QgsMessageBar.WARNING, duration = 5)

    def ajoutFiche(self):
        '''Permet de joindre un fichier externe au suivi'''

        openfile = ""
        openfile = QFileDialog.getOpenFileName(self)
        if openfile != "":
            self.cheminExcel = unicode(openfile)
            self.excelBool = True

    def retraitFiche(self):
        '''Permet de retirer un fichier externe au suivi'''
        if QMessageBox.question(self, u"Délier", u"Etes-vous certain de vouloir délier le fichier ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            self.cheminExcel = ""
            self.excelBool = True

    def importCsv(self):
        ''' Permet d'importer un fichier CSV compatible, issu de la macro Excel Macma Salmo'''

        self.cheminCsv = ""
        self.cheminCsv = QFileDialog.getOpenFileName(self, "Open File", "", "CSV (*.csv)")
        self.cheminCsv = unicode(self.cheminCsv)
        self.saisieAuto()

    def supprimer(self):
        '''Permet de supprimer le suivi courant ainsi que toutes les données liées (cascade)'''

        filtreCourant = self.modelThermi.filter()

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                if QMessageBox.question(self, "Suppression", u"Etes-vous certain de vouloir supprimer ce suivi thermique ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    record = self.modelThermi.record(row)
                    wid = record.value("opest_ope_code")

                    query = QSqlQuery(self.db)

                    wrelation = "operation"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                    query.addBindValue(wid)
                    if not query.exec_():
                        QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce suivi ...", QMessageBox.Ok)

                    if filtreCourant != "":
                        filtreCourant = filtreCourant.replace(str(wid), "NULL" )

                    self.setupModel()

                    if filtreCourant != "":
                        self.modelThermi.setFilter(filtreCourant)
                        self.row_count = self.modelThermi.rowCount()
                        if self.row_count != 0:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Suivi thermique"
                            self.mapper.toFirst()
                            self.btnDeleteFiltrage.setEnabled(True)

    def nouveau(self):
        '''Prépare le formulaire pour la saisie d'un nouveau suivi'''

        self.boolNew = True
        layer = self.gc.getLayerFromLegendByTableProps('ope_suivi_thermi', 'opest_geom', '')
        layer.removeSelection()
        self.thermi_annule_filtrage()
        self.cmbRiviere.setCurrentIndex(-1)

        self.activeButtonsModif(True)
        self.clearFields()
        self.activeFields(True)

        self.wthermi_geom = ""

        self.chkVerrouModif.setChecked(False)
        self.verrouillage()

    def annuler(self, repositionnement = True):
        '''Annule la saisie d'une nouveau suivi'''

        self.activeButtonsModif(False)
        self.btnFiltreCartoManuel.setEnabled(False)
        self.btnDeleteFiltrage.setEnabled(False)

        self.mapper.revert()

        self.boolNew = False
        self.btnCoordonnee.setChecked(False)
        if self.point_click != "":
            self.mc.scene().removeItem(self.point_click)
            self.point_click = ""
        self.point_click = ""

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

    def enregistrer(self):
        '''Enregistre la pêche nouvellement créée'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopest_station = wrecord.value(0)

            wopest_ope_code = self.leCodeOpe.text()
            value = self.dateDebut.date()
            wopest_date_debut  = QDate.toString(value, "yyyy-MM-dd")
            value2 = self.dateFin.date()
            wopest_date_fin = QDate.toString(value2, "yyyy-MM-dd")
            wopest_duree = self.spnDuree.value()
            wopest_ti_max = self.spnTiMax.value()
            wopest_ti_min = self.spnTiMin.value()
            wopest_ajmax_ti = self.spnAjmaxTi.value()
            value3 = self.dateAjmaxTi.date()
            wopest_d_ajmax_ti = QDate.toString(value3, "yyyy-MM-dd")
            wopest_tmj_min = self.spnTmjMin.value()
            wopest_tmj_max = self.spnTmjMax.value()
            wopest_tmp_moy = self.spnTmpMoy.value()
            wopest_tm30j_max = self.spnTm30jMax.value()
            wopest_nbj_tmj_4_19 = self.spnNbjTmj4_19.value()
            wopest_p100j_tmj_4_19 = self.spnTmj4_19.value()
            wopest_p100_tmj_inf_4 = self.spnTmjInf4.value()
            wopest_p100_tmj_sup_19 = self.spnTmjSup19.value()
            wopest_nbmax_ti_csf_sup19 = self.spnCsfSup19.value()
            wopest_nbmax_ti_csf_sup_eg25 = self.spnCsfSupeg25.value()
            wopest_nbmax_ti_csf_sup_eg15 = self.spnCsfSupeg15.value()
            value4 = self.datePonte.date()
            wopest_d50_ponte = QDate.toString(value4, "yyyy-MM-dd")
            wopest_nbj_incub = self.spnIncubation.value()
            value5 = self.dateEclosion.date()
            wopest_d50_eclo = QDate.toString(value5, "yyyy-MM-dd")
            wopest_nbj_rsp = self.spnResorption.value()
            value6 = self.dateEmergence.date()
            wopest_d50_emg = QDate.toString(value6, "yyyy-MM-dd")
            wopest_nbj_pel = self.spnNbjPel.value()
            wopest_nb_ti_sup15_pel = self.spnSup15pel.value()
            wopest_nbmax_ti_csf_sup15_pel = self.spnCsfSup15pel.value()
            wopest_nb_ti_inf_1_5pel = self.spnInf1_5pel.value()
            wopest_nbmax_ti_csf_inf1_5_pel = self.spnCsfInf1_5pel.value()
            wopest_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopest_excel = ""
                else :
                    wopest_excel = self.cheminExcel
                    self.excelBool = False
            else :
                wopest_excel = ""

            if wopest_ti_max <= 19:
                wtimax_id = 1
            elif wopest_ti_max > 19 and wopest_ti_max <= 22:
                wtimax_id = 2
            elif wopest_ti_max > 22 and wopest_ti_max <= 25:
                wtimax_id = 3
            elif wopest_ti_max > 25:
                wtimax_id = 4

            # Création du code opération
            queryFk = QSqlQuery(self.db)
            wrelation = "operation"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryFk.prepare("INSERT INTO " + wrelation + " (ope_code, ope_sta_id) VALUES (?, ?)")
            queryFk.addBindValue(wopest_ope_code)
            queryFk.addBindValue(wopest_station)
            if not queryFk.exec_():
                QMessageBox.critical(self, u"Erreur - Création de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

            # Création de la requête d'enregistrement
            query = QSqlQuery(self.db)
            wrelation = "ope_suivi_thermi"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("INSERT INTO " + wrelation + " (opest_date_debut, opest_date_fin, opest_duree, opest_ti_min, opest_ti_max,  opest_ajmax_ti,  opest_d_ajmax_ti, " +
            "opest_tmj_min, opest_tmj_max, opest_tmp_moy, opest_tm30j_max, opest_nbj_tmj_4_19, opest_p100j_tmj_4_19, opest_p100_tmj_inf_4, opest_p100_tmj_sup_19, " +
            "opest_nbmax_ti_csf_sup19, opest_nbmax_ti_csf_sup_eg25, opest_nbmax_ti_csf_sup_eg15, opest_d50_ponte, opest_nbj_incub, opest_d50_eclo, opest_nbj_rsp, opest_d50_emg, " +
            "opest_nbj_pel, opest_nb_ti_sup15_pel, opest_nbmax_ti_csf_sup15_pel, opest_nb_ti_inf_1_5pel, opest_nbmax_ti_csf_inf1_5_pel, opest_excel, opest_ope_code, " +
            "opest_timax_id, opest_geom) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, " + self.wthermi_geom + ")")
            query.addBindValue(wopest_date_debut)
            query.addBindValue(wopest_date_fin)
            query.addBindValue(wopest_duree)
            query.addBindValue(wopest_ti_min)
            query.addBindValue(wopest_ti_max)
            query.addBindValue(wopest_ajmax_ti)
            query.addBindValue(wopest_d_ajmax_ti)
            query.addBindValue(wopest_tmj_min)
            query.addBindValue(wopest_tmj_max)
            query.addBindValue(wopest_tmp_moy)
            query.addBindValue(wopest_tm30j_max)
            query.addBindValue(wopest_nbj_tmj_4_19)
            query.addBindValue(wopest_p100j_tmj_4_19)
            query.addBindValue(wopest_p100_tmj_inf_4)
            query.addBindValue(wopest_p100_tmj_sup_19)
            query.addBindValue(wopest_nbmax_ti_csf_sup19)
            query.addBindValue(wopest_nbmax_ti_csf_sup_eg25)
            query.addBindValue(wopest_nbmax_ti_csf_sup_eg15)
            query.addBindValue(wopest_d50_ponte)
            query.addBindValue(wopest_nbj_incub)
            query.addBindValue(wopest_d50_eclo)
            query.addBindValue(wopest_nbj_rsp)
            query.addBindValue(wopest_d50_emg)
            query.addBindValue(wopest_nbj_pel)
            query.addBindValue(wopest_nb_ti_sup15_pel)
            query.addBindValue(wopest_nbmax_ti_csf_sup15_pel)
            query.addBindValue(wopest_nb_ti_inf_1_5pel)
            query.addBindValue(wopest_nbmax_ti_csf_inf1_5_pel)
            query.addBindValue(wopest_excel)
            query.addBindValue(wopest_ope_code)
            query.addBindValue(wtimax_id)

            if not query.exec_():
                querySupp = QSqlQuery(self.db)
                wrelation = "operation"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                querySupp.prepare("DELETE FROM " + wrelation + " WHERE ope_code = ?")
                querySupp.addBindValue(wopest_ope_code)
                if not querySupp.exec_():
                    QMessageBox.critical(self, u"Erreur - Suppression de l'opération", querySupp.lastError().text(), QMessageBox.Ok)

                QMessageBox.critical(self, u"Erreur - Création du suivi", query.lastError().text(), QMessageBox.Ok)
            else:
                        # Ajout d'un nouveau vertex sur la couche cours_eau à l'emplacement du suivi
                        # Permet par la sélection par localisation dans QGIS
                layers = QgsMapLayerRegistry.instance().mapLayers()
                for name, layer in layers.iteritems():
                    if "cours_eau" in name:
                        source = layer.storageType()
                        if "PostgreSQL" in source or "PostGIS" in source:
                            self.iface.setActiveLayer(layer)

                            layerVertex = self.iface.activeLayer()
                            if not layerVertex.isValid():
                                QMessageBox.critical(self, u"Erreur", "La couche cours_eau n'est pas la couche active !", QMessageBox.Ok)
                            else:
                                caps = layerVertex.dataProvider().capabilities()
                                if caps & QgsVectorDataProvider.ChangeGeometries:
                                    ptVertex = QgsPoint(self.addVertex)
                                    layerVertex.startEditing()
                                    layerVertex.addTopologicalPoints(ptVertex)
                                    createVertex = layerVertex.addTopologicalPoints(ptVertex)
                                    if createVertex != 0:
                                        layerVertex.rollBack()
                                        QMessageBox.critical(self, u"Erreur - Ajout d'un noeud", "Le noeud sur la couche des rivières n'a pas été ajouté mais la station crée !", QMessageBox.Ok)
                                    else:
                                        layerVertex.commitChanges()
                                else :
                                    QMessageBox.critical(self, u"Erreur - Ajout d'un noeud", "Cette couche ne peut pas / plus changer sa géométrie!", QMessageBox.Ok)

                # Màj du nombre d'enregistrement
                self.row_count += 1
                if self.row_count == 1:
                    self.modelThermi.select()

            # Suppression du marqueur sur le canevas
            if self.point_click != "":
                self.mc.scene().removeItem(self.point_click)
                self.point_click = ""

            # Basculement du formulaire vers la visualisation
            self.annuler(False)
            self.mc.refresh()
            self.setupModel()
            self.boolNew = False
            self.saisieAutoBool = False
            self.wthermi_geom = ""
            self.saveRecord("last") #renvoie sur le dernier enregistrement

    def modification(self):
        '''Permet la modification du suivi courante'''

        # Validation de la saisie
        if self.validation_saisie():
            # Récupération des valeurs
            wrecord = self.cmbStation.model().record(self.cmbStation.currentIndex())
            wopest_station = wrecord.value(0)

            wopest_ope_code = self.leCodeOpe.text()
            value = self.dateDebut.date()
            wopest_date_debut  = QDate.toString(value, "yyyy-MM-dd")
            value2 = self.dateFin.date()
            wopest_date_fin = QDate.toString(value2, "yyyy-MM-dd")
            wopest_duree = self.spnDuree.value()
            wopest_ti_max = self.spnTiMax.value()
            wopest_ti_min = self.spnTiMin.value()
            wopest_ajmax_ti = self.spnAjmaxTi.value()
            value3 = self.dateAjmaxTi.date()
            wopest_d_ajmax_ti = QDate.toString(value3, "yyyy-MM-dd")
            wopest_tmj_min = self.spnTmjMin.value()
            wopest_tmj_max = self.spnTmjMax.value()
            wopest_tmp_moy = self.spnTmpMoy.value()
            wopest_tm30j_max = self.spnTm30jMax.value()
            wopest_nbj_tmj_4_19 = self.spnNbjTmj4_19.value()
            wopest_p100j_tmj_4_19 = self.spnTmj4_19.value()
            wopest_p100_tmj_inf_4 = self.spnTmjInf4.value()
            wopest_p100_tmj_sup_19 = self.spnTmjSup19.value()
            wopest_nbmax_ti_csf_sup19 = self.spnCsfSup19.value()
            wopest_nbmax_ti_csf_sup_eg25 = self.spnCsfSupeg25.value()
            wopest_nbmax_ti_csf_sup_eg15 = self.spnCsfSupeg15.value()
            value4 = self.datePonte.date()
            wopest_d50_ponte = QDate.toString(value4, "yyyy-MM-dd")
            wopest_nbj_incub = self.spnIncubation.value()
            value5 = self.dateEclosion.date()
            wopest_d50_eclo = QDate.toString(value5, "yyyy-MM-dd")
            wopest_nbj_rsp = self.spnResorption.value()
            value6 = self.dateEmergence.date()
            wopest_d50_emg = QDate.toString(value6, "yyyy-MM-dd")
            wopest_nbj_pel = self.spnNbjPel.value()
            wopest_nb_ti_sup15_pel = self.spnSup15pel.value()
            wopest_nbmax_ti_csf_sup15_pel = self.spnCsfSup15pel.value()
            wopest_nb_ti_inf_1_5pel = self.spnInf1_5pel.value()
            wopest_nbmax_ti_csf_inf1_5_pel = self.spnCsfInf1_5pel.value()
            wopest_excel = ""
            if self.excelBool ==True:
                if self.cheminExcel == "":
                    self.wopest_excel = ""
                else :
                    wopest_excel = self.cheminExcel
                    self.excelBool = False
            else :
                row = self.mapper.currentIndex()
                record = self.modelThermi.record(row)
                self.cheminExcel = record.value(u"opest_excel")
                wopest_excel = self.cheminExcel

            if wopest_ti_max <= 19:
                wtimax_id = 1
            elif wopest_ti_max > 19 and wopest_ti_max <= 22:
                wtimax_id = 2
            elif wopest_ti_max > 22 and wopest_ti_max <= 25:
                wtimax_id = 3
            elif wopest_ti_max > 25:
                wtimax_id = 4

            record = self.modelStation.record(self.cmbStation.currentIndex())
            wsta_id = record.value(0)

            if QMessageBox.question(self, "Enregistrer", u"Etes-vous certain de vouloir enregistrer les modifications ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

                filtreCourant = self.modelThermi.filter()

                queryFk = QSqlQuery(self.db)
                wrelationFk = "operation"
                if self.dbType == "postgres":
                    wrelationFk = self.dbSchema + "." + wrelationFk
                queryFk.prepare("UPDATE " + wrelationFk + " SET ope_code = '" + str(wopest_ope_code) + "', ope_sta_id = " + str(wsta_id) + "WHERE ope_code = '" + self.codeOpe + "'")
                if not queryFk.exec_():
                    QMessageBox.critical(self, u"Erreur - Modification du code de l'opération", queryFk.lastError().text(), QMessageBox.Ok)

                if self.saisieAutoBool == True:
                    # Modification si changement de géométrie
                    wthermi_geom = ""
                    wthermi_geom = self.wthermi_geom

                    query = QSqlQuery(self.db)
                    wrelation = "ope_suivi_thermi"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET opest_date_debut = '" + wopest_date_debut + "', opest_date_fin = '" + wopest_date_fin + "', opest_duree = " + str(wopest_duree) +
                    ", opest_ti_min = " + str(wopest_ti_min) + ", opest_ti_max = " + str(wopest_ti_max) + ", opest_ajmax_ti = " + str(wopest_ajmax_ti) + ", opest_d_ajmax_ti = '" + wopest_d_ajmax_ti +
                    "', opest_tmj_min = " + str(wopest_tmj_min) + ", opest_tmj_max = " + str(wopest_tmj_max) + ", opest_tmp_moy = " + str(wopest_tmp_moy) +
                    ", opest_tm30j_max = " + str(wopest_tm30j_max) + ", opest_nbj_tmj_4_19 = " + str(wopest_nbj_tmj_4_19) + ", opest_p100j_tmj_4_19 = " + str(wopest_p100j_tmj_4_19) +
                    ", opest_p100_tmj_inf_4 = " + str(wopest_p100_tmj_inf_4) + ", opest_p100_tmj_sup_19 = " + str(wopest_p100_tmj_sup_19) +
                    ", opest_nbmax_ti_csf_sup19 = " + str(wopest_nbmax_ti_csf_sup19) + ", opest_nbmax_ti_csf_sup_eg25 = " + str(wopest_nbmax_ti_csf_sup_eg25) +
                    ", opest_nbmax_ti_csf_sup_eg15 = " + str(wopest_nbmax_ti_csf_sup_eg15) + ", opest_d50_ponte = '" + wopest_d50_ponte + "', opest_nbj_incub = " + str(wopest_nbj_incub) +
                    ", opest_d50_eclo = '" + wopest_d50_eclo + "', opest_nbj_rsp = " + str(wopest_nbj_rsp) + ", opest_d50_emg = '" + wopest_d50_emg + "', opest_nbj_pel = " + str(wopest_nbj_pel) +
                    ", opest_nb_ti_sup15_pel = " + str(wopest_nb_ti_sup15_pel) + ", opest_nbmax_ti_csf_sup15_pel = " + str(wopest_nbmax_ti_csf_sup15_pel) +
                    ", opest_nb_ti_inf_1_5pel = " + str(wopest_nb_ti_inf_1_5pel) + ", opest_nbmax_ti_csf_inf1_5_pel = " + str(wopest_nbmax_ti_csf_inf1_5_pel) + ", opest_excel = '" + wopest_excel +
                    "', opest_timax_id = " + str(wtimax_id) + ", opest_geom = " + wthermi_geom + " WHERE opest_ope_code = '" + wopest_ope_code + "'")

                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification du suivi", query.lastError().text(), QMessageBox.Ok)
                    else :
                        # Ajout d'un nouveau vertex sur la couche cours_eau à l'emplacement du suivi
                        # Permet par la sélection par localisation dans QGIS
                        layers = QgsMapLayerRegistry.instance().mapLayers()
                        for name, layer in layers.iteritems():
                            if "cours_eau" in name:
                                source = layer.storageType()
                                if "PostgreSQL" in source or "PostGIS" in source:
                                    self.iface.setActiveLayer(layer)

                                    layerVertex = self.iface.activeLayer()
                                    if not layerVertex.isValid():
                                        QMessageBox.critical(self, u"Erreur", "La couche cours_eau n'est pas la couche active !", QMessageBox.Ok)
                                    else:
                                        caps = layerVertex.dataProvider().capabilities()
                                        if caps & QgsVectorDataProvider.ChangeGeometries:
                                            ptVertex = QgsPoint(self.addVertex)
                                            layerVertex.startEditing()
                                            layerVertex.addTopologicalPoints(ptVertex)
                                            createVertex = layerVertex.addTopologicalPoints(ptVertex)
                                            if createVertex != 0:
                                                layerVertex.rollBack()
                                                QMessageBox.critical(self, u"Erreur - Ajout d'un noeud", "Le noeud sur la couche des rivières n'a pas été ajouté mais la station crée !", QMessageBox.Ok)
                                            else:
                                                layerVertex.commitChanges()
                                        else :
                                            QMessageBox.critical(self, u"Erreur - Ajout d'un noeud", "Cette couche ne peut pas / plus changer sa géométrie!", QMessageBox.Ok)
                else:
                    # Modification si la géométrie reste inchangée
                    query = QSqlQuery(self.db)
                    wrelation = "ope_suivi_thermi"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET opest_date_debut = '" + wopest_date_debut + "', opest_date_fin = '" + wopest_date_fin + "', opest_duree = " + str(wopest_duree) +
                    ", opest_ti_min = " + str(wopest_ti_min) + ", opest_ti_max = " + str(wopest_ti_max) + ", opest_ajmax_ti = " + str(wopest_ajmax_ti) + ", opest_d_ajmax_ti = '" + wopest_d_ajmax_ti +
                    "', opest_tmj_min = " + str(wopest_tmj_min) + ", opest_tmj_max = " + str(wopest_tmj_max) + ", opest_tmp_moy = " + str(wopest_tmp_moy) +
                    ", opest_tm30j_max = " + str(wopest_tm30j_max) + ", opest_nbj_tmj_4_19 = " + str(wopest_nbj_tmj_4_19) + ", opest_p100j_tmj_4_19 = " + str(wopest_p100j_tmj_4_19) +
                    ", opest_p100_tmj_inf_4 = " + str(wopest_p100_tmj_inf_4) + ", opest_p100_tmj_sup_19 = " + str(wopest_p100_tmj_sup_19) +
                    ", opest_nbmax_ti_csf_sup19 = " + str(wopest_nbmax_ti_csf_sup19) + ", opest_nbmax_ti_csf_sup_eg25 = " + str(wopest_nbmax_ti_csf_sup_eg25) +
                    ", opest_nbmax_ti_csf_sup_eg15 = " + str(wopest_nbmax_ti_csf_sup_eg15) + ", opest_d50_ponte = '" + wopest_d50_ponte + "', opest_nbj_incub = " + str(wopest_nbj_incub) +
                    ", opest_d50_eclo = '" + wopest_d50_eclo + "', opest_nbj_rsp = " + str(wopest_nbj_rsp) + ", opest_d50_emg = '" + wopest_d50_emg + "', opest_nbj_pel = " + str(wopest_nbj_pel) +
                    ", opest_nb_ti_sup15_pel = " + str(wopest_nb_ti_sup15_pel) + ", opest_nbmax_ti_csf_sup15_pel = " + str(wopest_nbmax_ti_csf_sup15_pel) +
                    ", opest_nb_ti_inf_1_5pel = " + str(wopest_nb_ti_inf_1_5pel) + ", opest_nbmax_ti_csf_inf1_5_pel = " + str(wopest_nbmax_ti_csf_inf1_5_pel) + ", opest_excel = '" + wopest_excel +
                    "', opest_timax_id = " + str(wtimax_id) + " WHERE opest_ope_code = '" + wopest_ope_code + "'")

                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification du suivi et de sa géométrie", query.lastError().text(), QMessageBox.Ok)

            # Suppression des marqueurs sur le canevas
            if self.point_click != "":
                self.mc.scene().removeItem(self.point_click)
                self.point_click = ""

            # Basculement du formulaire vers la visualisation
            self.chkVerrouModif.setChecked(True)
            self.mc.refresh()
            self.setupModel()
            self.saisieAutoBool = False
            self.wthermi_geom = ""
            # self.saveRecord("last") #renvoie sur le dernier enregistrement

            if filtreCourant != "":
                self.modelThermi.setFilter(filtreCourant)
                self.row_count = self.modelThermi.rowCount()
                if self.row_count != 0:
                    self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Suivi thermique"
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
        elif self.wthermi_geom == "" and self.saisieAutoBool == True:
            self.iface.messageBar().pushMessage("Erreur : ", u"Aucun emplacement saisie ...", level=QgsMessageBar.CRITICAL, duration=5)
            saisieOk = False
        else:
            saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

    def calculCoordonnee(self):
        '''Permet de récupérer le clic sur le canevas'''

        if self.btnCoordonnee.isChecked():
            self.creaGeom = True
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
        if self.creaGeom == True:
            self.layerPoint = QgsPoint(point)
            self.saisieAuto()

    def saisieAuto(self):
        '''Permet la saisie automatique de certains champs'''

        # Création de la géométrie
        if self.creaGeom == True:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.saisieAutoBool = True
            self.wthermi_geom = ""
            pointTher = ""
            ptThermi = ""

            if self.point_click != "":
                self.mc.scene().removeItem(self.point_click)
                self.point_click = ""

            # Reprojection du point si nécessaire
            epsgBase = str(self.mc.mapSettings().destinationCrs().authid())
            epsgSrc = int(epsgBase.replace('EPSG:', ''))
            if epsgSrc != 2154:
                crsSrc = QgsCoordinateReferenceSystem(epsgSrc)
                crsDest = QgsCoordinateReferenceSystem(2154)
                xform = QgsCoordinateTransform(crsSrc, crsDest)
                ptThermi = xform.transform(self.layerPoint)
            else:
                ptThermi = self.layerPoint

            # Import virtuel de la couche des cours d'eau
            uri = QgsDataSourceURI()
            uri.setConnection("localhost", "5432", self.dbname, self.password, self.user)
            uri.setDataSource("data", "cours_eau", "ceau_geom")
            vlayer = QgsVectorLayer(uri.uri(), "riviere", "postgres")
            if not vlayer.isValid():
                self.iface.messageBar().pushMessage("Erreur : ", u"Layer failed Rivière to load !", level= QgsMessageBar.CRITICAL, duration = 5)
            # Calcul de la distance la plus courte entre le point et la rivière et modification du point
            shortestDistance = float("inf")
            self.wthermi_geom = ""
            self.pointThermi = ""
            self.point_click = ""
            x = ""
            y = ""
            for f in vlayer.getFeatures():
                dist = f.geometry().distance( QgsGeometry.fromPoint( ptThermi) )
                if dist < shortestDistance:
                    shortestDistance = dist
                    inter = f.geometry().nearestPoint( QgsGeometry.fromPoint( ptThermi ) )
                    pointTher = inter.vertexAt(0)
                    self.addVertex = pointTher

            self.pointThermi = QgsPoint(pointTher)

            self.point_click = QgsVertexMarker(self.mc)
            self.point_click.setCenter(self.pointThermi)

            if pointTher != "":
                pt_wkt = QgsPoint(pointTher).wellKnownText()
                self.wthermi_geom= "ST_GeomFromText(' "+ str(pt_wkt) + "', 2154)"

            else:
                self.iface.messageBar().pushMessage("Erreur : ", u"Aucune coordonnée (erreur au pt1) !", level= QgsMessageBar.CRITICAL, duration = 5)

            self.creaGeom = False
            self.mc.setMapTool(self.pan)
            self.btnCoordonnee.setChecked(False)
            QApplication.restoreOverrideCursor()

        # Copie des données du CSV dans les champs correspondant
        if self.cheminCsv != "" :
            listValeur = []
            chaine_nom = ""
            chaine_valeur = ""
            with open(self.cheminCsv, 'rt') as csvfile:
                reader = csv.reader(csvfile, delimiter = ';')
                i = 0
                for i, elt in enumerate(reader):
                    if i == 0:
                        for valThermi in elt:
                            if chaine_nom == "":
                                chaine_nom = str(valThermi)
                            else:
                                chaine_nom = chaine_nom + ";" + str(valThermi)
                    if i == 1:
                        for valThermi in elt:
                            listValeur.append(valThermi)
                            if chaine_valeur == "":
                                chaine_valeur = str(valThermi)
                            else :
                                chaine_valeur = chaine_valeur + ";" + str(valThermi)
                    i += 1
                try :
                    wopest_date_debut = listValeur[0]
                    wopest_date_debut = wopest_date_debut.replace('/', '-')
                    wopest_date_fin = listValeur[1]
                    wopest_date_fin = wopest_date_fin.replace('/', '-')
                    wopest_duree = int(listValeur[2])
                    wopest_ti_min = float(listValeur[3].replace(',', '.'))
                    wopest_ti_max = float(listValeur[4].replace(',', '.'))
                    wopest_ajmax_ti = float(listValeur[6].replace(',', '.'))
                    wopest_d_ajmax_ti = listValeur[7]
                    wopest_d_ajmax_ti = wopest_d_ajmax_ti.replace('/', '-')
                    wopest_tmj_min = float(listValeur[8].replace(',', '.'))
                    wopest_tmj_max = float(listValeur[9].replace(',', '.'))
                    wopest_tmp_moy = float(listValeur[12].replace(',', '.'))
                    wopest_tm30j_max = float(listValeur[13].replace(',', '.'))
                    wopest_nbj_tmj_4_19 = int(listValeur[16])
                    wopest_p100j_tmj_4_19 = float(listValeur[17].replace(',', '.'))
                    wopest_p100_tmj_inf_4 = float(listValeur[20].replace(',', '.'))
                    wopest_p100_tmj_sup_19 = float(listValeur[21].replace(',', '.'))
                    wopest_nbmax_ti_csf_sup19 = float(listValeur[24].replace(',', '.'))
                    wopest_nbmax_ti_csf_supeg25 = float(listValeur[27].replace(',', '.'))
                    wopest_nbmax_ti_csf_supeg15 = float(listValeur[30].replace(',', '.'))
                    wopest_d50_ponte = listValeur[31]
                    wopest_d50_ponte = wopest_d50_ponte.replace('/', '-')
                    wopest_nbj_incub = int(listValeur[32])
                    wopest_d50_eclo = listValeur[33]
                    wopest_d50_eclo = wopest_d50_eclo.replace('/', '-')
                    wopest_nbj_rsp = int(listValeur[34])
                    wopest_nbj_pel = int(listValeur[35])
                    wopest_d50_emg = listValeur[36]
                    wopest_d50_emg = wopest_d50_emg.replace('/', '-')
                    wopest_nb_ti_sup15_pel = float(listValeur[37].replace(',', '.'))
                    wopest_nbmax_ti_csf_sup15_pel = float(listValeur[38].replace(',', '.'))
                    wopest_nb_ti_inf_1_5pel = float(listValeur[40].replace(',', '.'))
                    wopest_nbmax_ti_csf_inf1_5_pel = float(listValeur[42].replace(',', '.'))

                    self.dateDebut.setDate(QDate.fromString(wopest_date_debut, "dd-MM-yyyy"))
                    self.dateFin.setDate(QDate.fromString(wopest_date_fin, "dd-MM-yyyy"))
                    self.spnDuree.setValue(wopest_duree)
                    self.spnTiMax.setValue(wopest_ti_max)
                    self.spnTiMin.setValue(wopest_ti_min)
                    self.spnAjmaxTi.setValue(wopest_ajmax_ti)
                    self.dateAjmaxTi.setDate(QDate.fromString(wopest_d_ajmax_ti, "dd-MM-yyyy"))
                    self.spnTmjMin.setValue(wopest_tmj_min)
                    self.spnTmjMax.setValue(wopest_tmj_max)
                    self.spnTmpMoy.setValue(wopest_tmp_moy)
                    self.spnTm30jMax.setValue(wopest_tm30j_max)
                    self.spnNbjTmj4_19.setValue(wopest_nbj_tmj_4_19)
                    self.spnTmj4_19.setValue(wopest_p100j_tmj_4_19)
                    self.spnTmjInf4.setValue(wopest_p100_tmj_inf_4)
                    self.spnTmjSup19.setValue(wopest_p100_tmj_sup_19)
                    self.spnCsfSup19.setValue(wopest_nbmax_ti_csf_sup19)
                    self.spnCsfSupeg25.setValue(wopest_nbmax_ti_csf_supeg25)
                    self.spnCsfSupeg15.setValue(wopest_nbmax_ti_csf_supeg15)
                    self.datePonte.setDate(QDate.fromString(wopest_d50_ponte, "dd-MM-yyyy"))
                    self.spnIncubation.setValue(wopest_nbj_incub)
                    self.dateEclosion.setDate(QDate.fromString(wopest_d50_eclo, "dd-MM-yyyy"))
                    self.spnResorption.setValue(wopest_nbj_rsp)
                    self.dateEmergence.setDate(QDate.fromString(wopest_d50_emg, "dd-MM-yyyy"))
                    self.spnNbjPel.setValue(wopest_nbj_pel)
                    self.spnSup15pel.setValue(wopest_nb_ti_sup15_pel)
                    self.spnCsfSup15pel.setValue(wopest_nbmax_ti_csf_sup15_pel)
                    self.spnInf1_5pel.setValue(wopest_nb_ti_inf_1_5pel)
                    self.spnCsfInf1_5pel.setValue(wopest_nbmax_ti_csf_inf1_5_pel)
                except :
                    # raise IndexError("message à afficher")
                    self.iface.messageBar().pushMessage("Erreur : ", u"Le fichier CSV n'est pas valide, vérifiez son contenu ...", level=QgsMessageBar.CRITICAL, duration=5)

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

        dialog = Filtrage_thermi_dialog(self.db, self.dbType, self.dbSchema, self.modelThermi)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.row_count = self.modelThermi.rowCount()
            if self.row_count != 0:
                self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Suivi thermique"
                self.mapper.toFirst()
                self.btnDeleteFiltrage.setEnabled(True)

    def ajoutMoa(self):
        '''Permet l'ouverture de la fenêtre pour ajouter un maître d'ouvrage'''

        record = self.modelThermi.record(self.row_courant)
        wopest_id = record.value("opest_id")
        dialog = Ope_moa_ajout_dialog(self.db, self.dbType, self.dbSchema, wopest_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelMoa.setFilter("opest_id = %i" % wopest_id)

    def suppMoa(self):
        '''Permet de supprimer le maître d'ouvrage sélectionné'''

        record = self.modelThermi.record(self.row_courant)
        wopest_id = record.value("opest_id")

        index = self.tbvMoa.currentIndex()
        if not index.isValid():
            return
        if QMessageBox.question(self, u"Suppression du maître d'ouvrage", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            query = QSqlQuery(self.db)

            wope_code = self.leCodeOpe.text()
            wrelation = "ope_suivi_thermi"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("SELECT opest_id FROM " + wrelation + " WHERE opest_ope_code = '" + wope_code + "'")
            if query.exec_():
                if query.next():
                    wopest_id = query.value(0)

            wid = ""
            selection = self.tbvMoa.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            wrelation = "real_suivi_thermi"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query.prepare("DELETE FROM " + wrelation + " WHERE rst_opest_id = '" + str(wopest_id) + "' and rst_moa_id = '" + str(wid) + "'")
            if not query.exec_():
                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce maître d'ouvrage ...", QMessageBox.Ok)
            self.modelMoa.setFilter("opest_id = %i" % wopest_id)

    def verrouillage(self):
        '''Verrouille les champs de saisie automatique si coché'''

        if self.chkVerrouAuto.isChecked():
            self.dateDebut.setEnabled(False)
            self.dateFin.setEnabled(False)
            self.spnDuree.setEnabled(False)
            self.spnTiMax.setEnabled(False)
            self.spnTiMin.setEnabled(False)
            self.spnAjmaxTi.setEnabled(False)
            self.dateAjmaxTi.setEnabled(False)
            self.spnTmjMin.setEnabled(False)
            self.spnTmjMax.setEnabled(False)
            self.spnTmpMoy.setEnabled(False)
            self.spnTm30jMax.setEnabled(False)
            self.spnNbjTmj4_19.setEnabled(False)
            self.spnTmj4_19.setEnabled(False)
            self.spnTmjInf4.setEnabled(False)
            self.spnTmjSup19.setEnabled(False)
            self.spnCsfSup19.setEnabled(False)
            self.spnCsfSupeg25.setEnabled(False)
            self.spnCsfSupeg15.setEnabled(False)
            self.datePonte.setEnabled(False)
            self.spnIncubation.setEnabled(False)
            self.dateEclosion.setEnabled(False)
            self.spnResorption.setEnabled(False)
            self.dateEmergence.setEnabled(False)
            self.spnNbjPel.setEnabled(False)
            self.spnSup15pel.setEnabled(False)
            self.spnCsfSup15pel.setEnabled(False)
            self.spnInf1_5pel.setEnabled(False)
            self.spnCsfInf1_5pel.setEnabled(False)

        else:
            self.dateDebut.setEnabled(True)
            self.dateFin.setEnabled(True)
            self.spnDuree.setEnabled(True)
            self.spnTiMax.setEnabled(True)
            self.spnTiMin.setEnabled(True)
            self.spnAjmaxTi.setEnabled(True)
            self.dateAjmaxTi.setEnabled(True)
            self.spnTmjMin.setEnabled(True)
            self.spnTmjMax.setEnabled(True)
            self.spnTmpMoy.setEnabled(True)
            self.spnTm30jMax.setEnabled(True)
            self.spnNbjTmj4_19.setEnabled(True)
            self.spnTmj4_19.setEnabled(True)
            self.spnTmjInf4.setEnabled(True)
            self.spnTmjSup19.setEnabled(True)
            self.spnCsfSup19.setEnabled(True)
            self.spnCsfSupeg25.setEnabled(True)
            self.spnCsfSupeg15.setEnabled(True)
            self.datePonte.setEnabled(True)
            self.spnIncubation.setEnabled(True)
            self.dateEclosion.setEnabled(True)
            self.spnResorption.setEnabled(True)
            self.dateEmergence.setEnabled(True)
            self.spnNbjPel.setEnabled(True)
            self.spnSup15pel.setEnabled(True)
            self.spnCsfSup15pel.setEnabled(True)
            self.spnInf1_5pel.setEnabled(True)
            self.spnCsfInf1_5pel.setEnabled(True)

    def verrouillageModif(self):
        '''Verrouille les champs afin d'éviter les modifications intempestive'''

        self.saisieAutoBool = False
        self.wthermi_geom = ""
        if self.chkVerrouModif.isChecked():
            self.leCodeOpe.setEnabled(False)
            self.cmbRiviere.setEnabled(False)
            self.cmbStation.setEnabled(False)
            self.btnImpCsv.setEnabled(False)
            self.btnCoordonnee.setEnabled(False)
            self.btnAjoutFiche.setEnabled(False)
            self.btnRetraitFiche.setEnabled(False)
            self.btnExcel.setEnabled(True)
            if self.boolNew == False:
                self.btnModif.setEnabled(False)
        else:
            self.leCodeOpe.setEnabled(True)
            self.cmbRiviere.setEnabled(True)
            self.cmbStation.setEnabled(True)
            self.btnImpCsv.setEnabled(True)
            self.btnCoordonnee.setEnabled(True)
            self.codeOpe = self.leCodeOpe.text()
            self.btnAjoutFiche.setEnabled(True)
            self.btnRetraitFiche.setEnabled(True)
            self.btnExcel.setEnabled(False)
            if self.boolNew == False:
                self.btnModif.setEnabled(True)

        self.btnCoordonnee.setChecked(False)
        if self.point_click != "":
            self.mc.scene().removeItem(self.point_click)
            self.point_click = ""

class Ope_moa_ajout_dialog(QDialog, Ui_dlgMoaAjoutForm):
    '''
    Class de la fenêtre permettant d'ajouter un maître d'ouvrage

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgMoaAjoutForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgMoaAjoutForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wopest_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage de la combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wopest_id: identifiant du suivi courant
        :type wopest_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ope_moa_ajout_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wopest_id = wopest_id
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
        '''Enregistre le maître d'ouvrage comme lié au suivi'''

        wrecord = self.cmbMoa.model().record(self.cmbMoa.currentIndex())
        wmoa = wrecord.value(0)

        query = QSqlQuery(self.db)

        wrelation = "real_suivi_thermi"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("INSERT INTO " + wrelation + " (rst_opest_id, rst_moa_id) VALUES (?, ?)")
        query.addBindValue(self.wopest_id)
        query.addBindValue(wmoa)
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur - Ajout du maître d'ouvrage", query.lastError().text(), QMessageBox.Ok)
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
