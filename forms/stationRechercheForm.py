# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\stationRechercheForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgStationRechercheForm(object):
    def setupUi(self, dlgStationRechercheForm):
        dlgStationRechercheForm.setObjectName("dlgStationRechercheForm")
        dlgStationRechercheForm.resize(388, 474)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(dlgStationRechercheForm)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.scrollArea = QtWidgets.QScrollArea(dlgStationRechercheForm)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 368, 454))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.groupBox = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)
        self.btnEt = QtWidgets.QPushButton(self.groupBox)
        self.btnEt.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnEt.setObjectName("btnEt")
        self.horizontalLayout_12.addWidget(self.btnEt)
        self.btnOu = QtWidgets.QPushButton(self.groupBox)
        self.btnOu.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnOu.setObjectName("btnOu")
        self.horizontalLayout_12.addWidget(self.btnOu)
        self.verticalLayout.addLayout(self.horizontalLayout_12)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.spnId = QtWidgets.QSpinBox(self.groupBox)
        self.spnId.setMaximum(900000)
        self.spnId.setObjectName("spnId")
        self.horizontalLayout.addWidget(self.spnId)
        self.horizontalLayout_6.addLayout(self.horizontalLayout)
        self.btnId = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnId.sizePolicy().hasHeightForWidth())
        self.btnId.setSizePolicy(sizePolicy)
        self.btnId.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnId.setObjectName("btnId")
        self.horizontalLayout_6.addWidget(self.btnId)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.cmbPdpg = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbPdpg.sizePolicy().hasHeightForWidth())
        self.cmbPdpg.setSizePolicy(sizePolicy)
        self.cmbPdpg.setObjectName("cmbPdpg")
        self.horizontalLayout_2.addWidget(self.cmbPdpg)
        self.btnPdpg = QtWidgets.QPushButton(self.groupBox)
        self.btnPdpg.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnPdpg.setObjectName("btnPdpg")
        self.horizontalLayout_2.addWidget(self.btnPdpg)
        self.horizontalLayout_7.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.cmbMeau = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbMeau.sizePolicy().hasHeightForWidth())
        self.cmbMeau.setSizePolicy(sizePolicy)
        self.cmbMeau.setObjectName("cmbMeau")
        self.horizontalLayout_3.addWidget(self.cmbMeau)
        self.horizontalLayout_8.addLayout(self.horizontalLayout_3)
        self.btnMeau = QtWidgets.QPushButton(self.groupBox)
        self.btnMeau.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnMeau.setObjectName("btnMeau")
        self.horizontalLayout_8.addWidget(self.btnMeau)
        self.verticalLayout.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.cmbRiviere = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbRiviere.sizePolicy().hasHeightForWidth())
        self.cmbRiviere.setSizePolicy(sizePolicy)
        self.cmbRiviere.setObjectName("cmbRiviere")
        self.horizontalLayout_4.addWidget(self.cmbRiviere)
        self.horizontalLayout_9.addLayout(self.horizontalLayout_4)
        self.btnRiviere = QtWidgets.QPushButton(self.groupBox)
        self.btnRiviere.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnRiviere.setObjectName("btnRiviere")
        self.horizontalLayout_9.addWidget(self.btnRiviere)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.cmbAappma = QtWidgets.QComboBox(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbAappma.sizePolicy().hasHeightForWidth())
        self.cmbAappma.setSizePolicy(sizePolicy)
        self.cmbAappma.setObjectName("cmbAappma")
        self.horizontalLayout_5.addWidget(self.cmbAappma)
        self.horizontalLayout_10.addLayout(self.horizontalLayout_5)
        self.btnAappma = QtWidgets.QPushButton(self.groupBox)
        self.btnAappma.setMaximumSize(QtCore.QSize(50, 16777215))
        self.btnAappma.setObjectName("btnAappma")
        self.horizontalLayout_10.addWidget(self.btnAappma)
        self.verticalLayout.addLayout(self.horizontalLayout_10)
        self.verticalLayout_4.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setWordWrap(True)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_3.addWidget(self.label_6)
        self.txtSql = QtWidgets.QTextEdit(self.groupBox_2)
        self.txtSql.setMaximumSize(QtCore.QSize(16777215, 100))
        self.txtSql.setObjectName("txtSql")
        self.verticalLayout_3.addWidget(self.txtSql)
        self.verticalLayout_4.addWidget(self.groupBox_2)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.btnPrevisualiser = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btnPrevisualiser.setObjectName("btnPrevisualiser")
        self.horizontalLayout_11.addWidget(self.btnPrevisualiser)
        self.btnExec = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btnExec.setObjectName("btnExec")
        self.horizontalLayout_11.addWidget(self.btnExec)
        self.btnRaz = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btnRaz.setObjectName("btnRaz")
        self.horizontalLayout_11.addWidget(self.btnRaz)
        self.btnAnnuler = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btnAnnuler.setObjectName("btnAnnuler")
        self.horizontalLayout_11.addWidget(self.btnAnnuler)
        self.verticalLayout_4.addLayout(self.horizontalLayout_11)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)

        self.retranslateUi(dlgStationRechercheForm)
        QtCore.QMetaObject.connectSlotsByName(dlgStationRechercheForm)

    def retranslateUi(self, dlgStationRechercheForm):
        _translate = QtCore.QCoreApplication.translate
        dlgStationRechercheForm.setWindowTitle(_translate("dlgStationRechercheForm", "Recherche de station(s)"))
        self.groupBox.setTitle(_translate("dlgStationRechercheForm", "Critère(s) :"))
        self.btnEt.setText(_translate("dlgStationRechercheForm", "Et"))
        self.btnOu.setText(_translate("dlgStationRechercheForm", "Ou"))
        self.label.setText(_translate("dlgStationRechercheForm", "ID :"))
        self.btnId.setText(_translate("dlgStationRechercheForm", "Ajouter"))
        self.label_2.setText(_translate("dlgStationRechercheForm", "Contexte PDPG :"))
        self.btnPdpg.setText(_translate("dlgStationRechercheForm", "Ajouter"))
        self.label_3.setText(_translate("dlgStationRechercheForm", "Masse d\'eau :"))
        self.btnMeau.setText(_translate("dlgStationRechercheForm", "Ajouter"))
        self.label_4.setText(_translate("dlgStationRechercheForm", "Rivière :"))
        self.btnRiviere.setText(_translate("dlgStationRechercheForm", "Ajouter"))
        self.label_5.setText(_translate("dlgStationRechercheForm", "AAPPMA :"))
        self.btnAappma.setText(_translate("dlgStationRechercheForm", "Ajouter"))
        self.groupBox_2.setTitle(_translate("dlgStationRechercheForm", "Requête SQL :"))
        self.label_6.setText(_translate("dlgStationRechercheForm", "<html><head/><body><p align=\"justify\"><span style=\" font-size:7pt;\">Attention : les modifications dans la requête sont possibles mais peuvent faire échouer celle-ci voir endommager la base de données ! ! !</span></p></body></html>"))
        self.txtSql.setHtml(_translate("dlgStationRechercheForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p></body></html>"))
        self.btnPrevisualiser.setText(_translate("dlgStationRechercheForm", "Prévisualisation"))
        self.btnExec.setText(_translate("dlgStationRechercheForm", "Exécuter"))
        self.btnRaz.setText(_translate("dlgStationRechercheForm", "Réinitialiser"))
        self.btnAnnuler.setText(_translate("dlgStationRechercheForm", "Annuler"))
