# -*- coding: utf-8 -*-
# Ce script permet la création d'une requête SQL afin de filtrer le formulaire "Pêches électriques" du plugin.

# Import des modules Python et PyQt5 nécessaire à l'exécution de ce fichier
import sys
import os
from PyQt5.QtCore import (Qt, QDate)
from PyQt5.QtWidgets import (QDialog, QMessageBox)
from PyQt5.QtSql import (QSqlQuery, QSqlTableModel, QSqlQueryModel)

# Initialise les ressources Qt à partir du fichier resources.py
# import resources_rc

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import du script Python de l'interface graphique nécessaire
from opePecheRechercheForm import (Ui_dlgPecheRechercheForm)

class Filtrage_peche_dialog(QDialog, Ui_dlgPecheRechercheForm):
    '''
    Class de la fenêtre permettant le filtrage attributaire des inventaires de reproduction

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgPecheRechercheForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgPecheRechercheForm: class
    '''
    def __init__(self, db, dbType, dbSchema, modelPeche, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param modelPeche: modèle pêche qui contient les données de la base de données
        :type modelPeche: QSqlRelationalTableModel

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Filtrage_peche_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.modelPeche = modelPeche
        self.setupUi(self)

        self.btnAnnuler.clicked.connect(self.reject)
        self.btnExec.clicked.connect(self.execution)
        self.btnRaz.clicked.connect(self.raz)
        self.btnEt.clicked.connect(self.et)
        self.btnOu.clicked.connect(self.ou)

        self.btnPrevisualiser.clicked.connect(self.previSql)

        self.btnCode.clicked.connect(self.ajoutCode)
        self.btnId.clicked.connect(self.ajoutId)
        self.btnPdpg.clicked.connect(self.ajoutPdpg)
        self.btnDate.clicked.connect(self.ajoutDate)
        self.btnRiviere.clicked.connect(self.ajoutRiviere)
        self.btnAappma.clicked.connect(self.ajoutAappma)
        self.btnMeau.clicked.connect(self.ajoutMeau)
        self.btnMotif.clicked.connect(self.ajoutMotif)

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.aappmaBool = False
        self.motifBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False

        self.wwhere = ""

        self.modelPdpg = QSqlTableModel(self, self.db)
        wrelation = "contexte_pdpg"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelPdpg.setTable(wrelation)
        self.modelPdpg.setSort(2, Qt.AscendingOrder)
        if (not self.modelPdpg.select()):
            QMessageBox.critical(self, u"Remplissage du modèle PDPG", self.modelPdpg.lastError().text(), QMessageBox.Ok)
        self.cmbPdpg.setModel(self.modelPdpg)
        self.cmbPdpg.setModelColumn(self.modelPdpg.fieldIndex("pdpg_nom"))

        self.modelAappma = QSqlTableModel(self, self.db)
        wrelation = "aappma"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelAappma.setTable(wrelation)
        self.modelAappma.setSort(1, Qt.AscendingOrder)
        if (not self.modelAappma.select()):
            QMessageBox.critical(self, u"Remplissage du modèle AAPPMA", self.modelAappma.lastError().text(), QMessageBox.Ok)
        self.cmbAappma.setModel(self.modelAappma)
        self.cmbAappma.setModelColumn(self.modelAappma.fieldIndex("apma_nom"))

        self.modelRiviere = QSqlTableModel(self, self.db)
        wrelation = "cours_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelRiviere.setTable(wrelation)
        self.modelRiviere.setFilter("ceau_nom <> 'NR'")
        self.modelRiviere.setSort(2, Qt.AscendingOrder)
        if (not self.modelRiviere.select()):
            QMessageBox.critical(self, u"Remplissage du modèle Rivière", self.modelRiviere.lastError().text(), QMessageBox.Ok)
        self.cmbRiviere.setModel(self.modelRiviere)
        self.cmbRiviere.setModelColumn(self.modelRiviere.fieldIndex("ceau_nom"))

        self.modelMeau = QSqlQueryModel(self)
        wrelation = "masse_eau"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelMeau.setQuery("select meau_code, meau_code || ' ; ' || meau_nom from " + wrelation + " order by meau_code;", self.db)
        if self.modelMeau.lastError().isValid():
            QMessageBox.critical(self, u"Remplissage du modèle Masse d'eau", self.modelMeau.lastError().text(), QMessageBox.Ok)
        self.cmbMeau.setModel(self.modelMeau)
        self.cmbMeau.setModelColumn(1)

        self.ModelMotif= QSqlTableModel(self, self.db)
        wrelation = "motif_peche"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.ModelMotif.setTable(wrelation)
        self.ModelMotif.setSort(1, Qt.AscendingOrder)
        if (not self.ModelMotif.select()):
            QMessageBox.critical(self, u"Remplissage du modèle Motif", self.ModelMotif.lastError().text(), QMessageBox.Ok)
        self.cmbMotif.setModel(self.ModelMotif)
        self.cmbMotif.setModelColumn(self.ModelMotif.fieldIndex("mope_motif"))

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def raz(self):
        '''Réinitialise toutes les variables de la fenêtre afin de recommencer une nouvelle requête'''

        self.spnId.setValue(0)
        self.wrq = ""
        self.txtSql.setText("")
        self.wwhere = ""
        self.datePeche.setDate(QDate(2000,1,1))

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)
        self.btnPdpg.setEnabled(True)
        self.btnDate.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)
        self.btnMeau.setEnabled(True)
        self.btnMotif.setEnabled(True)

        self.aappmaBool = False
        self.motifBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False

    def et(self):
        '''Change l'état des boutons et ajoute "and" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)

        if self.aappmaBool == False:
            self.btnAappma.setEnabled(True)

        if self.motifBool == False:
            self.btnMotif.setEnabled(True)

        if self.pdpgBool == False:
            self.btnPdpg.setEnabled(True)

        if self.ceauBool == False:
            self.btnRiviere.setEnabled(True)

        if self.meauBool == False:
            self.btnMeau.setEnabled(True)

        if self.anneeBool == False:
            self.btnDate.setEnabled(True)

        self.wwhere += " AND "

    def ou(self):
        '''Change l'état des boutons et ajoute "or" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)
        self.btnPdpg.setEnabled(True)
        self.btnDate.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)
        self.btnMeau.setEnabled(True)
        self.btnMotif.setEnabled(True)

        self.aappmaBool = False
        self.motifBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeBool = False

        self.wwhere += " OR "

    def ajoutCode(self):
        '''Change l'état des boutons et ajoute un critère de code opération à la requête'''

        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.wcode = self.leCodeOpe.text()
        if self.leCodeOpe.text() != "":
            if self.wcode != "":
                self.wwhere += "opep_ope_code ilike '%" + self.wcode + "%'"
        self.leCodeOpe.setText("")
        self.leCodeOpe.setFocus()

    def ajoutId(self):
        '''Change l'état des boutons et ajoute un critère d'id à la requête'''

        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.wid = self.spnId.value()
        if self.spnId.value() != "":
            if self.wid != "":
                self.wwhere += "opep_id = '" + str(self.wid) +"'"
        self.spnId.setValue(0)
        self.spnId.setFocus()

    def ajoutDate(self):
        '''Change l'état des boutons et ajoute un critère de date à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.anneeBool = True

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.wopep_date = self.datePeche.date().toString("yyyy")
        if self.wopep_date != "":
            self.wwhere += "date_part('year', opep_date) = '" + self.wopep_date + "'"

    def ajoutPdpg(self):
        '''Change l'état des boutons et ajoute un critère de pdpg à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.pdpgBool = True

        wfromOperation = "operation"
        wfromStation = "station"
        wfromPeche = "ope_peche_elec"
        if self.dbType == "postgres":
            self.wfromPdpg = self.dbSchema + "." + wfromPeche + ", " + self.dbSchema + "." + wfromOperation + ", " + self.dbSchema + "." + wfromStation

        wrecord = self.cmbPdpg.model().record(self.cmbPdpg.currentIndex())
        self.wsta_pdpg = wrecord.value(0)
        if self.cmbPdpg.currentText() != "":
            if self.wsta_pdpg != "":
                self.wwhere += " opep_id in (select distinct opep_id from " + self.wfromPdpg + " where (opep_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_pdpg_id = '" + str(self.wsta_pdpg) + "')"

    def ajoutRiviere(self):
        '''Change l'état des boutons et ajoute un critère de cours d'eau à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.ceauBool = True

        wfromOperation = "operation"
        wfromStation = "station"
        wfromPeche = "ope_peche_elec"
        if self.dbType == "postgres":
            self.wfromCeau = self.dbSchema + "." + wfromPeche + ", " + self.dbSchema + "." + wfromOperation + ", " + self.dbSchema + "." + wfromStation

        wrecord = self.cmbRiviere.model().record(self.cmbRiviere.currentIndex())
        self.wsta_riviere = wrecord.value(0)
        if self.cmbRiviere.currentText() != "":
            if self.wsta_riviere != "":
                self.wwhere += " opep_id in (select distinct opep_id from " + self.wfromCeau + " where (opep_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_ceau_id = '" + str(self.wsta_riviere) + "')"

    def ajoutAappma(self):
        '''Change l'état des boutons et ajoute un critère d'AAPPMA à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.aappmaBool = True

        wfromOperation = "operation"
        wfromStation = "station"
        wfromPeche = "ope_peche_elec"
        if self.dbType == "postgres":
            self.wfromAappma = self.dbSchema + "." + wfromPeche + ", " + self.dbSchema + "." + wfromOperation + ", " + self.dbSchema + "." + wfromStation

        wrecord = self.cmbAappma.model().record(self.cmbAappma.currentIndex())
        self.wsta_aappma = wrecord.value(0)
        if self.cmbAappma.currentText() != "":
            if self.wsta_aappma != "":
                self.wwhere += " opep_id in (select distinct opep_id from " + self.wfromAappma + " where (opep_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_apma_id = '" + str(self.wsta_aappma) + "')"

    def ajoutMeau(self):
        '''Change l'état des boutons et ajoute un critère de Masse d'eau à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.meauBool = True

        wfromOperation = "operation"
        wfromStation = "station"
        wfromPeche = "ope_peche_elec"
        if self.dbType == "postgres":
            self.wfromMeau = self.dbSchema + "." + wfromPeche + ", " + self.dbSchema + "." + wfromOperation + ", " + self.dbSchema + "." + wfromStation

        wrecord = self.cmbMeau.model().record(self.cmbMeau.currentIndex())
        self.wsta_meau = wrecord.value(0)
        if self.cmbMeau.currentText() != "":
            if self.wsta_meau != "":
                self.wwhere += " opep_id in (select distinct opep_id from " + self.wfromMeau + " where (opep_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_meau_code = '" + str(self.wsta_meau) + "')"

    def ajoutMotif(self):
        '''Change l'état des boutons et ajoute un critère de motif de pêche à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDate.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)
        self.btnMotif.setEnabled(False)

        self.motifBool = True

        wrecord = self.cmbMotif.model().record(self.cmbMotif.currentIndex())
        self.wopep_motif = wrecord.value(0)
        if self.cmbMotif.currentText() != "":
            if self.wopep_motif != "":
                self.wwhere += "opep_mope_id = '" + str(self.wopep_motif) + "'"

    def creaRequete(self):
    # def previSql(self):
        '''Regroupe les différentes variables contenant les clauses de la requête SQL et les concatène pour en faire une requête exécutable'''

        self.wrq = ""

        # Construit la clause FROM de la requête
        cfrom = "ope_peche_elec"
        if self.dbType == "postgres":
            cfrom = self.dbSchema + "." + cfrom

        # Construit la clause SELECT et ajoute la clause FROM à la requête
        self.wrq = "SELECT DISTINCT opep_id FROM " + cfrom

        # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
        if self.wwhere != "":
            #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
            operateurs = ["AND", "OR"]
            fin_where = self.wwhere[-5:]
            for ext in operateurs:
                if ext in fin_where:
                    self.wwhere = self.wwhere[:-4]
            self.wrq += " WHERE " + self.wwhere + " ORDER BY opep_id"
        else :
            self.wrq += " ORDER BY opep_id"

    def previSql(self):
        '''Permet de prévisualiser la requête avant de l'éxecuter'''
        self.txtSql.setText("")
        self.creaRequete()

        # Affiche la requête
        self.txtSql.setText(self.wrq)

    def execution(self):
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
                    wparam += str(query.value(0)) + ","
                if (wparam != ""):
                    wparam = "(" + wparam[0:len(wparam) - 1] + ")"
                    if self.modelPeche:
                        # Filtre le modèle des inventaires de reproduction et ferme la fenêtre
                        self.modelPeche.setFilter("opep_id in %s" % wparam)
                        self.modelPeche.select()
                        QDialog.accept(self)
                else :
                    QMessageBox.information(self, "Filtrage", u"Aucun pêche électrique ne correspond aux critères ...", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)
