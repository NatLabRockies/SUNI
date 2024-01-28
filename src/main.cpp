/*
BSD 3-Clause License

Copyright (c) Alliance for Sustainable Energy, LLC. See also https://github.com/NREL/SAM/blob/develop/LICENSE
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/


#include <set>
//#include <chrono>

#include <wx/wx.h>
#include <wx/frame.h>
#include <wx/stc/stc.h>
#include <fstream>

#if defined(__WXMSW__)||defined(__WXOSX__)
#include <wx/webview.h>
#else
#include <wx/html/htmlwin.h> // for linux - avoid webkitgtk dependencies
#endif

#include <wx/simplebook.h>
#include <wx/panel.h>
#include <wx/busyinfo.h>
#include <wx/dynlib.h>
#include <wx/dir.h>
#include <wx/wfstream.h>
#include <wx/datstrm.h>
#include <wx/grid.h>
#include <wx/stdpaths.h>
#include <wx/webview.h>
#include <wx/txtstrm.h>
#include <wx/buffer.h>
#include <wx/display.h>
#include <wx/utils.h>
#include <wx/platform.h>
#include <wx/txtstrm.h>
#include <wx/filename.h>

#include "main.h"
#include "pythonhandler.h"


#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/prettywriter.h" // for stringify JSON
#include "rapidjson/filereadstream.h"
#include "rapidjson/filewritestream.h"
#include "rapidjson/istreamwrapper.h"
#include "rapidjson/document.h"


static PythonConfig pythonConfig;


enum { __idFirst = wxID_HIGHEST+592,

	ID_BTN_INPUTFILE, ID_BTN_OUTPUTFILE, ID_BTN_SERIQCPATH,
	ID_TXT_INPUTFILE, ID_TXT_OUTPUTFILE, ID_TXT_SERIQCPATH,
	ID_INTERNAL_DATAFOLDER, ID_CMB_SERI_QC, ID_CMB_INTERVAL,
	ID_GHIid, ID_GHImodel, ID_GHIclass, ID_GHIclassUncert, ID_GHIcalUncert, ID_GHIcalDate, ID_GHIdueDate, ID_GHIradUncert,
	ID_DNIid, ID_DNImodel, ID_DNIclass, ID_DNIclassUncert, ID_DNIcalUncert, ID_DNIcalDate, ID_DNIdueDate, ID_DNIradUncert,
	ID_DHIid, ID_DHImodel, ID_DHIclass, ID_DHIclassUncert, ID_DHIcalUncert, ID_DHIcalDate, ID_DHIdueDate, ID_DHIradUncert,
	ID_MaxQC, ID_MinDNI, ID_MaxZEN, ID_DateFormat1, ID_DateFormat2, ID_ExtendedRpt, ID_BTN_START, ID_BTN_CANCEL, ID_PROGRESS
};

BEGIN_EVENT_TABLE( MainWindow, wxFrame )
	EVT_CLOSE( MainWindow::OnClose )
	EVT_MENU( wxID_ABOUT, MainWindow::OnCommand )
	EVT_MENU( wxID_HELP, MainWindow::OnCommand )
	EVT_MENU(wxID_OPEN, MainWindow::OnCommand)
	EVT_MENU( wxID_SAVE, MainWindow::OnCommand )
	EVT_MENU( wxID_SAVEAS, MainWindow::OnCommand )
	EVT_MENU( wxID_CLOSE, MainWindow::OnCommand )
	EVT_MENU( wxID_EXIT, MainWindow::OnCommand )
END_EVENT_TABLE()

static std::unique_ptr<std::string> s_python_path;

int set_python_path(const char* abs_path) {
	if (wxFileName::DirExists(abs_path)) {
		s_python_path = std::unique_ptr<std::string>(new std::string(abs_path));
		return 1;
	}
	else
		return 0;
}

MainWindow::MainWindow()
	: wxFrame( 0, wxID_ANY, wxString("Solar Uncertainty Integrator"),
		wxDefaultPosition, wxSize( 1100, 700 ) )
{
#ifdef __WXMSW__
	SetIcon( wxICON( appicon ) );
#endif

#ifdef __WXOSX__
	wxMenu *fileMenu = new wxMenu;
	fileMenu->Append( wxID_NEW, "New project\tCtrl-N" );
	fileMenu->Append( ID_NEW_SCRIPT, "New script" );
	fileMenu->AppendSeparator();
	fileMenu->Append( wxID_OPEN, "Open project\tCtrl-O" );
	fileMenu->Append( ID_OPEN_SCRIPT, "Open script" );
	fileMenu->AppendSeparator();
	fileMenu->Append( wxID_SAVE, "Save\tCtrl-S" );
	fileMenu->Append( wxID_SAVEAS, "Save as..." );
	fileMenu->Append( ID_SAVE_HOURLY, "Save with hourly results");
	fileMenu->AppendSeparator();
	fileMenu->Append( ID_IMPORT_CASES, "Import cases..");
	fileMenu->AppendSeparator();
	fileMenu->Append( ID_BROWSE_INPUTS, "Inputs browser...");
	fileMenu->AppendSeparator();
	fileMenu->Append( wxID_EXIT, "Quit SAM");

	wxMenu *caseMenu = new wxMenu;
	caseMenu->Append( ID_CASE_SIMULATE, "Simulate\tF5" );
	caseMenu->Append( ID_CASE_REPORT, "Create report\tF6" );
	caseMenu->Append( ID_CASE_CLEAR_RESULTS, "Clear all results" );
	caseMenu->AppendSeparator();
	caseMenu->Append( ID_CASE_RENAME, "Rename\tF2" );
	caseMenu->Append( ID_CASE_DUPLICATE, "Duplicate" );
	caseMenu->Append( ID_CASE_DELETE, "Delete" );
	caseMenu->AppendSeparator();
	caseMenu->Append( ID_CASE_MOVE_LEFT, "Move left" );
	caseMenu->Append( ID_CASE_MOVE_RIGHT, "Move right" );
	caseMenu->AppendSeparator();
	caseMenu->Append( ID_CASE_CONFIG, "Change model..." );
	caseMenu->Append( ID_CASE_RESET_DEFAULTS, "Reset inputs to default values" );

	wxMenu *helpMenu = new wxMenu;
	helpMenu->Append( wxID_HELP );
	helpMenu->AppendSeparator();
	helpMenu->Append( wxID_ABOUT );

	wxMenuBar *menuBar = new wxMenuBar;
	menuBar->Append( fileMenu, wxT("&File") );
	menuBar->Append( caseMenu, wxT("&Case")  );
	menuBar->Append( helpMenu, wxT("&Help")  );
	SetMenuBar( menuBar );
#endif
	m_mainMenuBar = new wxMenuBar;

	wxMenu *menu = new wxMenu ;
	menu->Append(wxID_SAVEAS, "Save Configuration");
	menu->Append(wxID_OPEN, "Open Configuration");
	menu->Append(wxID_EXIT, "Close");

	m_mainMenuBar->Append(menu, wxT("&File"));

	SetMenuBar(m_mainMenuBar);

	p = new wxPanel(this, wxID_ANY);

	wxStaticBoxSizer* sizer0 = new wxStaticBoxSizer(wxVERTICAL,p, "Files");
	sizer0->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	m_bInputFile = new wxButton(p, ID_BTN_INPUTFILE, "Input File");
	sizer0->Add(m_bInputFile,0, wxALIGN_LEFT,5);
	InputFile = new wxTextCtrl(p, ID_TXT_INPUTFILE, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "InputFile");
	InputFile->SetSizeHints(500, 24);
	sizer0->Add(InputFile,1, wxEXPAND | wxALL,5);
	m_bOutputFile = new wxButton(p, ID_BTN_OUTPUTFILE, "Output File");
	sizer0->Add(m_bOutputFile, 0, wxALIGN_LEFT, 5);
	OutputFile = new wxTextCtrl(p, ID_TXT_OUTPUTFILE, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "OutputFile");
	OutputFile->SetSizeHints(500, 24);
	sizer0->Add(OutputFile, 1, wxEXPAND | wxALL, 5);
	m_bSERIQCPath = new wxButton(p, ID_BTN_SERIQCPATH, "SERI QC Path");
	sizer0->Add(m_bSERIQCPath, 0, wxALIGN_LEFT, 5);
	SERIQCPath = new wxTextCtrl(p, ID_TXT_SERIQCPATH, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "SERIQCPath");
	SERIQCPath->SetSizeHints(500, 24);
	sizer0->Add(SERIQCPath, 1, wxEXPAND | wxALL, 5);
	wxGridSizer* grdFiles = new wxGridSizer(2, 2, 2, 5);
	grdFiles->Add(new wxStaticText(p, wxID_ANY, "SERI QC Station ID"));
	grdFiles->Add(new wxStaticText(p, wxID_ANY, "Interval (minutes)"),1, wxALIGN_RIGHT);
	// TODO - populate StationID
	wxArrayString asStationID;
	asStationID.Add("NRELSR");
	StationID = new wxComboBox(p, ID_CMB_SERI_QC, "NRELSR", wxDefaultPosition, wxDefaultSize, asStationID, wxCB_READONLY, wxDefaultValidator, "StationID");
	StationID->SetSizeHints(350, 24);
	wxArrayString asInterval;
	for (int i = 1; i < 61; i++)
		asInterval.Add(wxString::FromDouble(i));
	Interval = new wxComboBox(p, ID_CMB_INTERVAL,"1", wxDefaultPosition, wxDefaultSize, asInterval, wxCB_READONLY, wxDefaultValidator, "Interval");
	Interval->SetSizeHints(150, 24);
	grdFiles->Add(StationID, 1, wxEXPAND | wxALL);
	grdFiles->Add(Interval, 1, wxALIGN_RIGHT);
	sizer0->Add(grdFiles);


	wxArrayString asClass;
	asClass.Add("A");
	asClass.Add("B");
	asClass.Add("C");
	wxStaticBoxSizer* sizer1 = new wxStaticBoxSizer(wxVERTICAL, p, "Instruments and Uncertainty");
	sizer1->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	wxFlexGridSizer* grdInstruments = new wxFlexGridSizer(4, 9, 25, 15);
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, " ", wxDefaultPosition, wxSize(50, 24)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument ID",wxDefaultPosition,wxSize(150,72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument model", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument class", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "class Uncertainty (+/- %)", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Calibration Uncertainty (+/- %)", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Calibration Date", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Due Date", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Radiometer Uncertainty (+/- %)", wxDefaultPosition, wxSize(100, 72)));
	GHIid = new wxTextCtrl(p, ID_GHIid, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIid");
	GHIid->SetSizeHints(150, 24);
	GHImodel = new wxTextCtrl(p, ID_GHImodel, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHImodel");
	GHImodel->SetSizeHints(75, 24);
	GHIclass = new wxComboBox(p, ID_GHIclass, "A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "GHIclass");
	GHIclass->SetSizeHints(50, 24);
	GHIclassUncert = new wxTextCtrl(p, ID_GHIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIclassUncert");
	GHIclassUncert->SetSizeHints(50, 24);
	GHIcalUncert = new wxTextCtrl(p, ID_GHIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIcalUncert");
	GHIcalUncert->SetSizeHints(50, 24);
	GHIcalDate = new wxTextCtrl(p, ID_GHIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIcalDate");
	GHIcalDate->SetSizeHints(100, 24);
	GHIdueDate = new wxTextCtrl(p, ID_GHIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIdueDate");
	GHIdueDate->SetSizeHints(100, 24);
	GHIradUncert = new wxTextCtrl(p, ID_GHIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIradUncert");
	GHIradUncert->SetSizeHints(50, 24);
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "GHI", wxDefaultPosition, wxSize(50, 24)),1,wxALIGN_RIGHT,2);
	grdInstruments->Add(GHIid);
	grdInstruments->Add(GHImodel);
	grdInstruments->Add(GHIclass);
	grdInstruments->Add(GHIclassUncert);
	grdInstruments->Add(GHIcalUncert);
	grdInstruments->Add(GHIcalDate);
	grdInstruments->Add(GHIdueDate);
	grdInstruments->Add(GHIradUncert);
	DNIid = new wxTextCtrl(p, ID_DNIid, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIid");
	DNIid->SetSizeHints(150, 24);
	DNImodel = new wxTextCtrl(p, ID_DNImodel,wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNImodel");
	DNImodel->SetSizeHints(75, 24);
	DNIclass = new wxComboBox(p, ID_DNIclass,"A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "DNIclass");
	DNIclass->SetSizeHints(50, 24);
	DNIclassUncert = new wxTextCtrl(p, ID_DNIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIclassUncert");
	DNIclassUncert->SetSizeHints(50, 24);
	DNIcalUncert = new wxTextCtrl(p, ID_DNIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIcalUncert");
	DNIcalUncert->SetSizeHints(50, 24);
	DNIcalDate = new wxTextCtrl(p, ID_DNIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIcalDate");
	DNIcalDate->SetSizeHints(100, 24);
	DNIdueDate = new wxTextCtrl(p, ID_DNIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIdueDate");
	DNIdueDate->SetSizeHints(100, 24);
	DNIradUncert = new wxTextCtrl(p, ID_DNIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIradUncert");
	DNIradUncert->SetSizeHints(50, 24);
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "DNI", wxDefaultPosition, wxSize(50, 24)), 1, wxALIGN_RIGHT, 2);
	grdInstruments->Add(DNIid);
	grdInstruments->Add(DNImodel);
	grdInstruments->Add(DNIclass);
	grdInstruments->Add(DNIclassUncert);
	grdInstruments->Add(DNIcalUncert);
	grdInstruments->Add(DNIcalDate);
	grdInstruments->Add(DNIdueDate);
	grdInstruments->Add(DNIradUncert);
	DHIid = new wxTextCtrl(p, ID_DHIid, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIid");
	DHIid->SetSizeHints(150, 24);
	DHImodel = new wxTextCtrl(p, ID_DHImodel, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHImodel");
	DHImodel->SetSizeHints(75, 24);
	DHIclass = new wxComboBox(p, ID_DHIclass, "A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "DHIclass");
	DHIclass->SetSizeHints(50, 24);
	DHIclassUncert = new wxTextCtrl(p, ID_DHIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIclassUncert");
	DHIclassUncert->SetSizeHints(50, 24);
	DHIcalUncert = new wxTextCtrl(p, ID_DHIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIcalUncert");
	DHIcalUncert->SetSizeHints(50, 24);
	DHIcalDate = new wxTextCtrl(p, ID_DHIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIcalDate");
	DHIcalDate->SetSizeHints(100, 24);
	DHIdueDate = new wxTextCtrl(p, ID_DHIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIdueDate");
	DHIdueDate->SetSizeHints(100, 24);
	DHIradUncert = new wxTextCtrl(p, ID_DHIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIradUncert");
	DHIradUncert->SetSizeHints(50, 24);
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "DHI", wxDefaultPosition, wxSize(50, 24)), 1, wxALIGN_RIGHT, 2);
	grdInstruments->Add(DHIid);
	grdInstruments->Add(DHImodel);
	grdInstruments->Add(DHIclass);
	grdInstruments->Add(DHIclassUncert);
	grdInstruments->Add(DHIcalUncert);
	grdInstruments->Add(DHIcalDate);
	grdInstruments->Add(DHIdueDate);
	grdInstruments->Add(DHIradUncert);

	sizer1->Add(grdInstruments, 1, wxEXPAND | wxALL, 5);

	wxStaticBoxSizer* sizer2 = new wxStaticBoxSizer(wxVERTICAL, p, "Defaults");
	sizer2->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	wxBoxSizer* szH1 = new wxBoxSizer(wxHORIZONTAL);
	szH1->Add(new wxStaticText(p, wxID_ANY, "Maximum SERI QC Flag", wxDefaultPosition, wxSize(250, 24),wxALIGN_RIGHT));
	szH1->AddSpacer(10);
	MaxQC = new wxTextCtrl(p, ID_MaxQC, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "MaxQC");
	MaxQC->SetSizeHints(75, 24);
	szH1->Add(MaxQC);
	sizer2->Add(szH1, 1, wxALIGN_CENTER, 5);
	wxBoxSizer* szH2 = new wxBoxSizer(wxHORIZONTAL);
	szH2->Add(new wxStaticText(p, wxID_ANY, "Minimum DNI (W/m^2)", wxDefaultPosition, wxSize(250, 24), wxALIGN_RIGHT));
	szH2->AddSpacer(10);
	MinDNI = new wxTextCtrl(p, ID_MinDNI, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "MinDNI");
	MinDNI->SetSizeHints(75, 24);
	szH2->Add(MinDNI);
	sizer2->Add(szH2, 1, wxALIGN_CENTER, 5);
	wxBoxSizer* szH3 = new wxBoxSizer(wxHORIZONTAL);
	szH3->Add(new wxStaticText(p, wxID_ANY, "Maximum Zenith (deg)", wxDefaultPosition, wxSize(250, 24), wxALIGN_RIGHT));
	szH3->AddSpacer(10);
	MaxZEN = new wxTextCtrl(p, ID_MaxZEN, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "MaxZEN");
	MaxZEN->SetSizeHints(75, 24);
	szH3->Add(MaxZEN);
	sizer2->Add(szH3, 1, wxALIGN_CENTER, 5);
	wxBoxSizer* szH4 = new wxBoxSizer(wxHORIZONTAL);
	szH4->Add(new wxStaticText(p, wxID_ANY, "Create Extended Report", wxDefaultPosition, wxSize(250, 24), wxALIGN_RIGHT));
	szH4->AddSpacer(10);
	ExtendedRpt = new wxCheckBox(p, ID_ExtendedRpt, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "ExtendedRpt");
	ExtendedRpt->SetSizeHints(75, 24);
	szH4->Add(ExtendedRpt);
	sizer2->Add(szH4, 1, wxALIGN_CENTER, 5);
	wxBoxSizer* szH5 = new wxBoxSizer(wxHORIZONTAL);
	szH5->Add(new wxStaticText(p, wxID_ANY, "Date format:", wxDefaultPosition, wxSize(150, 24), wxALIGN_RIGHT));
	szH5->AddSpacer(10);
	wxArrayString asDateFormat;
	asDateFormat.Add("YYYY-MM-DD");
	asDateFormat.Add("MM/DD/YYYY");
	DateFormat0 = new wxRadioButton(p, ID_DateFormat1, asDateFormat[0], wxDefaultPosition, wxDefaultSize, wxRB_GROUP, wxDefaultValidator, "DateFormat");
	DateFormat0->SetSizeHints(150, 24);
	szH5->Add(DateFormat0);
	DateFormat1 = new wxRadioButton(p, ID_DateFormat2, asDateFormat[1], wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DateFormat");
	DateFormat1->SetSizeHints(150, 24);
	szH5->Add(DateFormat1);
	sizer2->Add(szH5, 1, wxALIGN_CENTER, 5);



	wxStaticBoxSizer* sizer3 = new wxStaticBoxSizer(wxVERTICAL, p, "Processing");
	sizer3->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	wxBoxSizer* szButtons = new wxBoxSizer(wxHORIZONTAL);
	m_bStart = new wxButton(p, ID_BTN_START, "Start");
	m_bStart->SetSizeHints(75, 24);
	szButtons->Add(m_bStart);
	szButtons->AddSpacer(10);
	m_bCancel = new wxButton(p, ID_BTN_CANCEL, "Cancel");
	m_bCancel->SetSizeHints(75, 24);
	szButtons->Add(m_bCancel);
	sizer3->Add(szButtons, 1, wxALIGN_CENTER, 25);
	m_gProgress = new wxGauge(p, ID_PROGRESS, 100, wxDefaultPosition, wxDefaultSize, wxGA_HORIZONTAL);
	m_gProgress->SetSizeHints(1000, 24);
	sizer3->Add(m_gProgress, 1, wxEXPAND, 2);
	wxBoxSizer* szPercent = new wxBoxSizer(wxHORIZONTAL);
	szPercent->Add(new wxStaticText(p, wxID_ANY, "0"));
	szPercent->AddStretchSpacer();
	szPercent->Add(new wxStaticText(p, wxID_ANY, "Percent Complete"));
	szPercent->AddStretchSpacer();
	szPercent->Add(new wxStaticText(p, wxID_ANY, "100"));
	szPercent->SetSizeHints(m_gProgress);
	sizer3->Add(szPercent, 1, wxEXPAND, 2);


	// add both columns to grid sizer
	wxFlexGridSizer* sizerTop = new wxFlexGridSizer(2, 2, wxSize(50, 50));
	sizerTop->Add(sizer0, 1, wxEXPAND, 30);
	sizerTop->Add(sizer1, 1, wxEXPAND, 3);
	sizerTop->Add(sizer2, 1, wxEXPAND, 3);
	sizerTop->Add(sizer3, 1, wxEXPAND, 3);
	sizerTop->AddGrowableCol(1);

	// testing progress bar
	m_gProgress->Pulse();

	p->SetSizer(sizerTop);
	sizerTop->SetSizeHints(this);
}



wxString MainWindow::GetProjectDisplayName()
{
	if ( m_projectFileName.IsEmpty() ) return wxT("untitled");
	else return m_projectFileName;
}

wxString MainWindow::GetProjectFileName()
{
	return m_projectFileName;
}

void MainWindow::OnInternalCommand( wxCommandEvent &evt )
{
	switch (evt.GetId())
	{
	case ID_INTERNAL_DATAFOLDER:
		wxLaunchDefaultBrowser(SUIApp::GetUserLocalDataDir());
		break;
	}
}

bool MainWindow::OpenConfiguration(const wxString& filename)
{
	bool ret = false;
	// iterate over contols and populate from JSON file
	if (wxFileExists(filename)) {
		rapidjson::Document doc, table;
		wxFileInputStream fis(filename);

		if (!fis.IsOk()) {
			wxLogError(wxS("Couldn't open the file '%s'."), filename);
			return false;
		}
		wxStringOutputStream os;
		fis.Read(os);

		rapidjson::StringStream is(os.GetString().c_str());

		doc.ParseStream(is);
		if (doc.HasParseError()) {
			wxLogError(wxS("Could not read the json file string conversion '%s'."), filename);
			return false;
		}
		else {
			bool ret = true;
			// limit on wxRadioButton - only one group supported (if more desired use wxRadioBox)
			int iRadioGroup = 0;
			for (auto &widget : p->GetChildren()) {
				auto ci = widget->GetClassInfo();
				wxString typeName = ci->GetClassName();
				wxString widgetName = widget->GetName();
				if (doc.FindMember(widgetName.c_str()) != doc.MemberEnd()) {
					auto jValue = doc.FindMember(widgetName.c_str());
					// set value based on type
					if (typeName == "wxTextCtrl") {
						wxString val;
						if (jValue->value.IsDouble())
							val = wxString::Format("%g", jValue->value.GetDouble());
						else if (jValue->value.IsInt())
							val = wxString::Format("%d", jValue->value.GetInt());
						else if (jValue->value.IsString())
							val = jValue->value.GetString();
						else
							ret = false;// throw error?
						((wxTextCtrl*)widget)->SetValue(val);
					}
					else if (typeName == "wxComboBox") {
						wxString val; // to handle "Interval" as integer in JSON
						if (jValue->value.IsDouble())
							val = wxString::Format("%g", jValue->value.GetDouble());
						else if (jValue->value.IsInt())
							val = wxString::Format("%d", jValue->value.GetInt());
						else if (jValue->value.IsString())
							val = jValue->value.GetString();
						else
							ret = false;// throw error?
						int iValue = ((wxComboBox*)widget)->FindString(val);
						if (iValue != wxNOT_FOUND)
							((wxComboBox*)widget)->SetSelection(iValue);
					}
					else if (typeName == "wxRadioButton") {
						if (jValue->value.IsInt()) {
							bool bVal = jValue->value.GetInt() == iRadioGroup;
							((wxRadioButton*)widget)->SetValue(bVal); // group or button testing
							iRadioGroup++;
						}
						else
							ret = false;// throw error?
					}
					else if (typeName == "wxCheckBox") {
						if (jValue->value.IsInt()) {
							bool bVal = jValue->value.GetInt() == 1;
							((wxCheckBox*)widget)->SetValue(bVal);
						}
						else
							ret = false;// throw error?
					}
				}
			}
			return ret;
		}

	}

	return ret;
}


bool MainWindow::SaveConfiguration(const wxString& filename)
{
	bool ret = true;
	// iterate over contols and save JSON file
	rapidjson::Document doc;
	doc.SetObject();

	// limit on wxRadioButton - only one group supported (if more desired use wxRadioBox)
	int iRadioGroup = 0;
	for (auto& widget : p->GetChildren()) {
		auto ci = widget->GetClassInfo();
		wxString typeName = ci->GetClassName();
		wxString widgetName = widget->GetName();
		rapidjson::Value jValue;
		// set value based on type
		if (typeName == "wxTextCtrl") {
			wxString val = ((wxTextCtrl*)widget)->GetValue();
			double dVal;
			int iVal;
			if (val.ToDouble(&dVal))
				jValue.SetDouble(dVal);
			else if (val.ToInt(&iVal))
				jValue.SetInt(iVal);
			else
				jValue.SetString(val.c_str(), doc.GetAllocator());
			doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());
		}
		else if (typeName == "wxComboBox") {
			wxString val = ((wxComboBox*)widget)->GetValue();
			double dVal;
			int iVal;
			if (val.ToDouble(&dVal))
				jValue.SetDouble(dVal);
			else if (val.ToInt(&iVal))
				jValue.SetInt(iVal);
			else
				jValue.SetString(val.c_str(), doc.GetAllocator());
			doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());
		}
		else if (typeName == "wxRadioButton") {
			if (((wxRadioButton*)widget)->GetValue()) {
				jValue.SetInt(iRadioGroup);
				doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());
			}
			else {
				iRadioGroup++;
			}
		}
		else if (typeName == "wxCheckBox") {
			if (((wxCheckBox*)widget)->GetValue()) {
				jValue.SetInt(1);
			}
			else {
				jValue.SetInt(0);
			}
			doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());
		}
		else
			ret = false;// throw error?
	}

	rapidjson::StringBuffer os;
	rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(os); // MSPT/MP 64MB JSON, 6.7MB txt, JSON Zip 242kB
	doc.Accept(writer);
	wxFFileOutputStream out(filename);
	out.Write(os.GetString(), os.GetSize());
	out.Close();
	return ret;
}


void MainWindow::OnCommand( wxCommandEvent &evt )
{

	switch( evt.GetId() )
	{
	case wxID_OPEN:
		{
			wxFileDialog dlg(this, "Open Configuration File", wxEmptyString, wxEmptyString, "Configuration Files (*.json)|*.json", wxFD_OPEN );
			if (dlg.ShowModal() == wxID_OK)
				if( !OpenConfiguration( dlg.GetPath() ) )
					wxMessageBox("Error opening configuration file:\n\n" + dlg.GetPath() + "\n\n", "Notice", wxOK, this );
		}
		break;
	case wxID_SAVEAS:
		{
			wxFileDialog dlg(this, "Save Configuration File", wxEmptyString, wxEmptyString, "Configuration Files (*.json)|*.json", wxFD_SAVE | wxFD_OVERWRITE_PROMPT);
			if (dlg.ShowModal() == wxID_OK)
				if (!SaveConfiguration(dlg.GetPath()))
					wxMessageBox("Error saving configuration file:\n\n" + dlg.GetPath() + "\n\n", "Notice", wxOK, this);
		}
		break;
	case wxID_EXIT:
		Close();
		break;
	}
}



void MainWindow::OnClose( wxCloseEvent &evt )
{
	Raise();
	/*
	if ( !CloseProject() )
	{
		evt.Veto();
		return;
	}
	*/
	// save window position to settings
	wxRect rr;
	GetPosition( &rr.x,&rr.y );
	GetClientSize( &rr.width, &rr.height );
	SUIApp::Settings().Write( "window_x", rr.x);
	SUIApp::Settings().Write( "window_y", rr.y);
	SUIApp::Settings().Write( "window_width", rr.width);
	SUIApp::Settings().Write( "window_height", rr.height);
	SUIApp::Settings().Write( "window_maximized", IsMaximized() );

	
	// destroy the window
	wxGetApp().ScheduleForDestruction( this );
}


