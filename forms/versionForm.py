# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\versionForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_versionForm(object):
    def setupUi(self, versionForm):
        versionForm.setObjectName("versionForm")
        versionForm.resize(525, 268)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(versionForm.sizePolicy().hasHeightForWidth())
        versionForm.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(versionForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(versionForm)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 505, 219))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.teMessage = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)
        self.teMessage.setObjectName("teMessage")
        self.verticalLayout_2.addWidget(self.teMessage)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtWidgets.QDialogButtonBox(versionForm)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(versionForm)
        QtCore.QMetaObject.connectSlotsByName(versionForm)

    def retranslateUi(self, versionForm):
        _translate = QtCore.QCoreApplication.translate
        versionForm.setWindowTitle(_translate("versionForm", "Gedopi - Note de version"))
        self.teMessage.setHtml(_translate("versionForm", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">Version 1.0 - notes concernant cette version :</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt; font-weight:600;\">    </span><span style=\" font-size:8pt;\">- première version du plugin des bugs ou soucis peuvent avoir lieux, merci de les transmettre au développeur (</span><a href=\"mailto:antignac.cyprien@laposte.net?subject=Plugin Gedopi\"><span style=\" font-size:8pt; text-decoration: underline; color:#0000ff;\">antignac.cyprien@laposte.net</span></a><span style=\" font-size:8pt;\">);</span></p>\n"
"<p align=\"justify\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">    - ce plugin fonctionne sous des versions QGIS 3.x (soit avec Qt 5 et Python 3), ne fonctionne plus avec les versions de QGIS 2.x (Qt 4 et Python 2.7);</span></p></body></html>"))

