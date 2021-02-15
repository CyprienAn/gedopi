# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\opeOperateurAjoutForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgOperateurAjoutForm(object):
    def setupUi(self, dlgOperateurAjoutForm):
        dlgOperateurAjoutForm.setObjectName("dlgOperateurAjoutForm")
        dlgOperateurAjoutForm.resize(400, 84)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlgOperateurAjoutForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(dlgOperateurAjoutForm)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cmbOperateur = QtWidgets.QComboBox(dlgOperateurAjoutForm)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbOperateur.sizePolicy().hasHeightForWidth())
        self.cmbOperateur.setSizePolicy(sizePolicy)
        self.cmbOperateur.setObjectName("cmbOperateur")
        self.horizontalLayout.addWidget(self.cmbOperateur)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.btnBox = QtWidgets.QDialogButtonBox(dlgOperateurAjoutForm)
        self.btnBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.btnBox.setCenterButtons(True)
        self.btnBox.setObjectName("btnBox")
        self.verticalLayout.addWidget(self.btnBox)

        self.retranslateUi(dlgOperateurAjoutForm)
        QtCore.QMetaObject.connectSlotsByName(dlgOperateurAjoutForm)

    def retranslateUi(self, dlgOperateurAjoutForm):
        _translate = QtCore.QCoreApplication.translate
        dlgOperateurAjoutForm.setWindowTitle(_translate("dlgOperateurAjoutForm", "Ajout d\'un opérateur"))
        self.label.setText(_translate("dlgOperateurAjoutForm", "Opérateur :"))