int SUIApp::OnExit()
{
	FileHistory().Save( Settings() );

	delete g_config;
//	wxLog::SetActiveTarget( 0 );
	return 0;
}

SUIApp::SUIApp()
{
}

wxString SUIApp::GetAppPath()
{
	wxFileName path( g_appArgs[0] );
	if ( !path.IsAbsolute() )
		path.MakeAbsolute();

	return wxPathOnly( path.GetFullPath() );
}

wxString SUIApp::GetRuntimePath()
{
	wxFileName path( GetAppPath() + "/../runtime/" );
	path.Normalize();
	return path.GetFullPath();
}

wxString SUIApp::GetUserLocalDataDir()
{
	wxString path = wxStandardPaths::Get().GetUserLocalDataDir();
	path.Replace("\\","/");

	if (!wxDirExists( path ))
		wxFileName::Mkdir( path, 511, wxPATH_MKDIR_FULL );

	return path;
}

wxConfig &SUIApp::Settings()
{
	if ( g_config == 0 ) throw SUIException( "g_config = NULL: internal error" );
	return *g_config;
}

MainWindow *SUIApp::Window()
{
	return g_mainWindow;
}



wxFileHistory &SUIApp::FileHistory()
{
static wxFileHistory s_fileHistory;
	return s_fileHistory;
}
wxArrayString SUIApp::RecentFiles()
{
	wxArrayString files;
	size_t n = FileHistory().GetCount();
	for ( size_t i=0;i<n;i++ )
		files.Add( FileHistory().GetHistoryFile( i ) );

	return files;
}

