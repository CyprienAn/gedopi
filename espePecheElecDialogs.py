# -*- coding: utf-8 -*-
# Ce script permet le fonctionnement du dialog "Export pêche électrique" du plugin.

# Import des modules Python et PyQt5 nécessaire à l'exécution de ce fichier
import sys
import os

#from PyQt5.QtGui import ()
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QMessageBox)
from PyQt5.QtCore import (Qt, QFileInfo)
from PyQt5.QtSql import (QSqlDatabase, QSqlQuery, QSqlTableModel)
from qgis.gui import (QgsMessageBar)


# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import des scripts Python des interfaces graphiques nécessaire au Dialog
from espePecheElecForm import (Ui_espePecheElecForm)

# Import de la Class Gedopi_common qui permet la connexion du formulaire avec PostgreSQL
from .commonDialogs import (Gedopi_common)

class EspePecheElec_dialog(QDialog, Ui_espePecheElecForm):
    '''Gére le fonctionnement interne du Dialog "Export pêche électrique" après son ouverture via le menu'''

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

        # Méthodes communes
        self.gc = Gedopi_common(self)

        # Variables de connexion à la base de données
        self.db = None
        self.dbType = ""
        self.dbSchema = ""

        self.btnAnnuler.clicked.connect(self.onReject)
        self.btnEnregistrer.clicked.connect(self.enregistrer)

        # Initialisation du formulaire
        if self.verifiePresenceCouche():
            self.setupModel()
        else:
            self.iface.messageBar().pushMessage("Erreur : ", u"La couche des opérations de pêches électriques n'est pas chargée ...", level= QgsMessageBar.CRITICAL, duration = 5)
            self.btnEnregistrer.setEnabled(False)
            self.cmbEspece.setEnabled(False)

    def verifiePresenceCouche(self):
        '''
        Vérifie la présence de différentes couches et renvoi dans __init__, True ou False,
        active le setupModel si return True,
        affiche un message si return False
        '''
        self.layer = None
        self.layer = self.gc.getLayerFromLegendByTableProps('ope_peche_elec', 'opep_geom', '')
        if self.layer:
            return True
        else:
            return False

    def setupModel(self):
        '''
        Initialise le formulaire en le connectant à la base de données
        et en attribuant aux différents champs leurs tables ou colonnes PostgreSQL
        '''
        self.infoMessage = u"Gedopi - Pêche électrique"
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
                self.host = connectionParams['host']
                self.user = connectionParams['user']
                self.password = connectionParams['password']
                self.dbname = connectionParams['dbname']

            if (not self.db.open()):
                QMessageBox.critical(self, "Erreur", u"Impossible de se connecter à la base de données ...", QMessageBox.Ok)
                QApplication.restoreOverrideCursor()
                return

        # Remplissage de la liste déroulante des espèces
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

    def enregistrer(self):
        requete = ""
        savefile = ""
        self.cheminExport= ""

        # Récupération de l'ID et du sigle de l'espèce en cours dans la combobox
        wrecord = self.cmbEspece.model().record(self.cmbEspece.currentIndex())
        wespeceId = wrecord.value(0)
        wespeceSigle = wrecord.value(1)

        # Écriture de la requête SQL en fonction de l'espèce choisi dans la liste déroulante
        requete = ("SELECT DISTINCT operation.ope_code AS CODE, " +
        "station.sta_xl93_aval AS X, " +
        "station.sta_yl93_aval AS Y, " +
        "cours_eau.ceau_nom AS RIVIERE, " +
        "(masse_eau.meau_code || ' ; '::text) || masse_eau.meau_nom AS MASSEEAU, " +
        "contexte_pdpg.pdpg_nom AS PDPG, " +
        "ope_peche_elec.opep_date AS DATE, " +
        "motif_peche.mope_motif AS MOTIF, " +
        "condition_peche.cope_condition AS CONDITION, " +
        "ope_peche_elec.opep_nbre_anode AS NANODE, " +
        "ope_peche_elec.opep_longueur_prospec AS LONGUEUR, " +
        "ope_peche_elec.opep_profondeur_moy AS PROFONDEUR, " +
        "ope_peche_elec.opep_largeur_moy AS LARGEUR, " +
        "ope_peche_elec.opep_surf_peche AS SURFACE, " +
        "ope_peche_elec.opep_pente AS PENTE, " +
        "ope_peche_elec.opep_ntt_reel AS NTTREEL, " +
        "ope_peche_elec.opep_ntt AS NTT, " +
        "(ope_peche_elec.ipro_valeur || ' ; '::text) || ipr.ipr_correspondance AS IPR, " +
        "string_agg(espece.esp_sigle, ' ; '::text) AS ESPECE, " +
        "f_poisson_params.espe_densite AS VALDEN_"+ wespeceSigle + ", " +
        "f_poisson_params.clde_val_correspond AS CLADEN_"+ wespeceSigle + ", " +
        "f_poisson_params.espe_biomasse AS VALBIO_"+ wespeceSigle + ", " +
        "f_poisson_params.clbi_val_correspond CLABIO_"+ wespeceSigle + ", " +
        "ope_peche_elec.opep_geom " +
        "FROM data.masse_eau, " +
        "data.cours_eau, " +
        "data.station, " +
        "data.contexte_pdpg, " +
        "data.operation, " +
        "data.ope_peche_elec " +
        "JOIN data.motif_peche ON motif_peche.mope_id = ope_peche_elec.opep_mope_id " +
        "JOIN data.condition_peche ON condition_peche.cope_id = ope_peche_elec.opep_cope_id " +
        "JOIN data.ipr ON ipr.ipr_id = ope_peche_elec.opep_ipr_id " +
        "JOIN data.espece_peche ON espece_peche.espe_opep_id = ope_peche_elec.opep_id " +
        "JOIN data.espece ON espece_peche.espe_esp_id = espece.esp_id " +
        "FULL JOIN data.f_poisson_params(" + str(wespeceId) + ") f_poisson_params(ope_code, espe_biomasse, clbi_val_correspond, espe_densite, clde_val_correspond) ON f_poisson_params.ope_code = ope_peche_elec.opep_ope_code " +
        "WHERE station.sta_meau_code = masse_eau.meau_code AND " +
        "station.sta_ceau_id = cours_eau.ceau_id AND " +
        "station.sta_pdpg_id = contexte_pdpg.pdpg_id AND " +
        "operation.ope_sta_id = station.sta_id AND " +
        "operation.ope_code = ope_peche_elec.opep_ope_code " +
        "GROUP BY operation.ope_code, station.sta_xl93_aval, station.sta_yl93_aval, cours_eau.ceau_nom, ((masse_eau.meau_code || ' ; '::text) || masse_eau.meau_nom), contexte_pdpg.pdpg_nom, ope_peche_elec.opep_date, motif_peche.mope_motif, condition_peche.cope_condition, ope_peche_elec.opep_nbre_anode, ope_peche_elec.opep_longueur_prospec, ope_peche_elec.opep_profondeur_moy, ope_peche_elec.opep_largeur_moy, ope_peche_elec.opep_surf_peche, ope_peche_elec.opep_pente, ope_peche_elec.opep_ntt_reel, ope_peche_elec.opep_ntt, ((ope_peche_elec.ipro_valeur || ' ; '::text) || ipr.ipr_correspondance), f_poisson_params.espe_densite, f_poisson_params.clde_val_correspond, f_poisson_params.espe_biomasse, f_poisson_params.clbi_val_correspond, ope_peche_elec.opep_geom " +
        "ORDER BY cours_eau.ceau_nom ")

        # Récupération du chemin où enregistrer l'export
        savefile = QFileDialog.getSaveFileName(self, "Save File", "", u"ESRI Shapefile (*.shp)")
        if savefile != "":
            cheminExport = unicode(savefile)
            # Récupération du nom du fichier
            path = QFileInfo(cheminExport)
            filename = path.completeBaseName()
        if cheminExport != "":
            query = QSqlQuery(self.db)
            query.prepare(requete)
            # Exécution de la requête afin de vérifier sa validité
            if query.exec_():
                # Création d'une ligne de commande DOS qui utilisera pgsql2shp pour créer un shapefile en fonction de la requête
                cmd = "cd C:\\Program Files\\PostgreSQL\\9.5\\bin & pgsql2shp.exe -f " + str(cheminExport) + " -h " + self.host + " -u " + self.user + " -P " + self.password + " " + self.dbname + " \"" + requete + "\""
                # Exécution de la ligne de commande (une fenêtre DOS s'ouvre le temps de l'exécution
                os.system(cmd)
                self.onReject()
                # Ajout du shape créé au caneva
                layer = self.iface.addVectorLayer(cheminExport, filename , "ogr")
            else:
                QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)

    def onReject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)
