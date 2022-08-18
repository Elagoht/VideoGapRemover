#!/usr/bin/python3
from PyQt5.QtWidgets import QApplication, QFileDialog, QLineEdit, QMainWindow, QSpinBox, QWidget, QGroupBox, QPushButton, QLabel, QGridLayout
from PyQt5.QtGui import  QKeySequence
from sys import argv,exit
from os import system
from pydub import AudioSegment,silence

messages={
    "select":"Select a file to convert.",
    "ready":"Ready to convert.",
    "success":"Successfully converted into {}.",
    "unselected":"Output file not selected.",
    "notdocx":"File extension must be docx."
}

def convert(inp:str,tsh:int,slen:int,kpt:int):
    out="/".join(inp.split("/")[:-1])
    if kpt>slen/2:kpt=slen/2
    audio=AudioSegment.from_file(inp)
    nogap=silence.detect_nonsilent(audio, min_silence_len=slen, silence_thresh=audio.dBFS-16)
    nogap=[((start-kpt)/1000 if (start-kpt)/1000>0 else 0,(stop+kpt)/1000 if (stop+kpt)/1000<len(audio) else len(audio)) for start,stop in nogap]
    print(nogap)
    for i in range(len(nogap)):
        print(f"ffmpeg -i {inp} -ss {nogap[i][0]} -to {nogap[i][1]} -async 1 -c copy {out}/cut{i}.mp4")
        system(f"ffmpeg -i {inp} -ss {nogap[i][0]} -to {nogap[i][1]} -async 1 -c copy {out}/cut{i}.mp4")
    with open(out+"/cuts.list","w") as file: file.writelines(f"file 'cut{i}.mp4'\n" for i in range(len(nogap)))
    system(f"ffmpeg -f concat -i {out}/cuts.list -c copy {out}/output.mp4")
    print(nogap)

class MainWin(QMainWindow):
    def __init__(self):
        super(MainWin,self).__init__()
        self.show()
        self.setFixedSize(360,400)
        self.central=Central()
        self.setCentralWidget(self.central)

class Central(QWidget):
    def __init__(self):
        super(Central,self).__init__()
        self.layout=QGridLayout(self)

        self.boxFileSelect=QGroupBox("File Selection",self)
        self.layFileSelect=QGridLayout(self.boxFileSelect)

        self.lDescription=QLabel("Pick or drag and drop a file to start.")
        self.lDescription.setWordWrap(True)
        self.bSelect=QPushButton("Select File",self)
        self.eFileName=QLineEdit("Not Selected.")
        self.eFileName.setDisabled(True)
        self.eFileName.setStyleSheet("color:black;")

        self.layFileSelect.addWidget(self.lDescription,0,0,1,3)
        self.layFileSelect.addWidget(self.bSelect,1,0)
        self.layFileSelect.addWidget(self.eFileName,1,1,1,2)

        self.boxSettings=QGroupBox("Settings",self)
        self.laySettings=QGridLayout(self.boxSettings)

        self.lTreshold=QLabel("Audio Trashold (db)")
        self.sTreshold=QSpinBox()
        self.sTreshold.setRange(-50,50)
        self.sTreshold.setValue(-16)
        self.lMinSilence=QLabel("Minimum Silence Length (ms)")
        self.sMinSilence=QSpinBox()
        self.sMinSilence.setSingleStep(100)
        self.sMinSilence.setRange(500,10000)
        self.lKeepSilence=QLabel("Keep Silence (ms)")
        self.sKeepSilence=QSpinBox()
        self.sKeepSilence.setRange(100,10000)
        self.sKeepSilence.setSingleStep(100)
        self.descKeepSilence=QLabel("Automatically sets half of minimum silence length if more than half.")
        self.descKeepSilence.setWordWrap(True)
        self.descKeepSilence.setStyleSheet("color:gray;font-size:9pt;")

        self.laySettings.addWidget(self.lTreshold)
        self.laySettings.addWidget(self.sTreshold)
        self.laySettings.addWidget(self.lMinSilence)
        self.laySettings.addWidget(self.sMinSilence)
        self.laySettings.addWidget(self.lKeepSilence)
        self.laySettings.addWidget(self.sKeepSilence)
        self.laySettings.addWidget(self.descKeepSilence)

        self.bConvert=QPushButton("Convert",self)
        self.lStatus=QLabel()

        self.layout.addWidget(self.boxFileSelect,0,0,1,3)
        self.layout.addWidget(self.boxSettings,1,0,1,3)
        self.layout.addWidget(self.bConvert,2,1)
        self.layout.addWidget(self.lStatus,3,0,1,3)

        self.file=""

        self.bSelect.clicked.connect(self.selectFile)
        self.bSelect.setShortcut(QKeySequence("Ctrl+O"))
        self.eFileName.textChanged.connect(self.canConvert)
        self.bConvert.clicked.connect(lambda:convert(self.file,self.sTreshold.value(),self.sMinSilence.value(),self.sKeepSilence.value()))
        self.canConvert()

    def selectFile(self):
        file=QFileDialog.getOpenFileName(self,"Select File","","",options=QFileDialog.DontUseNativeDialog)
        self.file=file[0]
        self.eFileName.setText(file[0].split("/")[-1] if file[0] else "Not Selected.")

    def canConvert(self):
        state=self.eFileName.text()=="Not Selected."
        self.bConvert.setDisabled(state)
        if state:
            self.lStatus.setText(messages["select"])
        else:
            self.lStatus.setText(messages["ready"])

app=QApplication(argv)
app.setApplicationName("Video Gap Remover")
main=MainWin()
exit(app.exec_())