void SUIApp::ShowHelp( const wxString &context )
{
	wxString url;
	if ( context.Left(1) == ":" )
		url = context; // for things like :about, etc
	else
	{
		wxFileName fn( SUIApp::GetRuntimePath() + "/help/html/" );
		fn.MakeAbsolute();
		url = "file:///" + fn.GetFullPath( wxPATH_NATIVE ) + "index.html";
#ifdef __WXGTK__
		if ( ! context.IsEmpty() )
			url = "file:///" + fn.GetFullPath( wxPATH_NATIVE ) + context + ".html";
		wxLaunchDefaultBrowser( url );
		return;
#else
		if ( ! context.IsEmpty() )
			url += "?" + context + ".html";
#endif
	}

	wxWindow *modal_active = 0;
	wxWindow *nonmodal_tlw = 0;
	for( wxWindowList::iterator wl = wxTopLevelWindows.begin();
		wl != wxTopLevelWindows.end();
		++wl )
	{
		wxTopLevelWindow *tlw = dynamic_cast<wxTopLevelWindow*>( *wl );
		wxDialog *dia = dynamic_cast<wxDialog*>( *wl );

		if ( tlw != 0 && (dia == 0  || !dia->IsModal()) )
			nonmodal_tlw = tlw;

		if ( dia != 0 && dia->IsActive() && dia->IsModal() )
			modal_active = dia;
	}

	// try several different parent windows for the help window
	// if possible, use the SAM main window
	// otherwise, choose any top level window that is not modal
	// last resort, choose a currently modal dialog box
	wxWindow *parent = SUIApp::Window();
	if ( !parent ) parent = nonmodal_tlw;
	if ( !parent ) parent = modal_active;

}


