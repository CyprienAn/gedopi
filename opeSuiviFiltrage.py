# -*- coding: utf-8 -*-
# Ce script permet la création d'une requête SQL afin de filtrer le formulaire "Suivis thermiques" du plugin.

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
from opeSuiviRechercheForm import (Ui_dlgSuiviRechercheForm)

class Filtrage_thermi_dialog(QDialog, Ui_dlgSuiviRechercheForm):
    '''
    Class de la fenêtre permettant le filtrage attributaire des inventaires de reproduction

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgSuiviRechercheForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgSuiviRechercheForm: class
    '''
    def __init__(self, db, dbType, dbSchema, modelThermi, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param modelThermi: modèle thermi qui contient les données de la base de données
        :type modelThermi: QSqlRelationalTableModel

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Filtrage_thermi_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.modelThermi = modelThermi
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
        self.btnDebut.clicked.connect(self.ajoutDateDebut)
        self.btnFin.clicked.connect(self.ajoutDateFin)
        self.btnRiviere.clicked.connect(self.ajoutRiviere)
        self.btnAappma.clicked.connect(self.ajoutAappma)
        self.btnMeau.clicked.connect(self.ajoutMeau)

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.aappmaBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeDebutBool = False
        self.anneeFinBool = False

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

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

    def raz(self):
        '''Réinitialise toutes les variables de la fenêtre afin de recommencer une nouvelle requête'''

        self.spnId.setValue(0)
        self.wrq = ""
        self.txtSql.setText("")
        self.wwhere = ""
        self.dateDebut.setDate(QDate(2000,1,1))
        self.dateFin.setDate(QDate(2000,1,1))

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)
        self.btnPdpg.setEnabled(True)
        self.btnDebut.setEnabled(True)
        self.btnFin.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)

        self.aappmaBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeDebutBool = False
        self.anneeFinBool = False

    def et(self):
        '''Change l'état des boutons et ajoute "and" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)

        if self.aappmaBool == False:
            self.btnAappma.setEnabled(True)

        if self.pdpgBool == False:
            self.btnPdpg.setEnabled(True)

        if self.ceauBool == False:
            self.btnRiviere.setEnabled(True)

        if self.meauBool == False:
            self.btnMeau.setEnabled(True)

        if self.anneeDebutBool == False:
            self.btnDebut.setEnabled(True)

        if self.anneeFinBool == False:
            self.btnFin.setEnabled(True)

        self.wwhere += " AND "

    def ou(self):
        '''Change l'état des boutons et ajoute "or" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnCode.setEnabled(True)
        self.btnId.setEnabled(True)
        self.btnPdpg.setEnabled(True)
        self.btnDebut.setEnabled(True)
        self.btnFin.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)
        self.btnMeau.setEnabled(True)

        self.aappmaBool = False
        self.pdpgBool = False
        self.ceauBool = False
        self.meauBool = False
        self.anneeDebutBool = False
        self.anneeFinBool = False

        self.wwhere += " OR "

    def ajoutCode(self):
        '''Change l'état des boutons et ajoute un critère de code opération à la requête'''

        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

        self.wcode = self.leCodeOpe.text()
        if self.leCodeOpe.text() != "":
            if self.wcode != "":
                self.wwhere += "opest_ope_code ilike '%" + self.wcode + "%'"
        self.leCodeOpe.setText("")
        self.leCodeOpe.setFocus()

    def ajoutId(self):
        '''Change l'état des boutons et ajoute un critère d'id à la requête'''

        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

        self.wid = self.spnId.value()
        if self.spnId.value() != "":
            if self.wid != "":
                self.wwhere += "opest_id = '" + str(self.wid) +"'"
        self.spnId.setValue(0)
        self.spnId.setFocus()

    def ajoutDateDebut(self):
        '''Change l'état des boutons et ajoute un critère de date de début à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

        self.anneeDebutBool = True

        self.wopest_date_debut = self.dateDebut.date().toString("yyyy")
        if self.wopest_date_debut != "":
            self.wwhere += "date_part('year', opest_date_debut) = '" + str(self.wopest_date_debut) + "'"

    def ajoutDateFin(self):
        '''Change l'état des boutons et ajoute un critère de date de fin à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

        self.anneeFinBool = True

        self.wopest_date_fin = self.dateFin.date().toString("yyyy")
        if self.wopest_date_fin != "":
            self.wwhere += "date_part('year', opest_date_fin) = '" + str(self.wopest_date_fin) + "'"

    def ajoutPdpg(self):
        '''Change l'état des boutons et ajoute un critère de pdpg à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

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
                self.wwhere += " opest_id in (select distinct opest_id from " + self.wfromPdpg + " where (opest_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_pdpg_id = '" + str(self.wsta_pdpg) + "')"

    def ajoutRiviere(self):
        '''Change l'état des boutons et ajoute un critère de cours d'eau à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

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
                self.wwhere += " opest_id in (select distinct opest_id from " + self.wfromCeau + " where (opest_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_ceau_id = '" + str(self.wsta_riviere) + "')"

    def ajoutAappma(self):
        '''Change l'état des boutons et ajoute un critère d'AAPPMA à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

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
                self.wwhere += " opest_id in (select distinct opest_id from " + self.wfromAappma + " where (opest_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_apma_id = '" + str(self.wsta_aappma) + "')"

    def ajoutMeau(self):
        '''Change l'état des boutons et ajoute un critère de Masse d'eau à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnCode.setEnabled(False)
        self.btnId.setEnabled(False)
        self.btnPdpg.setEnabled(False)
        self.btnDebut.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnMeau.setEnabled(False)

        self.meauBool = True

        wfromOperation = "operation"
        wfromStation = "station"
        wfromThermi = "ope_suivi_thermi"
        if self.dbType == "postgres":
            self.wfromMeau = self.dbSchema + "." + wfromThermi + ", " + self.dbSchema + "." + wfromOperation + ", " + self.dbSchema + "." + wfromStation

        wrecord = self.cmbMeau.model().record(self.cmbMeau.currentIndex())
        self.wsta_meau = wrecord.value(0)
        if self.cmbMeau.currentText() != "":
            if self.wsta_meau != "":
                self.wwhere += " opep_id in (select distinct opep_id from " + self.wfromMeau + " where (opest_ope_code = ope_code) and (ope_sta_id = sta_id) and sta_meau_code = '" + str(self.wsta_meau) + "')"

    def creaRequete(self):
    # def previSql(self):
        '''Regroupe les différentes variables contenant les clauses de la requête SQL et les concatène pour en faire une requête exécutable'''

        self.wrq = ""

        # Construit la clause FROM de la requête
        cfrom = "ope_suivi_thermi"
        if self.dbType == "postgres":
            cfrom = self.dbSchema + "." + cfrom

        # Construit la clause SELECT et ajoute la clause FROM à la requête
        self.wrq = "SELECT DISTINCT opest_id FROM " + cfrom

        # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
        if self.wwhere != "":
            #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
            operateurs = ["AND", "OR"]
            fin_where = self.wwhere[-5:]
            for ext in operateurs:
                if ext in fin_where:
                    self.wwhere = self.wwhere[:-4]
            self.wrq += " WHERE " + self.wwhere + " ORDER BY opest_id"
        else :
            self.wrq += " ORDER BY opest_id"

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
                    if self.modelThermi:
                        # Filtre le modèle des suivis thermiques et ferme la fenêtre
                        self.modelThermi.setFilter("opest_id in %s" % wparam)
                        self.modelThermi.select()
                        QDialog.accept(self)
                else :
                    QMessageBox.information(self, "Filtrage", u"Aucun suivi thermique ne correspond aux critères ...", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)
