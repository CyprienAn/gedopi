# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du formulaire "Droits de pêche" du plugin.

# Import des modules Python, PyQt5 et QGIS nécessaire à l'exécution de ce fichier
import sys
import os
# import datetime
# import processing
from functools import partial
from PyQt5.QtCore import (Qt, QDate)
from PyQt5.QtGui import (QCursor)
from PyQt5.QtWidgets import (QApplication, QDataWidgetMapper, QDialog, QFileDialog, QDockWidget, QHeaderView, QMessageBox, QTableView)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlQueryModel, QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel)
from qgis.core import (QgsCoordinateReferenceSystem, QgsExpression, QgsExpressionContext, QgsFeatureRequest, QgsFeature, QgsCoordinateTransform)
from qgis.gui import (QgsMessageBar)

# Initialise les ressources Qt à partir du fichier resources.py
from .resources_rc import *

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire
from bopeMainForm import (Ui_dwcBopeMainForm)
from bopeAjouRivForm import (Ui_dlgBopeAjoutRiviereForm)
from bopeProprioForm import (Ui_dlgBopeProprioForm)
from bopeRechercheProprioForm import (Ui_dlgBopeRechercheProprioForm)
from bopeCreaProprioForm import (Ui_dlgBopeCreaProprioForm)
from bopeModifProprioForm import (Ui_dlgBopeModifProprioForm)
from bopeAjouParcelleForm import (Ui_dlgBopeAjoutParcelleForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

# Import du script de filtrage des droits de pêche
from .bailPecheFiltrage import (Filtrage_bope_dialog)

class Bail_peche_dialog(QDockWidget, Ui_dwcBopeMainForm):
    '''
    Class principal du formulaire "Droits de pêche"

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
        self.modelBauxPe = None
        self.mapper = None
        self.modelAappma = None
        self.modelProprietaire = None
        self.modelRiviere= None

        # Variables diverses
        self.pdfBool = False
        self.boolNew = False

        # Slot pour le filtrage cartographique
        self.slot_bope_select_changed = None
        slot = partial(self.bope_select_changed, 2)

        # Connexion des événements
        self.btnFiltreCartoManuel.clicked.connect(slot)
        self.btnFiltreAttributaire.clicked.connect(self.filtreAttributaire)
        self.btnDeleteFiltrage.clicked.connect(self.bope_annule_filtrage)

        self.btnZoom.clicked.connect(self.zoomBope)
        self.btnSelection.clicked.connect(self.selectionBope)

        self.btnPremier.clicked.connect(lambda: self.saveRecord("first"))
        self.btnPrec.clicked.connect(lambda: self.saveRecord("prev"))
        self.btnSuiv.clicked.connect(lambda: self.saveRecord("next"))
        self.btnDernier.clicked.connect(lambda: self.saveRecord("last"))

        self.btnAjoutRiviere.clicked.connect(self.ajoutRiviere)
        self.btnSuppRiviere.clicked.connect(self.suppRiviere)
        self.btnAjoutParcelle.clicked.connect(self.ajoutParcelle)
        self.btnSuppParcelle.clicked.connect(self.suppParcelle)
        self.btnZoomParcelle.clicked.connect(self.zoomParcelle)
        self.btnSelectParcelle.clicked.connect(self.selectionParcelle)
        self.btnOuvrePdf.clicked.connect(self.openPdf)
        self.btnAjoutPdf.clicked.connect(self.ajoutPdf)
        self.btnRetraitPdf.clicked.connect(self.retraitPdf)
        self.btnCherchProprio.clicked.connect(self.cherchProprio)
        self.btnFiche.clicked.connect(self.ficheProprio)

        self.btnNouveau.clicked.connect(self.nouveau)
        self.btnEnregistrer.clicked.connect(self.enregistrer)
        self.btnSupprimer.clicked.connect(self.supprimer)
        self.btnAnnuler.clicked.connect(self.annuler)

        self.btnCreaProprio.clicked.connect(self.creaProprio)
        self.btnModifProprio.clicked.connect(self.modifProprio)
        self.btnSuppProprio.clicked.connect(self.suppProprio)

        self.dateSign.dateChanged.connect(self.dateFinAuto)
        self.chkIntemporel.stateChanged.connect(self.bailIntemporel)

        # Initialisation du nombre de page du formulaire
        self.row_courant = 0
        self.row_count = 0
        self.infoMessage = u"Gedopi - Droit de pêche"

        self.etat_courant = 0

        # Initialisation du formulaire
        if self.verifiePresenceCouche():
            self.setupModel()
            if not self.validationParcelleRiv():
                QMessageBox.warning(self, u"Attention", self.messageValidation, QMessageBox.Ok)
        else:
            self.clearFields()
            self.activeFields(False)
            self.activeButtons(False)

    def init_event(self):
        '''
        Appelé par setupModel(), supprime la sélection en cours si existante
        et supprime le filtrage en cours si existant
        '''
        layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
        if layer:
            layer.removeSelection()
            self.slot_bope_select_changed = partial(self.bope_select_changed, 1)
            layer.selectionChanged.connect(self.slot_bope_select_changed)

    def disconnect_event(self):
        '''
        Appelé par onVisibilityChange(), soit, quand le QDockWidget se ferme,
        déconnecte le filtrage et le rowChange()
        '''
        layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
        if layer:
            layer.selectionChanged.disconnect(self.slot_bope_select_changed)
            self.mapper.currentIndexChanged.disconnect(self.rowChange)

    def bope_select_changed(self, origine):
        '''
        Gère le filtrage cartographique des enregistrements

        :param origine: définie si le filtrage est cartographique ou attributaire,
                obtenu via les partial(self.bope_select_changed, origine)
        :type origine: int
        '''
        if self.etat_courant != 10:
            layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
            if layer:
                if layer.selectedFeatureCount() != 0:
                    self.btnFiltreCartoManuel.setEnabled(True)
                    if (origine == 1 and self.chkFiltreCartoAuto.isChecked()) or (origine == 2):
                        if (layer.selectedFeatureCount() >= 1000) and (QGis.QGIS_VERSION_INT < 21203):
                            layer.removeSelection()
                            self.iface.messageBar().pushMessage("Erreur : ", u"Le nombre d'éléments sélectionnés est trop important ...", level=QgsMessageBar.CRITICAL, duration=3)
                        else:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Droit de pêche"
                            wparam = ""
                            nbreTour = 0
                            for feature in layer.selectedFeatures():
                                expressContext = QgsExpressionContext()
                                expressContext.setFeature(feature)
                                wid = QgsExpression("par_bope_id").evaluate(expressContext)
                                nbreTour += 1
                                wparam += str(wid) + ","
                            if (wparam != ""):
                                wparam = "(" + wparam[0:len(wparam) - 1] + ")"
                                if self.modelBauxPe:
                                    self.modelBauxPe.setFilter("bope_id in %s" % wparam)
                                    self.modelBauxPe.select()
                                    self.row_count = self.modelBauxPe.rowCount()
                                    if nbreTour != self.row_count:
                                        self.iface.messageBar().pushMessage("Info : ", str(nbreTour - self.row_count) + u" parcelles sélectionnées n'ont pas de droits de pêche lié", level=QgsMessageBar.INFO, duration=5)
                                    self.mapper.toFirst()
                                    self.btnDeleteFiltrage.setEnabled(True)
                else:
                    self.btnFiltreCartoManuel.setEnabled(False)

    def bope_annule_filtrage(self):
        '''Annule le filtrage cartographique ou attributaire'''
        if self.modelBauxPe:
            self.infoMessage = u"Gedopi - Droit de pêche"
            self.modelBauxPe.setFilter("")
            self.modelBauxPe.select()
            self.row_count = self.modelBauxPe.rowCount()
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
        Vérifie la présence de la couche des parcelles et renvoi dans __init__, True ou False,
        active le setupModel si return True,
        verouille le formulaire si return False
        '''
        self.layer = None
        self.layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
        if self.layer:
            return True
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des parcelles n'est pas chargée ...", level= QgsMessageBar.CRITICAL, duration = 5)
            return False

    def validationParcelleRiv(self):
        '''
        Vérifie que tous les droits de pêches soient reliés à au moins une parcelle et rivière et renvoi dans __init__, True ou False,
        rien ne se passe si return True,
        affiche une fenêtre indiquant les erreurs si return False
        '''

        query = QSqlQuery(self.db)
        wrelation = "droit_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("SELECT bope_id FROM " + wrelation)
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur validation initiale des droits de pêche", query.lastError().text(), QMessageBox.Ok)
        else:
            wbope_id = ""
            listBopePar = []
            listBopeRiv = []
            size = query.size()
            sizeMax = query.size()
            while size > 0:
                if query.next():
                    listBopePar.append(query.value(0))
                    listBopeRiv.append(query.value(0))
                    if sizeMax == size:
                        wbope_id = "" + str(query.value(0)) + ""
                    else :
                        wbope_id = wbope_id + ", " + str(query.value(0)) + ""
                    size -= 1

        if wbope_id != "":
            queryPar = QSqlQuery(self.db)
            wrelation = "parcelle"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryPar.prepare("SELECT par_bope_id FROM " + wrelation + " WHERE par_bope_id in (" + wbope_id + ")")
            if not queryPar.exec_():
                QMessageBox.critical(self, u"Erreur validation initiale des parcelles", queryPar.lastError().text(), QMessageBox.Ok)
            else:
                wpar_id = ""
                size = queryPar.size()
                while size > 0:
                    if queryPar.next():
                        wpar_id = queryPar.value(0)
                        for elem in listBopePar:
                            if wpar_id == elem:
                                listBopePar.remove(wpar_id)
                        size -= 1

            queryRiv = QSqlQuery(self.db)
            wrelation = "bail_cours_eau"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            queryRiv.prepare("SELECT bce_bope_id FROM " + wrelation + " WHERE bce_bope_id in (" + wbope_id + ")")
            if not queryRiv.exec_():
                QMessageBox.critical(self, u"Erreur validation initiale des bail_cours_eau", queryRiv.lastError().text(), QMessageBox.Ok)
            else:
                wriv_id = ""
                size = queryRiv.size()
                while size > 0:
                    if queryRiv.next():
                        wriv_id = queryRiv.value(0)
                        for elem in listBopeRiv:
                            if wriv_id == elem:
                                listBopeRiv.remove(wriv_id)
                        size -= 1

        if listBopePar or listBopeRiv:
            self.messageValidation = u"Les droits de pêches suivants, n'ont pas de parcelles liés : \n " + str(listBopePar) + u" \n Les droits de pêches suivants, n'ont pas de rivières liés : \n" + str(listBopeRiv)
            return False
        else:
            return True

    def closeDatabase(self):
        '''Supprime certaines variables et déconnecte la base de données'''

        self.tbvRiviere.setModel(None)
        self.mapper.setModel(None)

        del self.modelBauxPe
        del self.modelProprietaire
        del self.modelAappma
        del self.modelRiviere

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

            if (not self.db.open()):
                QMessageBox.critical(self, "Erreur", u"Impossible de se connecter à la base de données ...", QMessageBox.Ok)
                QApplication.restoreOverrideCursor()
                return

        # Création du modèle des Baux de pêche
        self.modelBauxPe = QSqlRelationalTableModel(self, self.db)
        wrelation = "droit_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelBauxPe.setTable(wrelation)
        self.modelBauxPe.setSort(0, Qt.AscendingOrder)
        if (not self.modelBauxPe.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Baux de Pêche dans le setupModel() : \n" + self.modelBauxPe.lastError().text(), QMessageBox.Ok)
        self.row_count = self.modelBauxPe.rowCount()

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.setModel(self.modelBauxPe)
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))

        # Remplissage des cases droit_peche
        self.mapper.addMapping(self.leBopeId, self.modelBauxPe.fieldIndex("bope_id"))
        self.mapper.addMapping(self.chkPossession, self.modelBauxPe.fieldIndex("bope_existe"))
        self.mapper.addMapping(self.chkOrigine, self.modelBauxPe.fieldIndex("bope_origine_fede"))
        self.mapper.addMapping(self.chkIntemporel, self.modelBauxPe.fieldIndex("bope_infini"))
        self.mapper.addMapping(self.dateSign, self.modelBauxPe.fieldIndex("bope_date_sign"))
        self.mapper.addMapping(self.dateFin, self.modelBauxPe.fieldIndex("bope_date_fin"))

        # Création du modèle Rivière
        self.modelRiviere = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_cours_eau" #v_cours_eau est une vue dans postgresql
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelRiviere.setTable(wrelation)
        self.modelRiviere.setSort(0, Qt.AscendingOrder)

        # Remplissage du tableau avec le modèle Rivière
        self.modelRiviere.setHeaderData(self.modelRiviere.fieldIndex("ceau_code_hydro"), Qt.Horizontal, "Code hydro")
        self.modelRiviere.setHeaderData(self.modelRiviere.fieldIndex("ceau_nom"), Qt.Horizontal, u"Cours d'eau")

        if (not self.modelRiviere.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Rivière dans le setupModel() : \n" + self.modelRiviere.lastError().text(), QMessageBox.Ok)

        self.modelRiviere.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvRiviere.setModel(self.modelRiviere)
        self.tbvRiviere.setSelectionMode(QTableView.SingleSelection)
        self.tbvRiviere.setSelectionBehavior(QTableView.SelectRows)
        self.tbvRiviere.setColumnHidden(self.modelRiviere.fieldIndex("bce_ceau_id"), True)
        self.tbvRiviere.setColumnHidden(self.modelRiviere.fieldIndex("bce_bope_id"), True)
        self.tbvRiviere.setColumnHidden(self.modelRiviere.fieldIndex("ceau_affluent"), True)
        self.tbvRiviere.resizeColumnsToContents()
        self.tbvRiviere.horizontalHeader().setStretchLastSection(True)

        # Création du modèle Parcelle
        self.modelParcelle = QSqlRelationalTableModel(self, self.db)

        wrelation = "v_parcelle" #v_parcelle est une vue dans postgresql
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelParcelle.setTable(wrelation)
        self.modelParcelle.setSort(0, Qt.AscendingOrder)

        # Remplissage du tableau avec le modèle Parcelle
        self.modelParcelle.setHeaderData(self.modelParcelle.fieldIndex("com_nom"), Qt.Horizontal, "Commune")
        self.modelParcelle.setHeaderData(self.modelParcelle.fieldIndex("sec_nom"), Qt.Horizontal, "Section")
        self.modelParcelle.setHeaderData(self.modelParcelle.fieldIndex("par_numero"), Qt.Horizontal, u"Parcelle")
        self.modelParcelle.setHeaderData(self.modelParcelle.fieldIndex("sec_com_abs"), Qt.Horizontal, "Code absorption")

        if (not self.modelParcelle.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Parcelle dans le setupModel() : \n" + self.modelParcelle.lastError().text(), QMessageBox.Ok)

        self.modelParcelle.setEditStrategy(QSqlTableModel.OnManualSubmit)

        self.tbvParcelle.setModel(self.modelParcelle)
        self.tbvParcelle.setSelectionMode(QTableView.MultiSelection)
        self.tbvParcelle.setSelectionBehavior(QTableView.SelectRows)
        self.tbvParcelle.setColumnHidden(self.modelParcelle.fieldIndex("par_id"), True)
        self.tbvParcelle.setColumnHidden(self.modelParcelle.fieldIndex("par_bope_id"), True)
        self.tbvParcelle.resizeColumnsToContents()
        self.tbvParcelle.horizontalHeader().setStretchLastSection(True)
        self.tbvParcelle.setColumnWidth(0, 20)

        self.mapper.currentIndexChanged.connect(self.rowChange)

        if self.row_count == 0 :

            self.modelAappma = QSqlTableModel(self, self.db)
            wrelation = "aappma"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelAappma.setTable(wrelation)
            self.modelAappma.setSort(1, Qt.AscendingOrder)
            if (not self.modelAappma.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle AAPPMA dans le rowChange() : \n" + self.modelAappma.lastError().text(), QMessageBox.Ok)
            self.cmbAappma.setModel(self.modelAappma)
            self.cmbAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

            self.modelProprietaire = QSqlTableModel(self, self.db)
            wrelation = "proprietaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            query = QSqlQuery("select pro_id, pro_nom || ' ; ' || pro_adresse as infoProprio from " + wrelation + " order by pro_nom;", self.db)
            self.modelProprietaire.setQuery(query)
            if self.modelProprietaire.lastError().isValid():
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Propriétaire dans le rowChange() : \n" + self.modelProprietaire.lastError().text(), QMessageBox.Ok)
            self.cmbProprio.setModel(self.modelProprietaire)
            self.cmbProprio.setModelColumn(self.modelProprietaire.fieldIndex("infoProprio"))

            proprietaireNR = ""
            self.cmbProprio.addItem(proprietaireNR)
            indexProNR = self.cmbProprio.count()
            self.cmbProprio.setCurrentIndex(indexProNR - 1)

        # Vérification de la présence d'enregistrements
        if self.modelBauxPe.rowCount() == 0:
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

        self.leBopeId.setText("")
        self.chkPossession.setChecked(False)
        self.chkOrigine.setChecked(False)
        self.chkIntemporel.setChecked(False)
        self.dateSign.setDate(QDate(2000,1,1))
        self.dateFin.setDate(QDate(2000,1,1))
        modelRaz = QSqlQueryModel()
        self.tbvParcelle.setModel(modelRaz)
        self.tbvRiviere.setModel(modelRaz)

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
        self.leBopeId.setEnabled(False)
        self.tbvRiviere.setEnabled(active)
        self.tbvParcelle.setEnabled(active)
        self.chkPossession.setEnabled(active)
        self.chkOrigine.setEnabled(active)
        self.chkIntemporel.setEnabled(active)
        self.dateSign.setEnabled(active)
        self.dateFin.setEnabled(active)
        self.cmbProprio.setEnabled(active)
        self.cmbAappma.setEnabled(active)
        self.lblEcheance.hide()

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
        self.btnFiltreAttributaire.setEnabled(active)
        self.btnDeleteFiltrage.setEnabled(False)
        self.chkFiltreCartoAuto.setEnabled(active)

        self.btnAjoutRiviere.setEnabled(active)
        self.btnSuppRiviere.setEnabled(active)

        self.btnPremier.setEnabled(active)
        self.btnPrec.setEnabled(active)
        self.btnSuiv.setEnabled(active)
        self.btnDernier.setEnabled(active)

        self.btnZoom.setEnabled(active)
        self.btnSelection.setEnabled(active)

        self.btnAjoutPdf.setEnabled(active)
        self.btnRetraitPdf.setEnabled(active)
        self.btnOuvrePdf.setEnabled(active)

        self.btnFiche.setEnabled(active)
        self.btnCherchProprio.setEnabled(active)

        self.btnCreaProprio.setEnabled(True)
        self.btnModifProprio.setEnabled(True)
        self.btnSuppProprio.setEnabled(True)

        self.btnEnregistrer.setEnabled(active)
        self.btnNouveau.setEnabled(True)
        self.btnSupprimer.setEnabled(active)
        self.btnAnnuler.setEnabled(False)

        self.btnZoomParcelle.setEnabled(active)
        self.btnSelectParcelle.setEnabled(active)

        self.btnAjoutParcelle.setEnabled(active)
        self.btnAjoutRiviere.setEnabled(active)
        self.btnSuppParcelle.setEnabled(active)
        self.btnSuppRiviere.setEnabled(active)

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

        self.btnNouveau.setEnabled(not active)
        self.btnSupprimer.setEnabled(not active)
        self.btnEnregistrer.setEnabled(active)
        self.btnAnnuler.setEnabled(active)

        self.btnZoom.setEnabled(not active)
        self.btnSelection.setEnabled(not active)
        self.btnZoomParcelle.setEnabled(not active)
        self.btnSelectParcelle.setEnabled(not active)

        self.btnAjoutParcelle.setEnabled(not active)
        self.btnAjoutRiviere.setEnabled(not active)
        self.btnSuppParcelle.setEnabled(not active)
        self.btnSuppRiviere.setEnabled(not active)
        self.btnOuvrePdf.setEnabled(not active)

    def saveRecord(self, wfrom):
        '''Permet le passage d'un enregistrement à un autre en fonction du bouton de défilement'''

        row = self.mapper.currentIndex()
        if wfrom == "first":
            row = 0
        elif wfrom == "prev":
            row = 0 if row <= 1 else row - 1
        elif wfrom == "next":
            row += 1
            if row >= self.modelBauxPe.rowCount():
                row = self.modelBauxPe.rowCount() - 1
        elif wfrom == "last":
            row = self.modelBauxPe.rowCount() - 1

        self.mapper.setCurrentIndex(row)
        if self.row_count == 1:
            self.rowChange(0)

    def afficheInfoRow(self):
        '''Affiche en titre du QDockWidget, le nom du formulaire ainsi que l'enregistrement en courant / le nombre total'''

        self.setWindowTitle(self.infoMessage + " (" + str(self.row_courant + 1) + " / " + str(self.row_count) + ")")

    def rowChange(self, row):
        '''
        Permet la mise à jour des champs lorsque l'enregistrement change

        :param row: le numéro de l'enregistrement courant,
                obtenu d'après saveRecord()
        :type row: int
        '''

        # Boutons de naviguation
        self.row_courant = row
        self.btnPrec.setEnabled(row > 0)
        self.btnSuiv.setEnabled(row < self.modelBauxPe.rowCount() - 1)

        # Record bail de pêche courant
        record = self.modelBauxPe.record(row)

        # Récupération de la clé de la parcelle
        wbope_par_id = record.value(self.modelBauxPe.fieldIndex("bope_par_id"))

        # Record de l'AAPPMA courante
        wbope_apma_id = record.value(self.modelBauxPe.fieldIndex("bope_apma_id"))

        # Filtrage aappma
        self.modelAappma = QSqlTableModel(self, self.db)
        wrelation = "aappma"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelAappma.setTable(wrelation)
        self.modelAappma.setSort(1, Qt.AscendingOrder)
        if (not self.modelAappma.select()):
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle AAPPMA dans le rowChange() : \n" + self.modelAappma.lastError().text(), QMessageBox.Ok)

        self.cmbAappma.setModel(self.modelAappma)
        self.cmbAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        # Sélection AAPPMA
        result = self.cmbAappma.model().match(self.cmbAappma.model().index(0, 0), Qt.EditRole, wbope_apma_id, -1, Qt.MatchExactly)
        if result:
            self.cmbAappma.setCurrentIndex(result[0].row())

        # Record du propriétaire courant
        wbope_pro_id = record.value(self.modelBauxPe.fieldIndex("bope_pro_id"))

        # Filtrage propriétaire
        self.modelProprietaire = QSqlTableModel(self, self.db)
        wrelation = "proprietaire"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query = QSqlQuery("select pro_id, pro_nom || ' ; ' || pro_adresse as infoProprio from " + wrelation + " order by pro_nom;", self.db)
        self.modelProprietaire.setQuery(query)
        if self.modelProprietaire.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Propriétaire dans le rowChange() : \n" + self.modelProprietaire.lastError().text(), QMessageBox.Ok)

        # Attribution du modèle propriétaire à la combobox correspondante
        self.cmbProprio.setModel(self.modelProprietaire)
        self.cmbProprio.setModelColumn(self.modelProprietaire.fieldIndex("infoProprio"))

        proprietaireNR = ""
        self.cmbProprio.addItem(proprietaireNR)

        # Sélection propriétaire
        result = self.cmbProprio.model().match(self.cmbProprio.model().index(0, 0), Qt.EditRole, wbope_pro_id, -1, Qt.MatchExactly)
        if result:
            self.cmbProprio.setCurrentIndex(result[0].row())
        else:
            indexProNR = self.cmbProprio.count()
            self.cmbProprio.setCurrentIndex(indexProNR - 1)

        # Filtrage du tableau des rivières
        id = record.value("bope_id")
        self.modelRiviere.setFilter("bce_bope_id = %i" % id)

        # Filtrage du tableau des parcelles
        id = record.value("bope_id")
        self.modelParcelle.setFilter("par_bope_id = %i" % id)

        # Permet d'afficher un avertissement indiquant que le bail courant est ou va être dépassé
        self.lblEcheance.setText(u"Attention ce bail arrive à échéance !!!")

        dateEcheance = self.dateFin.date()
        dateDay = QDate.currentDate()
        echeance = dateEcheance.daysTo(dateDay)

        if dateEcheance < dateDay and dateEcheance != QDate(2000, 1, 1):
            self.lblEcheance.setText(u"Attention, ce bail est dépassé de " + str(echeance) + " jour(s) !!!")
            self.lblEcheance.show()
        elif abs(echeance) <= 90:
            self.lblEcheance.setText(u"Attention, ce bail arrive à échéance dans " + str(abs(echeance)) + " jour(s) !!!")
            self.lblEcheance.show()
        else:
            self.lblEcheance.hide()

        # Affiche le nombre d'enregistrement ainsi que celui actuel
        self.afficheInfoRow()

    def dateFinAuto(self):
        '''Permet de calculer automatiquement la date de fin en utilisant la date paramétre de la base de données'''

        query = QSqlQuery(self.db)
        wrelation = "parametre"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("select para_duree_droit_peche from " + wrelation)
        wduree = ""
        if query.exec_():
            if query.next():
                wduree = query.value(0)

        dateCourant = self.dateSign.date()
        dateCourant = dateCourant.addYears(wduree)
        self.dateFin.setDate(dateCourant)

    def bailIntemporel(self):
        '''Si la case Intemporel est cochée alors le bail se prolonge jusqu'en 2099'''

        if self.chkIntemporel.isChecked():
            self.dateFin.setDate(QDate(2099,12,31))
            self.dateFin.hide()
            self.lblDateFin.hide()
        else:
            self.dateFin.show()
            self.lblDateFin.show()
            self.dateFinAuto()

    def zoomBope(self):
        '''Permet de zoomer le canevas de la carte sur le droit courante'''

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                record = self.modelBauxPe.record(row)
                wid = record.value("bope_id")

                query = QSqlQuery(self.db)
                wrelation = "parcelle"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("SELECT par_id FROM " + wrelation + " WHERE par_bope_id = " + str(wid))
                if not query.exec_():
                    QMessageBox.critical(self, u"Erreur", query.lastError().text(), QMessageBox.Ok)

                if query.exec_():
                    wpar_id = ""
                    size = query.size()
                    sizeMax = query.size()
                    while size > 0:
                        if query.next():
                            if sizeMax == size:
                                wpar_id = "'" + str(query.value(0)) + "'"
                            else :
                                wpar_id = wpar_id + ", '" + str(query.value(0)) + "'"
                            size -= 1

                layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')

                query = "par_id in (" + wpar_id + ")"
                request = QgsFeatureRequest().setFilterExpression(query)

                iter = layer.getFeatures(request)
                feat = QgsFeature()
                iter.nextFeature(feat)
                box = feat.geometry().boundingBox()
                while iter.nextFeature(feat):
                    box.combineExtentWith(feat.geometry().boundingBox())

                if box:
                    if self.mc.hasCrsTransformEnabled():
                        crsDest = self.mc.mapSettings().destinationCrs()
                        crsSrc = layer.crs()
                        xform = QgsCoordinateTransform(crsSrc, crsDest)
                        box = xform.transform(box)
                    self.mc.setExtent(box.buffer(50))
                    self.mc.refresh()

    def selectionBope(self):
        '''Permet de sélectionner les parcelles correspondant à l'enregistrement courant'''

        if self.mapper:
            row = self.mapper.currentIndex()
            self.etat_courant = 10
            if row >= 0:
                record = self.modelBauxPe.record(row)
                wid = record.value("bope_id")

                query = QSqlQuery(self.db)
                wrelation = "parcelle"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("SELECT par_id FROM " + wrelation + " WHERE par_bope_id = " + str(wid))
                if not query.exec_():
                    QMessageBox.critical(self, u"Erreur", query.lastError().text(), QMessageBox.Ok)

                if query.exec_():
                    wpar_id = ""
                    size = query.size()
                    sizeMax = query.size()
                    while size > 0:
                        if query.next():
                            if sizeMax == size:
                                wpar_id = "'" + str(query.value(0)) + "'"
                            else :
                                wpar_id = wpar_id + ", '" + str(query.value(0)) + "'"
                            size -= 1

                layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
                layer.removeSelection()

                query = "par_id in (" + wpar_id + ")"
                selection = layer.getFeatures(QgsFeatureRequest().setFilterExpression(query))
                layer.setSelectedFeatures([k.id() for k in selection])

                self.etat_courant = 0

    def ajoutPdf(self):
        '''Permet de joindre un scan du bail de pêche'''

        openfile = ""
        openfile = QFileDialog.getOpenFileName(self, "Open File", "", "PDF / Images (*.pdf *.jpeg *.png *.jpg)")
        if openfile != "":
            self.cheminPdf = unicode(openfile)
            self.pdfBool = True

    def retraitPdf(self):
        '''Permet de délier un scan du bail de pêche'''
        if QMessageBox.question(self, u"Délier", u"Etes-vous certain de vouloir délier le fichier ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            self.cheminPdf = ""
            self.pdfBool = True

    def openPdf(self):
        '''Permet d'ouvrir le scan du bail lié'''

        row = self.mapper.currentIndex()
        record = self.modelBauxPe.record(row)
        lienPdf = record.value(u"bope_pdf")
        if lienPdf == "" or lienPdf == None or lienPdf == "NULL":
            self.iface.messageBar().pushMessage("Info : ", u"Pas de fichier joint !", level= QgsMessageBar.INFO, duration = 5)
        else :
            try:
                os.startfile(lienPdf)
            except:
                self.iface.messageBar().pushMessage("Info : ", u"Le fichier est introuvable !", level= QgsMessageBar.WARNING, duration = 5)

    def nouveau(self):
        '''Prépare le formulaire pour la saisie d'un nouveau bail'''

        self.boolNew = True
        self.cheminPdf = ""
        self.pdfBool = False

        indexProNR = self.cmbProprio.count()
        self.cmbProprio.setCurrentIndex(indexProNR - 1)
        self.cmbAappma.setCurrentIndex(-1)

        self.activeButtonsModif(True)
        self.clearFields()
        self.activeFields(True)

    def enregistrer(self):
        '''Enregistre les modifications apportées au droit de pêche ou en crée un nouveau'''

        # Récupération des valeurs
        wrecord = self.cmbAappma.model().record(self.cmbAappma.currentIndex())
        wbope_aappma = wrecord.value(0)
        self.aappmaID_NR = wbope_aappma

        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wbope_proprio = wrecord.value(0)

        if self.chkPossession.isChecked() :
            wbope_possession = True
        else:
            wbope_possession = False

        if self.chkOrigine.isChecked() :
            wbope_origine = True
        else:
            wbope_origine = False

        if self.chkIntemporel.isChecked() :
            wbope_intemporel = True
        else:
            wbope_intemporel = False

        self.valeurSign = self.dateSign.date()
        wbope_dateSign  = QDate.toString(self.valeurSign, "yyyy-MM-dd")

        self.valeurFin = self.dateFin.date()
        wbope_dateFin  = QDate.toString(self.valeurFin, "yyyy-MM-dd")

        wbopePdf = ""
        if self.pdfBool ==True:
            if self.cheminPdf == "":
                self.wbopePdf = ""
            else :
                wbopePdf = self.cheminPdf
                self.pdfBool = False
        else :
            row = self.mapper.currentIndex()
            record = self.modelBauxPe.record(row)
            self.cheminPdf = record.value(u"bope_pdf")
            wbopePdf = self.cheminPdf
        if str(wbopePdf) == "NULL":
            wbopePdf = ""

        wbope_id = self.leBopeId.text()

        # Validation et enregistrement
        if self.validation_saisie():
            if self.boolNew == False:
                if QMessageBox.question(self, "Enregistrer", u"Etes-vous certain de vouloir enregistrer les modifications ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

                    filtreCourant = self.modelBauxPe.filter()

                    layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
                    layer.removeSelection()
                    self.bope_annule_filtrage()

                    row = self.mapper.currentIndex()
                    record = self.modelBauxPe.record(row)
                    wid = record.value("bope_id")

                    query = QSqlQuery(self.db)
                    wrelation = "droit_peche"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET bope_existe = " + str(wbope_possession) + ", bope_origine_fede = " + str(wbope_origine) +
                    ", bope_date_sign = '" + wbope_dateSign + "', bope_infini = " + str(wbope_intemporel) + ", bope_date_fin = '" + wbope_dateFin +
                    "', bope_apma_id = " + str(wbope_aappma) + ", bope_pro_id = " + str(wbope_proprio) + ", bope_pdf = '" + wbopePdf + "' WHERE bope_id = '" + str(wbope_id) + "'")

                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Modification du droit de pêche", query.lastError().text(), QMessageBox.Ok)

                    self.setupModel()

                    if filtreCourant != "":
                        self.modelBauxPe.setFilter(filtreCourant)
                        self.row_count = self.modelBauxPe.rowCount()
                        if self.row_count != 0:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Droit de pêche"
                            self.mapper.toFirst()
                            self.btnDeleteFiltrage.setEnabled(True)

            if self.boolNew == True:
                layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
                layer.removeSelection()
                self.bope_annule_filtrage()

                row = self.mapper.currentIndex()
                record = self.modelBauxPe.record(row)
                wid = record.value("bope_id")

                query = QSqlQuery(self.db)
                wrelation = "droit_peche"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("INSERT INTO " + wrelation +
                " (bope_existe, bope_origine_fede, bope_date_sign, bope_infini, bope_date_fin, bope_apma_id, bope_pro_id, bope_pdf) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
                query.addBindValue(wbope_possession)
                query.addBindValue(wbope_origine)
                query.addBindValue(wbope_dateSign)
                query.addBindValue(wbope_intemporel)
                query.addBindValue(wbope_dateFin)
                query.addBindValue(wbope_aappma)
                query.addBindValue(wbope_proprio)
                query.addBindValue(wbopePdf)

                if not query.exec_():
                    QMessageBox.critical(self, u"Erreur - Enregistrement du droit de pêche", query.lastError().text(), QMessageBox.Ok)
                else:
                    self.iface.messageBar().pushMessage("Attention : ", u"N'oubliez pas d'ajouter les parcelles et rivières concernées !", level= QgsMessageBar.INFO, duration = 5)

                # Màj du nombre d'enregistrement
                self.row_count += 1
                if self.row_count == 1:
                    self.modelBauxPe.select()

                # Basculement du formulaire vers la visualisation
                self.annuler(False)
                self.boolNew = False

                self.setupModel()
                self.saveRecord("last") #renvoie sur le dernier enregistrement

    def supprimer (self):
        '''Permet de supprimer le bail courant'''

        filtreCourant = self.modelBauxPe.filter()

        if self.mapper:
            row = self.mapper.currentIndex()
            if row >= 0:
                if QMessageBox.question(self, "Suppression", u"Etes-vous certain de vouloir supprimer ce droit de pêche ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                    record = self.modelBauxPe.record(row)
                    wid = record.value("bope_id")
                    queryPar = QSqlQuery(self.db)
                    wrelation = "parcelle"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    queryPar.prepare("UPDATE " + wrelation + " SET par_bope_id = null WHERE par_bope_id = " + str(wid))
                    if not queryPar.exec_():
                        QMessageBox.critical(self, "Erreur", u"Impossible de délier la parcelle. \n " + queryPar.lastError().text() , QMessageBox.Ok)
                    else:
                        queryRiv = QSqlQuery(self.db)
                        wrelation = "bail_cours_eau"
                        if self.dbType == "postgres":
                            wrelation = self.dbSchema + "." + wrelation
                        queryRiv.prepare("DELETE FROM " + wrelation + " WHERE bce_bope_id = ?")
                        queryRiv.addBindValue(wid)
                        if not queryRiv.exec_():
                            QMessageBox.critical(self, "Erreur", u"Impossible de délier ce cours d'eau. \n" + queryRiv.lastError().text() , QMessageBox.Ok)
                        else:
                            query = QSqlQuery(self.db)
                            wrelation = "droit_peche"
                            if self.dbType == "postgres":
                                wrelation = self.dbSchema + "." + wrelation
                            query.prepare("DELETE FROM " + wrelation + " WHERE bope_id = ?")
                            query.addBindValue(wid)
                            if not query.exec_():
                                QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce droit de pêche. \n " + query.lastError().text() , QMessageBox.Ok)

                    if filtreCourant != "":
                        filtreCourant = filtreCourant.replace(str(wid), "NULL" )

                    self.setupModel()

                    if filtreCourant != "":
                        self.modelBauxPe.setFilter(filtreCourant)
                        self.row_count = self.modelBauxPe.rowCount()
                        if self.row_count != 0:
                            self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Droit de pêche"
                            self.mapper.toFirst()
                            self.btnDeleteFiltrage.setEnabled(True)

    def annuler(self, repositionnement = True):
        '''Annule la saisie d'un nouveau bail'''

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
                # self.saveRecord("last") #renvoie sur le dernier enregistrement
                self.setupModel()

    def validation_saisie(self):
        '''Avant enregistrement, cette méthode doit valider la saisie'''
        if self.valeurFin < self.valeurSign:
            self.iface.messageBar().pushMessage("Erreur : ", u"La date de signature est antérieur à la date d'échéance !", level= QgsMessageBar.CRITICAL, duration = 5)
            saisieOk = False
        elif type(self.aappmaID_NR) != int:
            if self.aappmaID_NR.isNull():
                self.iface.messageBar().pushMessage("Erreur : ", u"Une parcelle est forcément sur une AAPPMA !", level= QgsMessageBar.CRITICAL, duration = 5)
                saisieOk = False
        elif self.cmbProprio.currentText() == "":
            self.iface.messageBar().pushMessage("Erreur : ", u"Un droit de pêche à forcément un propriétaire foncier !", level= QgsMessageBar.CRITICAL, duration = 5)
            saisieOk = False
        else:
            saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

    def ficheProprio(self):
        '''Permet l'ouverture d'une fenêtre montrant la totalité des informations sur le propriétaires'''

        # Récupération de l'identifiant du proprietaire
        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wbope_pro_id = wrecord.value(0)

        # Vérification que le propriétaire n'est pas NULL
        if self.cmbProprio.currentIndex() == -1  or self.cmbProprio.currentText() == "":
            QMessageBox.information(self, u"Propriétaire", u"Pas de propriétaire renseigné")
        else :
            dialog = Fiche_proprio(self.db, self.dbType, self.dbSchema, wbope_pro_id)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.exec_()

    def filtreAttributaire(self):
        '''Permet l'ouverture de la fenêtre de filtre attributaire'''

        dialog = Filtrage_bope_dialog(self.db, self.dbType, self.dbSchema, self.modelBauxPe)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.row_count = self.modelBauxPe.rowCount()
            if self.row_count != 0:
                self.infoMessage = u"(FILTRAGE EN COURS) Gedopi - Droit de pêche"
                self.mapper.toFirst()
                self.btnDeleteFiltrage.setEnabled(True)

    def selectionParcelle(self):
        '''Permet de sélectionner sur le canevas, les parcelles sélectionnées dans le tableau'''

        selection = self.tbvParcelle.selectionModel()
        indexElementSelectionne = selection.selectedRows()
        nbreSelect = len(indexElementSelectionne)
        nbreSelectMax = len(indexElementSelectionne)

        if nbreSelect != 0:
            while nbreSelect > 0:
                    if nbreSelectMax == nbreSelect:
                        wid = "'" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    else :
                        wid = wid + ", '" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    nbreSelect -= 1

            layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
            layer.removeSelection()

            query = "par_id in (" + wid + ")"
            selection = layer.getFeatures(QgsFeatureRequest().setFilterExpression(query))
            layer.setSelectedFeatures([k.id() for k in selection])
        else :
            QMessageBox.critical(self, "Erreur", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def zoomParcelle(self):
        '''Permet de zoomer sur le canevas, sur les parcelles sélectionnées dans le tableau'''

        selection = self.tbvParcelle.selectionModel()
        indexElementSelectionne = selection.selectedRows()
        nbreSelect = len(indexElementSelectionne)
        nbreSelectMax = len(indexElementSelectionne)

        if nbreSelect != 0:
            while nbreSelect > 0:
                    if nbreSelectMax == nbreSelect:
                        wid = "'" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    else :
                        wid = wid + ", '" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    nbreSelect -= 1

            layer = self.gc.getLayerFromLegendByTableProps('parcelle', 'par_geom', '')
            layer.removeSelection()

            query = "par_id in (" + wid + ")"
            request = QgsFeatureRequest().setFilterExpression(query)
            iter = layer.getFeatures(request)
            feat = QgsFeature()
            iter.nextFeature(feat)
            box = feat.geometry().boundingBox()
            while iter.nextFeature(feat):
                box.combineExtentWith(feat.geometry().boundingBox())

            if box:
                if self.mc.hasCrsTransformEnabled():
                    crsDest = self.mc.mapSettings().destinationCrs()
                    crsSrc = layer.crs()
                    xform = QgsCoordinateTransform(crsSrc, crsDest)
                    box = xform.transform(box)
                self.mc.setExtent(box.buffer(50))
                self.mc.refresh()
        else :
            QMessageBox.critical(self, "Erreur", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def ajoutParcelle(self):
        '''Permet l'ouverture de la fenêtre de sélection d'une parcelle'''

        # Récupération de l'identifiant du droit de pêche et ouverture de la fenêtre
        record = self.modelBauxPe.record(self.row_courant)
        wbope_id = record.value("bope_id")
        dialog = Ajout_parcelle(self.db, self.dbType, self.dbSchema, wbope_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelParcelle.setFilter("par_bope_id = %i" % wbope_id)

    def suppParcelle(self):
        '''Permet la suppression de la parcelle liée au droit de pêche'''

        # Vérification qu'une parcelle est sélectionnée
        index = self.tbvParcelle.currentIndex()
        if not index.isValid():
            self.iface.messageBar().pushMessage("Erreur : ", u"Vous n'avez pas sélectionné de parcelle...", level=QgsMessageBar.CRITICAL, duration=3)
            return

        # Récupération de l'id du droit de pêche
        wbope_id = self.leBopeId.text()
        wbope_id = int(wbope_id)

        # Validation et suppression
        if QMessageBox.question(self, u"Suppression de la parcelle", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            selection = self.tbvParcelle.selectionModel()
            indexElementSelectionne = selection.selectedRows()
            nbreSelect = len(indexElementSelectionne)
            nbreSelectMax = len(indexElementSelectionne)
            wid = ""

            if nbreSelect != 0:
                while nbreSelect > 0:
                        if nbreSelectMax == nbreSelect:
                            wid = "'" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                        else :
                            wid = wid + ", '" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                        nbreSelect -= 1
                if wid != "":
                    query = QSqlQuery(self.db)
                    wrelation = "parcelle"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    query.prepare("UPDATE " + wrelation + " SET par_bope_id = null WHERE par_id in (" + wid + ")")
                    if not query.exec_():
                        QMessageBox.critical(self, u"Erreur - Suppression d'une parcelle : ", query.lastError().text(), QMessageBox.Ok)
                    self.modelParcelle.setFilter("par_bope_id = %i" % wbope_id)

    def ajoutRiviere(self):
        '''Permet l'ouverture de la fenêtre de sélection d'une rivière'''

        # Récupération de l'identifiant du droit de pêche et ouverture de la fenêtre
        record = self.modelBauxPe.record(self.row_courant)
        wbope_id = record.value("bope_id")
        dialog = Ajout_riviere(self.db, self.dbType, self.dbSchema, wbope_id)
        dialog.setWindowModality(Qt.ApplicationModal)
        if dialog.exec_():
            self.modelRiviere.setFilter("bce_bope_id = %i" % wbope_id)

    def suppRiviere(self):
        '''Permet la suppression de la rivière liée au droit de pêche'''

        # Vérification qu'une rivière est sélectionnée
        index = self.tbvRiviere.currentIndex()
        if not index.isValid():
            self.iface.messageBar().pushMessage("Erreur : ", u"Vous n'avez pas sélectionné de cours d'eau...", level=QgsMessageBar.CRITICAL, duration=3)
            return

        # Validation et suppression
        if QMessageBox.question(self, u"Suppression du cours d'eau", u"Confirmez-vous la suppression ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:

            # Récupération de l'id du droit de pêche
            wbope_id = self.leBopeId.text()
            wbope_id = int(wbope_id)

            wid = ""
            selection = self.tbvRiviere.selectionModel()
            indexElementSelectionne = selection.selectedRows(1)
            wid = indexElementSelectionne[0].data()

            if wid != "":

                # Suppression du tableau, de la rivière sélectionnée
                query = QSqlQuery(self.db)
                wrelation = "bail_cours_eau"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("DELETE FROM " + wrelation + " WHERE bce_bope_id = '" + str(wbope_id) + "' and bce_ceau_id = '" + str(wid) + "'")
                if not query.exec_():
                    QMessageBox.critical(self, "Erreur", u"Impossible de supprimer ce cours d'eau ...", QMessageBox.Ok)
                self.modelRiviere.setFilter("bce_bope_id = %i" % wbope_id)

    def cherchProprio(self):
        '''Permet l'ouverture de la fenêtre de recherche d'un propriétaire'''

        dialog = Bope_recherche_proprio_dialog(self.db, self.dbType, self.dbSchema, self.cmbProprio)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

    def creaProprio(self):
        '''Permet l'ouverture de la fenêtre de création d'un propriétaire'''

        # Récupération du propriétaire courant première fois
        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wcurrentProprio = wrecord.value(0)

        # Ouverture de la fenêtre de création
        dialog = Creation_proprio(self.db, self.dbType, self.dbSchema, self.cmbProprio)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

        # Récupération du propriétaire courant seconde fois pour comparaison avec la première
        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wajoutProprio = wrecord.value(0)

        # Si les deux correspondent alors un propriétaire à été créé, on recharge la combobox
        if wcurrentProprio == wajoutProprio:
            self.rechargeProprio()

    def modifProprio(self):
        '''Permet l'ouverture de la fenêtre de modification d'un propriétaire'''

        # Récupération du propriétaire courant
        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wbope_pro_id = wrecord.value(0)

        # Vérification que le propriétaire n'est pas NULL
        if self.cmbProprio.currentIndex() == -1 or self.cmbProprio.currentText() == "":
            QMessageBox.information(self, u"Propriétaire", u"Pas de propriétaire renseigné")
        else :
            dialog = Modification_proprio(self.db, self.dbType, self.dbSchema, wbope_pro_id)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.exec_()
            self.rechargeProprio()

    def suppProprio(self):
        '''Permet la suppression d'un propriétaire'''

        # Récupération du propriétaire courant
        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
        wbope_pro_id = wrecord.value(0)

        # Vérification que le propriétaire n'est pas NULL
        if self.cmbProprio.currentIndex() == -1  or self.cmbProprio.currentText() == "":
            QMessageBox.information(self, u"Propriétaire", u"Pas de propriétaire renseigné")
        else:
            if QMessageBox.question(self, "Suppression", u"Etes-vous certain de vouloir supprimer ce propriétaire ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
                        wrecord = self.cmbProprio.model().record(self.cmbProprio.currentIndex())
                        wbope_pro_id = wrecord.value(0)
                        query = QSqlQuery(self.db)
                        wrelation = "proprietaire"
                        if self.dbType == "postgres":
                            wrelation = self.dbSchema + "." + wrelation
                        query.prepare("DELETE FROM " + wrelation + " WHERE pro_id = ?")
                        query.addBindValue(wbope_pro_id)
                        if not query.exec_():
                            QMessageBox.critical(self, "Erreur", query.lastError().text(), QMessageBox.Ok)
                        self.rechargeProprio()

    def rechargeProprio(self):
        '''Permet de recharger la combobox Propriétaire afin d'appliquer les modifications faites à la table propriétaire'''

        # Récupération de l'enregistrement courant
        row = self.mapper.currentIndex()
        record = self.modelBauxPe.record(row)

        # Récupération du propriétaire courant
        wbope_pro_id = record.value(self.modelBauxPe.fieldIndex("bope_pro_id"))

        # Recharge du modèle propriétaire
        self.modelProprietaire.clear()
        wrelation = "proprietaire"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query = QSqlQuery("select pro_id, pro_nom || ' ; ' || pro_adresse as infoProprio from " + wrelation + " order by pro_nom;", self.db)
        self.modelProprietaire.setQuery(query)
        if self.modelProprietaire.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle",u"Erreur au modèle Propriétaire dans le rechargeProprio() : \n" +  self.modelProprietaire.lastError().text(), QMessageBox.Ok)

        # Attribution du modèle à la combobox
        self.cmbProprio.setModel(self.modelProprietaire)
        self.cmbProprio.setModelColumn(self.modelProprietaire.fieldIndex("infoProprio"))

        proprietaireNR = ""
        self.cmbProprio.addItem(proprietaireNR)

        # Rétablissement du propriétaire courant avant recharge
        result = self.cmbProprio.model().match(self.cmbProprio.model().index(0, 0), Qt.EditRole, wbope_pro_id, -1, Qt.MatchExactly)
        if result:
            self.cmbProprio.setCurrentIndex(result[0].row())
        else:
            indexProNR = self.cmbProprio.count()
            self.cmbProprio.setCurrentIndex(indexProNR - 1)

class Creation_proprio(QDialog, Ui_dlgBopeCreaProprioForm):
    '''
    Class de la fenêtre permettant de créer un nouveau propriétaire

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeCreaProprioForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeCreaProprioForm: class
    '''
    def __init__(self, db, dbType, dbSchema, cmbProprio, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param cmbProprio: combobox des propriétaires afin de pouvoir ajouter celui créé via cette fenêtre
        :type cmbProprio: QComboBox

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Creation_proprio, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.setupUi(self)
        self.cmbProprio = cmbProprio

        self.btnChercher.clicked.connect(self.recherche)
        self.btnAjouter.clicked.connect(self.ajouter)
        self.btnAjouter.setEnabled(False)

        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.enregistrer)


    def recherche(self):
        '''Permet de rechercher un propriétaire avant d'en créer un nouveau'''

        # Double les ' afin d'éviter de faire échouer la requête SQL de recherche
        wrecherch = self.leNomRecherche.text()
        if "'" in wrecherch and "''" not in wrecherch:
            wrecherch = wrecherch.replace("'", "''")

        # Requête SQL qui va chercher si le propriétaire saisi existe
        if wrecherch != "":
            self.modelCherche = QSqlRelationalTableModel(self, self.db)
            wrelation = "proprietaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelCherche.setTable(wrelation)
            self.modelCherche.setSort(1, Qt.AscendingOrder)

            self.modelCherche.setFilter("pro_nom ILIKE '%" + wrecherch + "%'")
            self.modelCherche.select()

            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_nom"), Qt.Horizontal, u"Nom")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_telephone"), Qt.Horizontal, u"Téléphone")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_mail"), Qt.Horizontal, u"Email")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_adresse"), Qt.Horizontal, u"Adresse")

            if not self.modelCherche.select():
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Cherche dans le Creation_proprio.recherche() : \n" + self.modelCherche.lastError().text(), QMessageBox.Ok)

            self.tbvProprio.setModel(self.modelCherche)
            self.tbvProprio.setSelectionMode(QTableView.SingleSelection)
            self.tbvProprio.setSelectionBehavior(QTableView.SelectRows)
            self.tbvProprio.setColumnHidden(self.modelCherche.fieldIndex("pro_id"), True)
            self.tbvProprio.resizeColumnsToContents()
            self.tbvProprio.horizontalHeader().setStretchLastSection(True)
            self.btnAjouter.setEnabled(True)
        else:
            QMessageBox.critical(self, "Erreur", u"Aucun nom saisie ...", QMessageBox.Ok)

    def ajouter(self):
        ''' Permet après recherche de placer le propriétaire sélectionné en haut de la combobox dans le dockwidget'''

        wid = ""
        selection = self.tbvProprio.selectionModel()
        indexElementSelectionne = selection.selectedRows(0)
        wid = indexElementSelectionne[0].data()

        if wid != "":
            result = self.cmbProprio.model().match(self.cmbProprio.model().index(0, 0), Qt.EditRole, wid, -1, Qt.MatchExactly)
            if result:
                self.cmbProprio.setCurrentIndex(result[0].row())
                QDialog.accept(self)
        else :
            QMessageBox.critical(self, "Erreur", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def enregistrer(self):
        '''Enregistre le propriétaire dans la base de données'''

        if self.validation_saisie():
            wnom = self.leNom.text()

            wpro_nom= wnom

            wpro_mail= self.leMail.text()

            wpro_tel= self.leTel.text()

            wadresse = self.leAdresse.text()

            wpro_adresse= wadresse

            querypro = QSqlQuery(self.db)
            wrelation = "proprietaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            querypro.prepare("INSERT INTO " + wrelation + " (pro_nom, pro_telephone, pro_mail, pro_adresse) VALUES (?, ?, ?, ? )")
            querypro.addBindValue(wpro_nom)
            querypro.addBindValue(wpro_tel)
            querypro.addBindValue(wpro_mail)
            querypro.addBindValue(wpro_adresse)

            if not querypro.exec_():
                QMessageBox.critical(self, u"Erreur - Création du propriétaire", querypro.lastError().text(), QMessageBox.Ok)
            else:
                QDialog.accept(self)

    def validation_saisie(self):
        '''Valide la saisie avant enregistrement'''

        if self.leNom.text() == "":
            saisieOk = False
        else:
            saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

class Modification_proprio(QDialog, Ui_dlgBopeModifProprioForm):
    '''
    Class de la fenêtre permettant de modifier les données d'un propriétaire

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeModifProprioForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeModifProprioForm: class
    '''
    def __init__(self, db, dbType, dbSchema,wbope_pro_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des champs

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wbope_pro_id: identifiant du propriétaire issue de la table des droits de pêche (fk)
        :type wbope_pro_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Modification_proprio, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wbope_pro_id = wbope_pro_id
        self.setupUi(self)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.accepted.connect(self.enregistrer)

        query = QSqlQuery(self.db)
        wrelation = "proprietaire"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("SELECT pro_nom, pro_mail, pro_telephone, pro_adresse FROM " + wrelation + " WHERE pro_id = " + str(self.wbope_pro_id))
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur", query.lastError().text(), QMessageBox.Ok)

        if query.exec_():
            if query.next():
                wnom = query.value(0)
                wmail = query.value(1)
                wtelephone = query.value(2)
                wadresse = query.value(3)

                self.leNom.setText(wnom)
                self.leMail.setText(wmail)
                self.leTel.setText(wtelephone)
                self.leAdresse.setText(wadresse)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def enregistrer(self):
        '''Enregistre les modifications apportées au propriétaire dans la base de données'''

        if self.validation_saisie():
            wnom = self.leNom.text()
            if "'" in wnom and "''" not in wnom:
                wnom = wnom.replace("'", "''")

            wpro_nom= wnom

            wpro_mail= self.leMail.text()

            wpro_tel= self.leTel.text()

            wadresse = self.leAdresse.text()
            if "'" in wadresse and "''" not in wadresse:
                wadresse = wadresse.replace("'", "''")
            wpro_adresse= wadresse

            querypro = QSqlQuery(self.db)
            wrelation = "proprietaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            querypro.prepare("UPDATE " + wrelation + " SET pro_nom = '" + wpro_nom + "', pro_telephone = '" + wpro_tel + "', pro_mail = '" + wpro_mail + "', pro_adresse = '" + wpro_adresse +
            "' WHERE pro_id = " + str(self.wbope_pro_id))

            if not querypro.exec_():
                QMessageBox.critical(self, u"Erreur - Modification du propriétaire", querypro.lastError().text(), QMessageBox.Ok)
            else:
                QDialog.accept(self)

    def validation_saisie(self):
        '''Valide la saisie avant enregistrement'''

        saisieOk = True
        # Voir si contrôles de saisie
        return saisieOk

class Bope_recherche_proprio_dialog(QDialog, Ui_dlgBopeRechercheProprioForm):
    '''
    Class de la fenêtre permettant de rechercher un propriétaire

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeRechercheProprioForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeRechercheProprioForm: class
    '''
    def __init__(self, db, dbType, dbSchema, cmbProprio, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param cmbProprio: combobox des propriétaires afin de pouvoir ajouter celui issu de la recherche
        :type cmbProprio: QComboBox

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Bope_recherche_proprio_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.setupUi(self)
        self.btnChercher.clicked.connect(self.recherche)
        self.btnAjouter.clicked.connect(self.ajouter)
        self.btnAnnuler.clicked.connect(self.reject)
        self.btnAjouter.setEnabled(False)
        self.cmbProprio = cmbProprio

    def recherche(self):
        '''Permet de rechercher un propriétaire'''

        # Double les ' afin d'éviter de faire échouer la requête SQL de recherche
        wrecherch = self.leNom.text()
        if "'" in wrecherch and "''" not in wrecherch:
            wrecherch = wrecherch.replace("'", "''")

        # Requête SQL qui va chercher si le propriétaire saisi existe
        if wrecherch != "":
            self.modelCherche = QSqlRelationalTableModel(self, self.db)
            wrelation = "proprietaire"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelCherche.setTable(wrelation)
            self.modelCherche.setSort(1, Qt.AscendingOrder)

            self.modelCherche.setFilter("pro_nom ILIKE '%" + wrecherch + "%'")
            self.modelCherche.select()

            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_nom"), Qt.Horizontal, u"Nom")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_telephone"), Qt.Horizontal, u"Téléphone")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_mail"), Qt.Horizontal, u"Email")
            self.modelCherche.setHeaderData(self.modelCherche.fieldIndex("pro_adresse"), Qt.Horizontal, u"Adresse")

            if (not self.modelCherche.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle recherche dans le Bope_recherche_proprio_dialog.recherche() : \n" + self.modelCherche.lastError().text(), QMessageBox.Ok)

            self.tbvProprio.setModel(self.modelCherche)
            self.tbvProprio.setSelectionMode(QTableView.SingleSelection)
            self.tbvProprio.setSelectionBehavior(QTableView.SelectRows)
            self.tbvProprio.setColumnHidden(self.modelCherche.fieldIndex("pro_id"), True)
            self.tbvProprio.resizeColumnsToContents()
            self.tbvProprio.horizontalHeader().setStretchLastSection(True)
            self.btnAjouter.setEnabled(True)
        else:
            QMessageBox.critical(self, "Erreur", u"Aucun nom saisie ...", QMessageBox.Ok)

    def ajouter(self):
        ''' Permet après recherche de placer le propriétaire sélectionné en haut de la combobox dans le dockwidget'''

        wid = ""
        selection = self.tbvProprio.selectionModel()
        indexElementSelectionne = selection.selectedRows(0)
        wid = indexElementSelectionne[0].data()

        if wid != "":
            result = self.cmbProprio.model().match(self.cmbProprio.model().index(0, 0), Qt.EditRole, wid, -1, Qt.MatchExactly)
            if result:
                self.cmbProprio.setCurrentIndex(result[0].row())
                QDialog.accept(self)
        else :
            QMessageBox.critical(self, "Erreur", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

class Fiche_proprio(QDialog, Ui_dlgBopeProprioForm):
    '''
    Class de la fenêtre affichant les données complètes sur le propriétaire

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeProprioForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeProprioForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wbope_pro_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des champs

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wbope_pro_id: identifiant du propriétaire issue de la table des droits de pêche (fk)
        :type wbope_pro_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Fiche_proprio, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wbope_pro_id = wbope_pro_id
        self.setupUi(self)
        self.btnFermer.clicked.connect(self.reject)

        query = QSqlQuery(self.db)
        wrelation = "proprietaire"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        query.prepare("SELECT pro_nom, pro_mail, pro_telephone, pro_adresse FROM " + wrelation + " WHERE pro_id = " + str(self.wbope_pro_id))
        if not query.exec_():
            QMessageBox.critical(self, u"Erreur", query.lastError().text(), QMessageBox.Ok)

        if query.exec_():
            if query.next():
                wnom = query.value(0)
                if "''" in wnom:
                    wnom = wnom.replace("''", "'")
                wmail = query.value(1)
                wtelephone = query.value(2)
                wadresse = query.value(3)
                if "'" in wadresse and "''" not in wadresse:
                    wadresse = wadresse.replace("'", "''")

                self.leNom.setText(wnom)
                self.leMail.setText(wmail)
                self.leTel.setText(wtelephone)
                self.leAdresse.setText(wadresse)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

class Ajout_parcelle(QDialog, Ui_dlgBopeAjoutParcelleForm):
    '''
    Class de la fenêtre permettant la recherche d'une parcelle et de son ajout au droit de pêche

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeAjoutParcelleForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeAjoutParcelleForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wbope_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wbope_id: identifiant du droit de pêche
        :type wbope_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ajout_parcelle, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wbope_id = wbope_id
        self.setupUi(self)

        self.modelPar = None

        self.btnRechercher.clicked.connect(self.recherche)
        self.btnAjouter.setEnabled(False)
        self.btnAjouter.clicked.connect(self.ajouter)
        self.btnAnnuler.clicked.connect(self.reject)
        self.btnRaz.clicked.connect(self.raz)

        self.btnPrevisualiser.clicked.connect(self.previSql)

        self.btnC.clicked.connect(self.ajoutCommune)
        self.btnCS.clicked.connect(self.ajoutComSection)
        self.btnCSP.clicked.connect(self.ajoutComSecParcelle)

        self.wwhere = ""

        self.modelCommune = QSqlTableModel(self, self.db)
        wrelation = "commune"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelCommune.setTable(wrelation)
        self.modelCommune.setSort(2, Qt.AscendingOrder)
        if (not self.modelCommune.select()):
            QMessageBox.critical(self, u"Remplissage du modèle Commune", self.modelCommune.lastError().text(), QMessageBox.Ok)
        else:
            if self.dbType == "spatialite":
                while self.modelCommune.canFetchMore():
                    self.modelRiviere.fetchMore()
        self.cmbCommune.setModel(self.modelCommune)
        self.cmbCommune.setModelColumn(self.modelCommune.fieldIndex("com_nom"))
        self.cmbCommune.setCurrentIndex(1)

        self.modelSection = QSqlQueryModel(self)
        self.modelParcelle = QSqlQueryModel(self)

        self.cmbSection.setModel(self.modelSection)
        self.cmbSection.setModelColumn(2)

        self.cmbParcelle.setModel(self.modelParcelle)
        self.cmbParcelle.setModelColumn(1)

        self.cmbCommune.currentIndexChanged.connect(self.changeCmbCommune)
        self.cmbSection.currentIndexChanged.connect(self.changeCmbSection)

        self.cmbCommune.setCurrentIndex(0)

    def changeCmbCommune(self, newInd):
        '''
        Filtre la combobox section en fonction de la commune affichée dans celle des communes

        :param newInd: index courant dans la combobox
        :type newInd: int
        '''
        self.modelParcelle.clear()
        self.cmbParcelle.clear()
        self.cmbParcelle.setModel(self.modelParcelle)
        self.cmbParcelle.setModelColumn(1)

        record = self.modelCommune.record(newInd)
        wcom_insee = record.value(self.modelCommune.fieldIndex("com_insee"))

        self.modelSection.clear()
        wrelation = "section"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelSection.setQuery("select sec_id, sec_nom || ' ; ' || sec_com_abs from " + wrelation + " where sec_com_insee = '%s' order by sec_nom;" % str(wcom_insee), self.db)
        if self.modelSection.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle Section", self.modelSection.lastError().text(), QMessageBox.Ok)

        self.cmbSection.setModel(self.modelSection)
        self.cmbSection.setModelColumn(1)

        self.cmbSection.setCurrentIndex(0)

    def changeCmbSection(self, newInd):
        '''
        Filtre la combobox parcelle en fonction de la section affichée dans celle des sections

        :param newInd: index courant dans la combobox
        :type newInd: int
        '''
        record = self.modelSection.record(newInd)
        wsec_id = record.value(0)
        self.cmbParcelle.clear()

        self.modelParcelle.clear()
        wrelation = "parcelle"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelParcelle.setQuery("select par_id, par_numero from " + wrelation + " where par_sec_id = '%s' order by par_numero;" % str(wsec_id), self.db)
        if self.modelParcelle.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle Parcelle", self.modelParcelle.lastError().text(), QMessageBox.Ok)

        self.cmbParcelle.setModel(self.modelParcelle)
        self.cmbParcelle.setModelColumn(1)

    def ajoutCommune(self):
        '''Ajoute un critère de commune à la requête'''

        wrecord = self.cmbCommune.model().record(self.cmbCommune.currentIndex())
        self.wcommune = wrecord.value(0)
        if self.cmbCommune.currentText() != "":
            if self.wcommune != "":
                if self.wwhere == "":
                    self.wwhere += "sec_com_insee = '" + str(self.wcommune) +"'"
                else :
                     self.wwhere += " OR sec_com_insee = '" + str(self.wcommune) +"'"

    def ajoutComSection(self):
        '''Ajoute un critère de commune et section à la requête'''

        wrecord = self.cmbSection.model().record(self.cmbSection.currentIndex())
        self.wsection = wrecord.value(0)
        if self.cmbSection.currentText() != "":
            if self.wsection != "":
                if self.wwhere == "":
                    self.wwhere += "par_sec_id = '" + str(self.wsection) +"'"
                else:
                    self.wwhere += " OR par_sec_id = '" + str(self.wsection) +"'"

    def ajoutComSecParcelle(self):
        '''Ajoute un critère de commune, section et parcelle à la requête'''

        wrecord = self.cmbParcelle.model().record(self.cmbParcelle.currentIndex())
        self.wparcelle = wrecord.value(0)
        if self.cmbParcelle.currentText() != "":
            if self.wparcelle != "":
                if self.wwhere == "":
                    self.wwhere += "par_id = '" + str(self.wparcelle) +"'"
                else:
                    self.wwhere += "OR par_id = '" + str(self.wparcelle) +"'"

    def raz(self):
        '''Réinitialise toutes les variables de la fenêtre afin de recommencer une nouvelle requête'''

        self.wrq = ""
        self.txtSql.setText("")
        self.wwhere = ""
        modelRaz = QSqlQueryModel()
        self.tbvResu.setModel(modelRaz)

        self.btnAjouter.setEnabled(False)

    def creaRequete(self):
        '''Permet de prévisualiser la requête avant de l'éxecuter'''

        self.wrq = ""

        # Construit la clause FROM de la requête
        if self.dbType == "postgres":
            cfrom = self.dbSchema + ".commune, " + self.dbSchema + ".section, " + self.dbSchema + ".parcelle"

        # Construit la clause SELECT et ajoute la clause FROM à la requête
        self.wrq = "SELECT DISTINCT par_id FROM " + cfrom

        # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
        if self.wwhere != "":
            #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
            operateurs = ["and", "or"]
            fin_where = self.wwhere[-5:]
            for ext in operateurs:
                if ext in fin_where:
                    self.wwhere = self.wwhere[:-4]
            self.wrq += " WHERE par_sec_id = sec_id AND sec_com_insee = com_insee AND " + self.wwhere + " ORDER BY par_id"
        else :
            self.wrq = u"Aucun critère défini, veuillez réinitialiser et recommencer"
            self.txtSql.setText(self.wrq)

    def previSql(self):
        '''Permet de prévisualiser la requête avant de l'éxecuter'''
        self.txtSql.setText("")
        self.creaRequete()

        # Affiche la requête
        self.txtSql.setText(self.wrq)

    def recherche (self):
        '''Permet d'éxecuter la requête'''

        # Vérifie la non présence de mot pouvant endommager la base de données
        erreur = False
        interdit = ["update", "delete", "insert", "intersect", "duplicate", "merge", "truncate", "create", "drop", "alter"]
        if self.txtSql.toPlainText() != "":
            self.requete = self.txtSql.toPlainText()
        else:
            self.creaRequete()
            self.requete = self.wrq
        testRequete = self.requete.lower()
        for mot in interdit:
            if mot in testRequete:
                erreur = True
        if erreur == True :
            QMessageBox.critical(self, u"Erreur SQL", u"Vous essayez d'exécuter une requête qui peut endommager la base de données !", QMessageBox.Ok)
        # Après récupération du contenu de la zone de texte, exécute la requête
        else:
            query = QSqlQuery(self.db)
            query.prepare(self.requete)
            if query.exec_():
                wparam = ""
                while query.next():
                    wparam = wparam + "'" + str(query.value(0)) + "' ,"
                if (wparam != ""):
                    wparam = "(" + wparam[0:len(wparam) - 1] + ")"

                    # Création du modèle Parcelle
                    self.modelPar = QSqlRelationalTableModel(self, self.db)

                    wrelation = "parcelle"
                    if self.dbType == "postgres":
                        wrelation = self.dbSchema + "." + wrelation
                    self.modelPar.setTable(wrelation)
                    self.modelPar.setFilter("par_id in %s" %wparam)
                    self.modelPar.setSort(0, Qt.AscendingOrder)

                    # Remplissage du tableau avec le modèle Parcelle
                    self.modelPar.setHeaderData(self.modelPar.fieldIndex("par_id"), Qt.Horizontal, "ID")
                    self.modelPar.setHeaderData(self.modelPar.fieldIndex("par_numero"), Qt.Horizontal, u"Parcelle")

                    if (not self.modelPar.select()):
                        QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Parcelle dans le ajoutParcelle.recherche() : \n" + self.modelPar.lastError().text(), QMessageBox.Ok)

                    self.modelPar.setEditStrategy(QSqlTableModel.OnManualSubmit)

                    self.tbvResu.setModel(self.modelPar)
                    self.tbvResu.setSelectionMode(QTableView.MultiSelection)
                    self.tbvResu.setSelectionBehavior(QTableView.SelectRows)
                    self.tbvResu.setColumnHidden(self.modelPar.fieldIndex("par_sec_id"), True)
                    self.tbvResu.setColumnHidden(self.modelPar.fieldIndex("par_geom"), True)
                    self.tbvResu.setColumnHidden(self.modelPar.fieldIndex("par_bope_id"), True)
                    self.tbvResu.resizeColumnsToContents()
                    self.tbvResu.horizontalHeader().setResizeMode(QHeaderView.Stretch)
                    self.tbvResu.horizontalHeader().setStretchLastSection(True)
                    self.tbvResu.horizontalHeader().moveSection(3, 0) # Place la 3émé colonne de PostgreSQL en position 0
                    self.tbvResu.setColumnWidth(0, 20)
                    self.btnAjouter.setEnabled(True)
                else :
                    QMessageBox.information(self, "Filtrage", u"Aucune parcelle ne correspond aux critères ...", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)

    def ajouter (self):
        ''' Permet après recherche d'ajouter dans la base de données le lien entre la parcelle et le droit de pêche'''

        selection = self.tbvResu.selectionModel()
        indexElementSelectionne = selection.selectedRows(3) # 3 pour récupérer l'id de la parcelle situé en colonne 3 dans PostgreSQL
        nbreSelect = len(indexElementSelectionne)
        nbreSelectMax = len(indexElementSelectionne)
        wid = ""

        if nbreSelect != 0:
            while nbreSelect > 0:
                    if nbreSelectMax == nbreSelect:
                        wid = "'" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    else :
                        wid = wid + ", '" + str(indexElementSelectionne[nbreSelect - 1].data()) + "'"
                    nbreSelect -= 1
            if wid != "":

                queryVerif = QSqlQuery(self.db)
                wrelation = "parcelle"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                queryVerif.prepare("select par_id, par_bope_id from data.parcelle where par_id in (" + wid + ") and par_bope_id is not null")
                if queryVerif.exec_():
                    wpar_id = ""
                    wbope_id = ""
                    message = ""
                    size = queryVerif.size()
                    while size > 0:
                        if queryVerif.next():
                            wpar_id = queryVerif.value(0)
                            wbope_id = queryVerif.value(1)
                            message = message + "La parcelle " + wpar_id + u", est utilisée par le droit de pêche " + str(wbope_id) + ". \n"
                            size -= 1

                    if message != "":
                        QMessageBox.critical(self, u"Erreur : ", u"\n Des parcelles sont déjà liées à un droit de pêche : \n" + message , QMessageBox.Ok)
                    else:
                        query = QSqlQuery(self.db)
                        wrelation = "parcelle"
                        if self.dbType == "postgres":
                            wrelation = self.dbSchema + "." + wrelation
                        query.prepare("UPDATE " + wrelation + " SET par_bope_id = " + str(self.wbope_id) + " WHERE par_id in (" + wid + ")")
                        if not query.exec_():
                            QMessageBox.critical(self, u"Erreur - Ajout d'une parcelle : ", query.lastError().text(), QMessageBox.Ok)
                        else:
                            QDialog.accept(self)
        else :
            QMessageBox.critical(self, "Erreur : ", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

class Ajout_riviere(QDialog, Ui_dlgBopeAjoutRiviereForm):
    '''
    Class de la fenêtre permettant la recherche d'une rivière et de son ajout au droit de pêche

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeAjoutRiviereForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeAjoutRiviereForm: class
    '''
    def __init__(self, db, dbType, dbSchema, wbope_id, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param wbope_id: identifiant du droit de pêche
        :type wbope_id: int

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Ajout_riviere, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.wbope_id = wbope_id
        self.setupUi(self)

        self.modelRiv = None

        self.btnChercher.clicked.connect(self.recherche)
        self.btnAjouter.setEnabled(False)
        self.btnAjouter.clicked.connect(self.ajouter)
        self.btnAnnuler.clicked.connect(self.reject)

    def recherche(self):
        '''Permet de rechercher une rivière pour la lier au droit de pêche'''

        # Double les ' afin d'éviter de faire échouer la requête SQL de recherche
        nom = self.leNom.text()
        if "'" in nom and "''" not in nom:
            nom = nom.replace("'", "''")

        # Requête SQL qui va chercher si le propriétaire saisi existe
        if nom != "":
            self.modelRiv = QSqlRelationalTableModel(self, self.db)
            wrelation = "cours_eau"
            if self.dbType == "postgres":
                wrelation = self.dbSchema + "." + wrelation
            self.modelRiv.setTable(wrelation)
            self.modelRiv.setSort(2, Qt.AscendingOrder)
            self.modelRiv.setFilter("ceau_nom ILIKE '%" + nom + "%'")
            self.modelRiv.select()
            self.modelRiv.setHeaderData(self.modelRiv.fieldIndex("ceau_code_hydro"), Qt.Horizontal, "Code hydro")
            self.modelRiv.setHeaderData(self.modelRiv.fieldIndex("ceau_nom"), Qt.Horizontal, "Nom")

            if (not self.modelRiv.select()):
                QMessageBox.critical(self, u"Remplissage du modèle", u"Erreur au modèle Cherche dans le Ajout_riviere.recherche() : \n" + self.modelRiv.lastError().text(), QMessageBox.Ok)

            self.tbvResu.setModel(self.modelRiv)
            self.tbvResu.setSelectionMode(QTableView.SingleSelection)
            self.tbvResu.setSelectionBehavior(QTableView.SelectRows)
            self.tbvResu.setColumnHidden(self.modelRiv.fieldIndex("ceau_id"), True)
            self.tbvResu.setColumnHidden(self.modelRiv.fieldIndex("ceau_geom"), True)
            self.tbvResu.setColumnHidden(self.modelRiv.fieldIndex("ceau_longueur"), True)
            self.tbvResu.setColumnHidden(self.modelRiv.fieldIndex("ceau_affluent"), True)
            self.tbvResu.resizeColumnsToContents()
            self.tbvResu.horizontalHeader().setStretchLastSection(True)
            self.btnAjouter.setEnabled(True)
        else:
            QMessageBox.critical(self, "Erreur", u"Aucun nom de rivière saisie ...", QMessageBox.Ok)

    def ajouter(self):
        ''' Permet après recherche d'ajouter dans la base de données le lien entre la rivière et le droit de pêche'''

        wid = ""
        try:
            selection = self.tbvResu.selectionModel()
            indexElementSelectionne = selection.selectedRows(0)
            wid = indexElementSelectionne[0].data()

            if wid != "":
                query = QSqlQuery(self.db)

                wrelation = "bail_cours_eau"
                if self.dbType == "postgres":
                    wrelation = self.dbSchema + "." + wrelation
                query.prepare("INSERT INTO " + wrelation + " (bce_bope_id, bce_ceau_id) VALUES (?, ?)")
                query.addBindValue(self.wbope_id)
                query.addBindValue(wid)
                if not query.exec_():
                    QMessageBox.critical(self, u"Erreur - Ajout du cours d'eau", query.lastError().text(), QMessageBox.Ok)
                else:
                    QDialog.accept(self)
        except:
            QMessageBox.critical(self, "Erreur", u"Pas d'élément sélectionné ...", QMessageBox.Ok)

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)
