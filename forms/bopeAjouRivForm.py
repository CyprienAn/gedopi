# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\bopeAjouRivForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgBopeAjoutRiviereForm(object):
    def setupUi(self, dlgBopeAjoutRiviereForm):
        dlgBopeAjoutRiviereForm.setObjectName("dlgBopeAjoutRiviereForm")
        dlgBopeAjoutRiviereForm.resize(314, 256)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dlgBopeAjoutRiviereForm.sizePolicy().hasHeightForWidth())
        dlgBopeAjoutRiviereForm.setSizePolicy(sizePolicy)
        dlgBopeAjoutRiviereForm.setMinimumSize(QtCore.QSize(280, 220))
        dlgBopeAjoutRiviereForm.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(dlgBopeAjoutRiviereForm)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbl_riviere = QtWidgets.QLabel(dlgBopeAjoutRiviereForm)
        self.lbl_riviere.setObjectName("lbl_riviere")
        self.horizontalLayout.addWidget(self.lbl_riviere)
        self.leNom = QtWidgets.QLineEdit(dlgBopeAjoutRiviereForm)
        self.leNom.setObjectName("leNom")
        self.horizontalLayout.addWidget(self.leNom)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.lbl_resu = QtWidgets.QLabel(dlgBopeAjoutRiviereForm)
        self.lbl_resu.setObjectName("lbl_resu")
        self.verticalLayout_2.addWidget(self.lbl_resu)
        self.tbvResu = QtWidgets.QTableView(dlgBopeAjoutRiviereForm)
        self.tbvResu.setObjectName("tbvResu")
        self.verticalLayout_2.addWidget(self.tbvResu)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnChercher = QtWidgets.QPushButton(dlgBopeAjoutRiviereForm)
        self.btnChercher.setObjectName("btnChercher")
        self.horizontalLayout_2.addWidget(self.btnChercher)
        self.btnAjouter = QtWidgets.QPushButton(dlgBopeAjoutRiviereForm)
        self.btnAjouter.setObjectName("btnAjouter")
        self.horizontalLayout_2.addWidget(self.btnAjouter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btnAnnuler = QtWidgets.QPushButton(dlgBopeAjoutRiviereForm)
        self.btnAnnuler.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnAnnuler.setObjectName("btnAnnuler")
        self.horizontalLayout_3.addWidget(self.btnAnnuler)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.retranslateUi(dlgBopeAjoutRiviereForm)
        QtCore.QMetaObject.connectSlotsByName(dlgBopeAjoutRiviereForm)

    def retranslateUi(self, dlgBopeAjoutRiviereForm):
        _translate = QtCore.QCoreApplication.translate
        dlgBopeAjoutRiviereForm.setWindowTitle(_translate("dlgBopeAjoutRiviereForm", "Ajout d\'une rivière"))
        self.lbl_riviere.setText(_translate("dlgBopeAjoutRiviereForm", "Nom de la rivière :"))
        self.lbl_resu.setText(_translate("dlgBopeAjoutRiviereForm", "Résultat(s) :"))
        self.btnChercher.setText(_translate("dlgBopeAjoutRiviereForm", "Chercher"))
        self.btnAjouter.setText(_translate("dlgBopeAjoutRiviereForm", "Ajouter"))
        self.btnAnnuler.setText(_translate("dlgBopeAjoutRiviereForm", "Annuler"))

