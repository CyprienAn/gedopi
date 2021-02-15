# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\bopeRechercheProprioForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgBopeRechercheProprioForm(object):
    def setupUi(self, dlgBopeRechercheProprioForm):
        dlgBopeRechercheProprioForm.setObjectName("dlgBopeRechercheProprioForm")
        dlgBopeRechercheProprioForm.resize(488, 221)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(dlgBopeRechercheProprioForm)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbl_riviere = QtWidgets.QLabel(dlgBopeRechercheProprioForm)
        self.lbl_riviere.setObjectName("lbl_riviere")
        self.horizontalLayout.addWidget(self.lbl_riviere)
        self.leNom = QtWidgets.QLineEdit(dlgBopeRechercheProprioForm)
        self.leNom.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.leNom.setObjectName("leNom")
        self.horizontalLayout.addWidget(self.leNom)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnChercher = QtWidgets.QPushButton(dlgBopeRechercheProprioForm)
        self.btnChercher.setObjectName("btnChercher")
        self.horizontalLayout_2.addWidget(self.btnChercher)
        self.btnAjouter = QtWidgets.QPushButton(dlgBopeRechercheProprioForm)
        self.btnAjouter.setObjectName("btnAjouter")
        self.horizontalLayout_2.addWidget(self.btnAjouter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lbl_resu = QtWidgets.QLabel(dlgBopeRechercheProprioForm)
        self.lbl_resu.setObjectName("lbl_resu")
        self.verticalLayout.addWidget(self.lbl_resu)
        self.tbvProprio = QtWidgets.QTableView(dlgBopeRechercheProprioForm)
        self.tbvProprio.setObjectName("tbvProprio")
        self.verticalLayout.addWidget(self.tbvProprio)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btnAnnuler = QtWidgets.QPushButton(dlgBopeRechercheProprioForm)
        self.btnAnnuler.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnAnnuler.setObjectName("btnAnnuler")
        self.horizontalLayout_3.addWidget(self.btnAnnuler)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.retranslateUi(dlgBopeRechercheProprioForm)
        QtCore.QMetaObject.connectSlotsByName(dlgBopeRechercheProprioForm)

    def retranslateUi(self, dlgBopeRechercheProprioForm):
        _translate = QtCore.QCoreApplication.translate
        dlgBopeRechercheProprioForm.setWindowTitle(_translate("dlgBopeRechercheProprioForm", "Recherche d\'un propriétaire"))
        self.lbl_riviere.setText(_translate("dlgBopeRechercheProprioForm", "Nom du propriétaire :"))
        self.btnChercher.setText(_translate("dlgBopeRechercheProprioForm", "Chercher"))
        self.btnAjouter.setText(_translate("dlgBopeRechercheProprioForm", "Ajouter"))
        self.lbl_resu.setText(_translate("dlgBopeRechercheProprioForm", "Résultat(s) :"))
        self.btnAnnuler.setText(_translate("dlgBopeRechercheProprioForm", "Annuler"))

