# -*- coding: utf-8 -*-
# Ce script permet la création d'une requête SQL afin de filtrer le formulaire "Droits de pêche" du plugin.

# Import des modules Python et PyQt5 nécessaire à l'exécution de ce fichier
import sys
import os
from PyQt5.QtCore import (Qt, QDate)
from PyQt5.QtWidgets import (QDialog, QMessageBox)
from PyQt5.QtSql import (QSqlQuery, QSqlQueryModel, QSqlTableModel)

# Initialise les ressources Qt à partir du fichier resources.py
# import resources_rc

# Ajout du chemin vers le répertoire contenant les interfaces graphiques
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")

# Import du script Python de l'interface graphique nécessaire
from bopeRechercheForm import (Ui_dlgBopeRechercheForm)

class Filtrage_bope_dialog(QDialog, Ui_dlgBopeRechercheForm):
    '''
    Class de la fenêtre permettant le filtrage attributaire des baux de pêche

    :param QDialog: Permet d'afficher l'interface graphique comme une fenêtre indépendante
    :type QDialog: QDialog

    :param Ui_dlgBopeRechercheForm: Class du script de l'interface graphique du formulaire,
            apporte les éléments de l'interface
    :type Ui_dlgBopeRechercheForm: class
    '''
    def __init__(self, db, dbType, dbSchema, modelBauxPe, parent=None):
        '''
        Constructeur, récupération de variable, connection des événements et remplissage des combobox

        :param db: définie dans le setupModel(),
                représente la connexion avec la base de données
        :type db: QSqlDatabase

        :param dbType: type de la base de données (postgre)
        :type dbType: str

        :param dbSchema: nom du schéma sous PostgreSQL contenant les données (data)
        :type dbSchema: unicode

        :param modelBauxPe: modèle droit de pêche qui contient les données de la base de données
        :type modelBauxPe: QSqlRelationalTableModel

        :param parent: défini que cette fenêtre n'hérite pas d'autres widgets
        :type parent: NoneType
        '''
        super(Filtrage_bope_dialog, self).__init__(parent)
        self.db = db
        self.dbType = dbType
        self.dbSchema = dbSchema
        self.modelBauxPe = modelBauxPe
        self.setupUi(self)

        self.btnAnnuler.clicked.connect(self.reject)
        self.btnExec.clicked.connect(self.execution)
        self.btnRaz.clicked.connect(self.raz)
        self.btnEt.clicked.connect(self.et)
        self.btnOu.clicked.connect(self.ou)

        self.btnPrevisualiser.clicked.connect(self.previSql)

        self.btnId.clicked.connect(self.ajoutId)
        self.btnRiviere.clicked.connect(self.ajoutRiviere)
        self.btnAappma.clicked.connect(self.ajoutAappma)
        self.btnPossession.clicked.connect(self.ajoutPossession)
        self.btnSign.clicked.connect(self.ajoutDateSign)
        self.btnFin.clicked.connect(self.ajoutDateFin)
        self.btnC.clicked.connect(self.ajoutCommune)
        self.btnCS.clicked.connect(self.ajoutComSection)
        self.btnCSP.clicked.connect(self.ajoutComSecParcelle)
        self.btnProprio.clicked.connect(self.ajoutProprio)
        self.btnAdresse.clicked.connect(self.ajoutAdresse)

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.leTel.setInputMask("#9999999999999")

        self.possessionBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.CBool = False
        self.CSBool = False
        self.CSPBool = False

        self.wwhere = ""
        self.wwherePossession = ""
        self.wwhereProprio = ""

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

        self.modelCommune = QSqlTableModel(self, self.db)
        wrelation = "commune"
        if self.dbType == "postgres":
            wrelation = self.dbSchema + "." + wrelation
        self.modelCommune.setTable(wrelation)
        self.modelCommune.setSort(2, Qt.AscendingOrder)
        if (not self.modelCommune.select()):
            QMessageBox.critical(self, u"Remplissage du modèle Commune", self.modelCommune.lastError().text(), QMessageBox.Ok)
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

    def reject(self):
        '''Ferme la fenêtre si clic sur le bouton annuler'''

        QDialog.reject(self)

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

    def raz(self):
        '''Réinitialise toutes les variables de la fenêtre afin de recommencer une nouvelle requête'''

        self.possessionBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.CBool = False
        self.CSBool = False
        self.CSPBool = False

        self.spnId.setValue(0)
        self.wrq = ""
        self.txtSql.setText("")
        self.wwhere = ""
        self.wwherePossession = ""
        self.wwhereProprio = ""

        self.chkPossession.setChecked(False)
        self.dateSign.setDate(QDate(2000,1,1))
        self.dateFin.setDate(QDate(2000,1,1))

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnId.setEnabled(True)
        self.btnSign.setEnabled(True)
        self.btnFin.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)
        self.btnPossession.setEnabled(True)
        self.btnC.setEnabled(True)
        self.btnCS.setEnabled(True)
        self.btnCSP.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)

    def et(self):
        '''Change l'état des boutons et ajoute "and" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnId.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)

        if self.possessionBool == False:
            self.btnPossession.setEnabled(True)

        if self.aappmaBool == False:
            self.btnAappma.setEnabled(True)

        if self.anneeSignBool == False:
            self.btnSign.setEnabled(True)

        if self.anneeFinBool == False:
            self.btnFin.setEnabled(True)

        if self.CBool == False:
            self.btnC.setEnabled(True)

        if self.CSBool == False:
            self.btnCS.setEnabled(True)

        if self.CSPBool == False:
            self.btnCSP.setEnabled(True)

        self.wwhere += " AND "

    def ou(self):
        '''Change l'état des boutons et ajoute "or" à la requête'''

        self.btnEt.setEnabled(False)
        self.btnOu.setEnabled(False)

        self.btnId.setEnabled(True)
        self.btnSign.setEnabled(True)
        self.btnFin.setEnabled(True)
        self.btnRiviere.setEnabled(True)
        self.btnAappma.setEnabled(True)
        self.btnC.setEnabled(True)
        self.btnCS.setEnabled(True)
        self.btnCSP.setEnabled(True)
        self.btnProprio.setEnabled(True)
        self.btnAdresse.setEnabled(True)
        self.btnPossession.setEnabled(True)

        self.possessionBool = False
        self.aappmaBool = False
        self.anneeSignBool = False
        self.anneeFinBool = False
        self.CBool = False
        self.CSBool = False
        self.CSPBool = False

        self.wwhere += " OR "

    def ajoutId(self):
        '''Change l'état des boutons et ajoute un critère d'id à la requête'''

        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.wid = self.spnId.value()
        if self.spnId.value() != "":
            if self.wid != "":
                self.wwhere += "bope_id = '" + str(self.wid) +"'"
        self.spnId.setValue(0)
        self.spnId.setFocus()

    def ajoutRiviere(self):
        '''Change l'état des boutons et ajoute un critère de cours d'eau à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        wfrombce = "bail_cours_eau"
        if self.dbType == "postgres":
            self.wfromCeau = self.dbSchema + "." + wfrombce

        wrecord = self.cmbRiviere.model().record(self.cmbRiviere.currentIndex())
        self.wCeau = wrecord.value(0)
        if self.cmbRiviere.currentText() != "":
            if self.wCeau != "":
                self.wwhere += "bope_id in (select distinct bce_bope_id from " + self.wfromCeau + " where bce_ceau_id = '" + str(self.wCeau) + "')"

    def ajoutAappma(self):
        '''Change l'état des boutons et ajoute un critère d'aappma à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.aappmaBool = True

        wrecord = self.cmbAappma.model().record(self.cmbAappma.currentIndex())
        self.wbope_aappma = wrecord.value(0)
        if self.cmbAappma.currentText() != "":
            if self.wbope_aappma != "":
                self.wwhere += "bope_apma_id = '" + str(self.wbope_aappma) + "'"

    def ajoutPossession(self):
        '''Change l'état des boutons et ajoute un critère de possession à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.possessionBool = True

        if self.chkPossession.isChecked() == True:
            self.wwherePossession = "bope_existe = True"
        else:
            self.wwherePossession = "bope_existe = False"

        self.wwhere += self.wwherePossession

    def ajoutDateSign(self):
        '''Change l'état des boutons et ajoute un critère de date de signature à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.anneeSignBool = True

        self.wbope_date_sign = self.dateSign.date().toString("yyyy")
        if self.wbope_date_sign != "":
            self.wwhere += "date_part('year', bope_date_sign) = '" + str(self.wbope_date_sign) + "'"

    def ajoutDateFin(self):
        '''Change l'état des boutons et ajoute un critère de date d'expiration à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.anneeFinBool = True

        self.wbope_date_fin = self.dateFin.date().toString("yyyy")
        if self.wbope_date_fin != "":
            self.wwhere += "date_part('year', bope_date_fin) = '" + str(self.wbope_date_fin) + "'"

    def ajoutCommune(self):
        '''Change l'état des boutons et ajoute un critère de commune à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.CBool = True

        wrecord = self.cmbCommune.model().record(self.cmbCommune.currentIndex())
        self.wcommune = wrecord.value(0)
        if self.cmbCommune.currentText() != "":
            if self.wcommune != "":
                self.wwhere += "bope_id in (select bope_id from data.droit_peche, data.parcelle, data.section where bope_id = par_bope_id and par_sec_id = sec_id and sec_com_insee = '" + str(self.wcommune) +"')"

    def ajoutComSection(self):
        '''Change l'état des boutons et ajoute un critère de commune et section à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.CSBool = True

        wrecord = self.cmbSection.model().record(self.cmbSection.currentIndex())
        self.wsection = wrecord.value(0)
        if self.cmbSection.currentText() != "":
            if self.wsection != "":
                self.wwhere += "bope_id in (select bope_id from data.droit_peche, data.parcelle where par_bope_id = bope_id and par_sec_id = '" + str(self.wsection) +"')"

    def ajoutComSecParcelle(self):
        '''Change l'état des boutons et ajoute un critère de commune, section et parcelle à la requête'''

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
        self.btnProprio.setEnabled(False)
        self.btnAdresse.setEnabled(False)

        self.CSPBool = True

        wrecord = self.cmbParcelle.model().record(self.cmbParcelle.currentIndex())
        self.wparcelle = wrecord.value(0)
        if self.cmbParcelle.currentText() != "":
            if self.wparcelle != "":
                self.wwhere += "bope_id in (select par_bope_id from data.parcelle where par_id = '" + str(self.wparcelle) +"')"

    def ajoutProprio(self):
        '''
        Change l'état des boutons et ajoute un critère de nom de propriétaire
        et / ou de mail
        et / ou de téléphone à la requête
        '''
        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
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

        self.btnEt.setEnabled(True)
        self.btnOu.setEnabled(True)

        self.btnId.setEnabled(False)
        self.btnSign.setEnabled(False)
        self.btnFin.setEnabled(False)
        self.btnRiviere.setEnabled(False)
        self.btnAappma.setEnabled(False)
        self.btnPossession.setEnabled(False)
        self.btnC.setEnabled(False)
        self.btnCS.setEnabled(False)
        self.btnCSP.setEnabled(False)
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
    # def previSql(self):
        '''Regroupe les différentes variables contenant les clauses de la requête SQL et les concatène pour en faire une requête exécutable'''

        self.wrq = ""

        # Construit la clause FROM de la requête
        cfrom = "droit_peche"
        if self.dbType == "postgres":
            cfrom = self.dbSchema + "." + cfrom

        # Construit la clause SELECT et ajoute la clause FROM à la requête
        self.wrq = "SELECT DISTINCT bope_id FROM " + cfrom

        # Construit la clause WHERE et ORDER BY et l'ajoute à la requête
        if self.wwhere != "":
            #Supprime l'opérateur "and" ou "or" si celui-ci n'est pas suivi d'un critère
            operateurs = ["AND", "OR"]
            fin_where = self.wwhere[-5:]
            for ext in operateurs:
                if ext in fin_where:
                    self.wwhere = self.wwhere[:-4]
            self.wrq += " WHERE " + self.wwhere + " ORDER BY bope_id"
        else :
            self.wrq += " ORDER BY bope_id"

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
                    if self.modelBauxPe:
                        # Filtre le modèle des droits de pêche et ferme la fenêtre
                        self.modelBauxPe.setFilter("bope_id in %s" % wparam)
                        self.modelBauxPe.select()
                        QDialog.accept(self)
                else :
                    QMessageBox.information(self, "Filtrage", u"Aucun bail de pêche ne correspond aux critères ...", QMessageBox.Ok)
            else:
                QMessageBox.critical(self, u"Erreur SQL", query.lastError().text(), QMessageBox.Ok)