bool SUIApp::OnInit()
{


		// apd : On windows, make sure process is DPI aware, regardless
		// of whether wxWidgets does this.  ref: http://trac.wxwidgets.org/ticket/16116
		// We don't use built-in icons or AUI, and rather have clean lines and text
		// rather than blurry look, now that UI pages can be made to scale (as of 8/24/2015)
#ifdef __WXMSW__
	typedef BOOL(WINAPI* SetProcessDPIAware_t)(void);
	wxDynamicLibrary dllUser32(wxT("user32.dll"));
	SetProcessDPIAware_t pfnSetProcessDPIAware =
		(SetProcessDPIAware_t)dllUser32.RawGetSymbol(wxT("SetProcessDPIAware"));
	if (pfnSetProcessDPIAware)
		pfnSetProcessDPIAware();
#endif


	// note: DO NOT CALL wxApp::Init() here, because
	// we want to do our own handling of command line
	// arguments.

//	wxMetroTheme::SetTheme( new SAMThemeProvider );
	// set app and vendor
	SetAppName("");
	SetVendorName("");

	
	for (int i = 0; i < argc; i++)
		g_appArgs.Add(argv[i]);

	if (g_appArgs.Count() < 1 || !wxDirExists(wxPathOnly(g_appArgs[0])))
	{
		wxMessageBox("Startup error - cannot determine application runtime folder from startup argument.\n\n"
			"Try running " + g_appArgs[0] + " by specifying the full path to the executable.");
		return false;
	}

	g_config = new wxConfig("SolarUncertaintyIntegrator", "NREL");// mem leak

	wxInitAllImageHandlers();



	FileHistory().Load(Settings());


	g_mainWindow = new MainWindow();
	SetTopWindow(g_mainWindow);
	g_mainWindow->Show();

	bool first_load = true;
	wxString fl_key = wxString::Format("first_load");
	Settings().Read(fl_key, &first_load, true);

	if (first_load)
	{
		// register the first load
		Settings().Write(fl_key, false);

	}
	else
	{
		// restore window position
		bool b_maximize = false;
		int f_x, f_y, f_width, f_height;
		Settings().Read("window_x", &f_x, -1);
		Settings().Read("window_y", &f_y, -1);
		Settings().Read("window_width", &f_width, -1);
		Settings().Read("window_height", &f_height, -1);
		Settings().Read("window_maximized", &b_maximize, false);

		if (b_maximize)
			g_mainWindow->Maximize();
		else
		{
			if (wxDisplay::GetFromPoint(wxPoint(f_x, f_y)) != wxNOT_FOUND)
			{
				if (f_width > 100 && f_height > 100)
					g_mainWindow->SetClientSize(f_width, f_height);

				if (f_x > 0 && f_y > 0)
					g_mainWindow->SetPosition(wxPoint(f_x, f_y));
			}
			else // place default here...
				g_mainWindow->Maximize();
		}
	}
	
	try {
		LoadPythonConfig();
	}
	catch (std::exception e) {
		SUIException ex(e.what());
		wxMessageBox(ex.what(),"Initialization error", wxICON_ERROR);
	}
	
	return true;
}




