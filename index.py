#!/bin/env python3
from PyQt5.QtWidgets import QApplication, QFileDialog, QLineEdit, QMainWindow, QSpinBox, QWidget, QGroupBox, QPushButton, QLabel, QGridLayout, QStatusBar
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
    times=""
    for part in nogap:
        times+=f"+between(t,{part[0]},{part[1]})"
    times=times[1:]
    ffmpeg=f"""ffmpeg -i {inp} -vf "select='{times}', setpts=N/FRAME_RATE/TB\" -af "aselect='{times}', asetpts=N/SR/TB" -y out.mp4"""
    system(ffmpeg)
    print(ffmpeg)

class MainWin(QMainWindow):
    def __init__(self):
        super(MainWin,self).__init__()
        self.show()
        self.setFixedSize(400,self.minimumHeight())
        self.l_status=QStatusBar()
        self.setStatusBar(self.l_status)
        self.central=Central()
        self.setCentralWidget(self.central)

class Central(QWidget):
    def __init__(self):
        super(Central,self).__init__()
        self.layout=QGridLayout(self)

        self.box_file_select=QGroupBox("File Selection",self)
        self.lay_file_select=QGridLayout(self.box_file_select)

        self.l_description=QLabel("Pick or drag and drop a file to start.")
        self.l_description.setWordWrap(True)
        self.b_input_select=QPushButton("Select File",self)
        self.e_input_file_name=QLineEdit("Not Selected.")
        self.e_input_file_name.setDisabled(True)
        self.e_input_file_name.setStyleSheet("color:black;")

        self.lay_file_select.addWidget(self.l_description,0,0,1,3)
        self.lay_file_select.addWidget(self.b_input_select,1,0)
        self.lay_file_select.addWidget(self.e_input_file_name,1,1,1,2)

        self.box_settings=QGroupBox("Settings",self)
        self.lay_settings=QGridLayout(self.box_settings)

        self.l_treshold=QLabel("Audio Trashold (db)")
        self.s_treshold=QSpinBox()
        self.s_treshold.setRange(-50,50)
        self.s_treshold.setValue(-16)
        self.l_min_silence=QLabel("Minimum Silence Length (ms)")
        self.s_min_silence=QSpinBox()
        self.s_min_silence.setSingleStep(100)
        self.s_min_silence.setRange(500,10000)
        self.l_keep_silence=QLabel("Keep Silence (ms)")
        self.s_keep_silence=QSpinBox()
        self.s_keep_silence.setRange(100,10000)
        self.s_keep_silence.setSingleStep(100)
        self.desc_keep_silence=QLabel("Automatically sets half of minimum silence length if more than half.")
        self.desc_keep_silence.setWordWrap(True)
        self.desc_keep_silence.setStyleSheet("color:gray;font-size:9pt;")

        self.lay_settings.addWidget(self.l_treshold)
        self.lay_settings.addWidget(self.s_treshold)
        self.lay_settings.addWidget(self.l_min_silence)
        self.lay_settings.addWidget(self.s_min_silence)
        self.lay_settings.addWidget(self.l_keep_silence)
        self.lay_settings.addWidget(self.s_keep_silence)
        self.lay_settings.addWidget(self.desc_keep_silence)
        
        self.box_convert=QGroupBox("Convert",self)
        self.lay_convert=QGridLayout(self.box_convert)

        self.b_output_select=QPushButton("Select File",self)
        self.e_output_file_name=QLineEdit("Not Selected.")
        self.e_output_file_name.setDisabled(True)
        self.e_output_file_name.setStyleSheet("color:black;")
        self.b_convert=QPushButton("Start",self)

        self.lay_convert.addWidget(self.b_output_select,0,0,1,1)
        self.lay_convert.addWidget(self.e_output_file_name,0,1,1,1)
        self.lay_convert.addWidget(self.b_convert,1,0,1,2)

        self.layout.addWidget(self.box_file_select,0,0,1,3)
        self.layout.addWidget(self.box_settings,1,0,1,3)
        self.layout.addWidget(self.box_convert,2,1)

        self.input_file=""
        self.output_file=""

        self.b_input_select.clicked.connect(self.select_input_file)
        self.b_input_select.setShortcut(QKeySequence("Ctrl+O"))
        self.e_input_file_name.textChanged.connect(self.can_convert)
        self.b_convert.clicked.connect(lambda:convert(self.input_file,self.s_treshold.value(),self.s_min_silence.value(),self.s_keep_silence.value()))
        self.can_convert()

    def select_input_file(self):
        file=QFileDialog.getOpenFileName(self,"Select File","","",options=QFileDialog.DontUseNativeDialog)
        self.input_file=file[0]
        self.e_input_file_name.setText(file[0].split("/")[-1] if file[0] else "Not Selected.")

    def select_output_file(self):
        file=QFileDialog.getOpenFileName(self,"Select File","","",options=QFileDialog.DontUseNativeDialog)
        self.output_file=file[0]
        if "." in self.input_file:
            if self.output_file.endswith("."+self.input_file.split(".")[-1]):
                self.output_file+="."+self.input_file.split(".")[-1]
        self.e_output_file_name.setText(file[0].split("/")[-1] if file[0] else "Not Selected.")

    def can_convert(self):
        state=self.e_input_file_name.text()=="Not Selected."
        self.b_convert.setDisabled(state)

app=QApplication(argv)
app.setApplicationName("Video Gap Remover")
main=MainWin()
exit(app.exec_())
