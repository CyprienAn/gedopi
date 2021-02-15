# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\opeMoaAjoutForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgMoaAjoutForm(object):
    def setupUi(self, dlgMoaAjoutForm):
        dlgMoaAjoutForm.setObjectName("dlgMoaAjoutForm")
        dlgMoaAjoutForm.resize(400, 83)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlgMoaAjoutForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(dlgMoaAjoutForm)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.cmbMoa = QtWidgets.QComboBox(dlgMoaAjoutForm)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbMoa.sizePolicy().hasHeightForWidth())
        self.cmbMoa.setSizePolicy(sizePolicy)
        self.cmbMoa.setObjectName("cmbMoa")
        self.horizontalLayout.addWidget(self.cmbMoa)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.btnBox = QtWidgets.QDialogButtonBox(dlgMoaAjoutForm)
        self.btnBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.btnBox.setCenterButtons(True)
        self.btnBox.setObjectName("btnBox")
        self.verticalLayout.addWidget(self.btnBox)

        self.retranslateUi(dlgMoaAjoutForm)
        QtCore.QMetaObject.connectSlotsByName(dlgMoaAjoutForm)

    def retranslateUi(self, dlgMoaAjoutForm):
        _translate = QtCore.QCoreApplication.translate
        dlgMoaAjoutForm.setWindowTitle(_translate("dlgMoaAjoutForm", "Ajout d\'un maître d\'ouvrage"))
        self.label.setText(_translate("dlgMoaAjoutForm", "Maitre d\'ouvrage :"))