wxWindow *SUIApp::CurrentActiveWindow()
{
	wxWindowList &wl = ::wxTopLevelWindows;
	for( wxWindowList::iterator it = wl.begin(); it != wl.end(); ++it )
		if ( wxTopLevelWindow *tlw = dynamic_cast<wxTopLevelWindow*>( *it ) )
			if ( tlw->IsActive() )
				return tlw;

	return 0;
}


wxString SUIApp::ReadProxyFile()
{
	wxString proxy_file = SUIApp::GetAppPath() + "/proxy.txt";
	if ( wxFileExists( proxy_file ) )
	{
		if ( FILE *f = fopen(proxy_file.c_str(), "r") )
		{
			char buf[512];
			fgets(buf,511,f);
			fclose(f);
			return wxString::FromAscii(buf).Trim().Trim(false);
		}
	}

	return wxEmptyString;
}

bool SUIApp::WriteProxyFile( const wxString &proxy )
{
	wxString proxy_file = SUIApp::GetAppPath() + "/proxy.txt";
	if ( FILE *f = fopen(proxy_file.c_str(), "w") )
	{
		fprintf(f, "%s\n", (const char*)proxy.ToAscii() );
		fclose(f);
		return true;
	}
	else
		return false;
}

std::string SUIApp::GetPythonConfigPath(){
    wxFileName path( GetAppPath() + "/python" );
    path.Normalize();
    return path.GetFullPath().ToStdString();
}

void SUIApp::LoadPythonConfig(){
    pythonConfig = ReadPythonConfig(GetPythonConfigPath() + "/python_config.json");
    if (CheckPythonInstalled(pythonConfig)){
        std::string python_path = GetPythonConfigPath();
		set_python_path(python_path.c_str());
        return;
    }
}

bool SUIApp::CheckPythonPackage(const std::string& pip_name){
    if (CheckPythonInstalled(pythonConfig)){
        if (CheckPythonPackageInstalled(pip_name, pythonConfig))
            return true;
    }
    return false;
}

void SUIApp::InstallPython() {
    if (pythonConfig.pythonVersion.empty() && pythonConfig.minicondaVersion.empty())
        LoadPythonConfig();

    auto python_path = GetPythonConfigPath();
    // already installed and correctly configured
    if (CheckPythonInstalled(pythonConfig)){
		set_python_path(python_path.c_str());
        return;
    }

#ifdef __WXMSW__
    // windows
    bool errors = InstallPythonWindows(python_path, pythonConfig);
#else
    bool errors = InstallPythonUnix(python_path, pythonConfig);
#endif
    if (errors)
        throw std::runtime_error("Error installing python.");
    LoadPythonConfig();
}

void SUIApp::InstallPythonPackage(const std::string& pip_name) {
    if (CheckPythonPackageInstalled(pip_name, pythonConfig))
        return;
    auto packageConfig = ReadPythonPackageConfig(pip_name, GetPythonConfigPath() + "/" + pip_name + ".json");

#ifdef __WXMSW__
	bool retval = InstallFromPipWindows(GetPythonConfigPath() + "\\" + pythonConfig.pipPath, packageConfig);
#else
	std::string pip_exec = GetPythonConfigPath() + "/" + pythonConfig.pipPath;
	bool retval = InstallFromPip(pip_exec, packageConfig);
#endif
    if (retval == 0){
        pythonConfig.packages.push_back(pip_name);
        WritePythonConfig(GetPythonConfigPath() + "/python_config.json", pythonConfig);
    }
    else {
        throw std::runtime_error("Error installing " + pip_name);
    }
}



IMPLEMENT_APP( SUIApp );
