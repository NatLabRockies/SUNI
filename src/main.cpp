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
#include <regex>

#include <wx/wx.h>
#include <wx/scrolwin.h>
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
#include <wx/textfile.h>
#include <wx/calctrl.h>

#include "main.h"
#include "pythonhandler.h"
#include "csv.h"


#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/prettywriter.h" // for stringify JSON
#include "rapidjson/filereadstream.h"
#include "rapidjson/filewritestream.h"
#include "rapidjson/istreamwrapper.h"
#include "rapidjson/document.h"


#include <fstream>
#include <future>
#include <sstream>

#ifdef __WINDOWS__
#include <Windows.h>
#include <stdio.h>
#include <tchar.h>
#pragma warning(disable: 4191)
#include "AtlBase.h"
#include "AtlConv.h"
#endif


#ifdef _MSC_VER
#define popen _popen
#define pclose _pclose
#endif




static PythonConfig pythonConfig;


enum { __idFirst = wxID_HIGHEST+592,

	ID_BTN_INPUTFILE, ID_BTN_OUTPUTFILE, ID_BTN_SERIQCPATH,
	ID_TXT_INPUTFILE, ID_TXT_OUTPUTFILE, ID_TXT_SERIQCPATH,
	ID_INTERNAL_DATAFOLDER, ID_CMB_SERI_QC, ID_CMB_INTERVAL,
	ID_GHIid, ID_GHImodel, ID_GHIclass, ID_GHIclassUncert, ID_GHIcalUncert, ID_GHIcalDate, ID_GHIdueDate, ID_GHIradUncert,
	ID_DNIid, ID_DNImodel, ID_DNIclass, ID_DNIclassUncert, ID_DNIcalUncert, ID_DNIcalDate, ID_DNIdueDate, ID_DNIradUncert,
	ID_DHIid, ID_DHImodel, ID_DHIclass, ID_DHIclassUncert, ID_DHIcalUncert, ID_DHIcalDate, ID_DHIdueDate, ID_DHIradUncert,
	ID_MaxQC, ID_MinDNI, ID_MaxZEN, ID_DateFormat1, ID_DateFormat2, ID_ExtendedRpt, ID_BTN_START, ID_BTN_CANCEL, ID_PROGRESS, ID_CALENDAR, ID_NODATE
};



class MyMessageDialog : public wxDialog {
public:
	MyMessageDialog(wxWindow* parent,
		const wxString& message,
		const wxString& title,
		long buttons,
		const wxPoint& pos = wxDefaultPosition,
		const wxSize& size = wxDefaultSize,
		bool addButtonClose = false)
		: wxDialog(parent, wxID_ANY, title, pos, size, wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER) {
		SetEscapeId(wxID_NONE);

		wxPanel* panel = new wxPanel(this);
		panel->SetBackgroundColour(*wxWHITE);

		wxBoxSizer* szpnl = new wxBoxSizer(wxVERTICAL);

		int wrap = 600;
		if (size != wxDefaultSize && size.x > 100)
			wrap = size.x - 40;

		int nlpos = message.Find('\n');
		if (nlpos > 0) {
			wxStaticText* label1 = new wxStaticText(panel, wxID_ANY, message.Left(nlpos), wxDefaultPosition,
				wxDefaultSize, wxALIGN_LEFT);
			wxFont font(label1->GetFont());
			font.SetPointSize(font.GetPointSize() + 2);
			label1->SetFont(font);
			label1->SetForegroundColour(wxColour(0, 0, 120));
			label1->Wrap(wrap);

			wxStaticText* label2 = new wxStaticText(panel, wxID_ANY, message.Mid(nlpos + 1), wxDefaultPosition,
				wxDefaultSize, wxALIGN_LEFT);
			label2->Wrap(wrap);

			szpnl->Add(label1, 0, wxTOP | wxLEFT | wxRIGHT | wxEXPAND, 20);
			szpnl->Add(label2, 1, wxALL | wxEXPAND, 20);
		}
		else {
			wxStaticText* label = new wxStaticText(panel, wxID_ANY, message, wxDefaultPosition, wxDefaultSize,
				wxALIGN_LEFT);
			label->Wrap(wrap);

			szpnl->Add(label, 1, wxALL | wxEXPAND, 20);
		}

		if (addButtonClose) {
			wxButton* buttonClose = new wxButton(this, wxID_OK, wxT("OK"));
			szpnl->Add(buttonClose, 1, wxCENTER);
		}

		panel->SetSizer(szpnl);

		wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
		sizer->Add(panel, 1, wxALL | wxEXPAND, 0);
		sizer->Add(CreateButtonSizer(buttons), 0, wxALL | wxEXPAND, 11);


		SetSizerAndFit(sizer);

		if (size != wxDefaultSize)
			SetClientSize(size);
		else {
			wxSize sz = GetClientSize();
			if (sz.x < 340) sz.x = 340;
			if (sz.y < 120) sz.y = 120;
			SetClientSize(sz);
		}

		if (pos == wxDefaultPosition) {
			if (parent)
				CenterOnParent();
			else
				CenterOnScreen();
		}
		Layout();
	}
	void Initialize() {
		Layout();
		Refresh();
	}

	void OnClose(wxCloseEvent&) {
		EndModal(wxID_CANCEL);
	}

	void OnCharHook(wxKeyEvent& evt) {
		if (evt.GetKeyCode() == WXK_ESCAPE)
			EndModal(wxID_CANCEL);
	}

	void OnCommand(wxCommandEvent& evt) {
		EndModal(evt.GetId());
	}
};




class CalendarDialog : public wxDialog
{
public:
	CalendarDialog(wxWindow* parent, wxWindowID id, const wxPoint pos, const wxDateTime& dt, const int& dateFormat) : wxDialog(parent, id, "Select Date", pos), m_dt(dt), m_dateFormat(dateFormat)
	{
		wxBoxSizer* vs = new wxBoxSizer(wxVERTICAL);
		m_calendar = new wxCalendarCtrl(this, ID_CALENDAR, m_dt);
		vs->Add(m_calendar, 1, wxEXPAND | wxALL, 1);
		wxBoxSizer* bs = new wxBoxSizer(wxHORIZONTAL);
		bs->Add(new wxButton(this, ID_NODATE, "Blank"), 1, wxEXPAND, 1);
		bs->Add(new wxButton(this, wxID_OK, "OK"), 1, wxEXPAND, 1);
		bs->Add(new wxButton(this, wxID_CANCEL, "Cancel"), 1, wxEXPAND, 1);
		vs->Add(bs);
		SetSizerAndFit(vs);
	}
	const wxString &GetDate() { return m_dtstr; }
private:
	wxCalendarCtrl* m_calendar;
	wxDateTime m_dt;
	int m_dateFormat;
	wxString m_dtstr;

	void OnCommand(wxCommandEvent& evt) {
		switch (evt.GetId()) {
		case ID_NODATE:
			m_dtstr = "";
			break;
		}
	};
	void OnCalendar(wxCalendarEvent& evt) {
		m_dt = evt.GetDate();
		if (m_dateFormat == 1)
			m_dtstr = m_dt.FormatISODate();
		else
			m_dtstr = m_dt.Format(wxString::FromAscii("%m/%d/%Y"));
	}

	DECLARE_EVENT_TABLE();
};



BEGIN_EVENT_TABLE(CalendarDialog, wxDialog)
EVT_BUTTON(ID_NODATE, CalendarDialog::OnCommand)
EVT_CALENDAR_SEL_CHANGED(ID_CALENDAR, CalendarDialog::OnCalendar)
//	EVT_CALENDAR(ID_CALENDAR, CalendarDialog::OnCalendar)
END_EVENT_TABLE()




BEGIN_EVENT_TABLE( MainWindow, wxFrame )
	EVT_CLOSE(MainWindow::OnClose)
	EVT_IDLE(MainWindow::OnIdle)
//	EVT_ACTIVATE(MainWindow::OnActivate)
//	EVT_SET_FOCUS(MainWindow::OnSetFocus)
	EVT_MENU( wxID_ABOUT, MainWindow::OnCommand )
	EVT_MENU( wxID_HELP, MainWindow::OnCommand )
	EVT_MENU(wxID_OPEN, MainWindow::OnCommand)
	EVT_MENU( wxID_SAVE, MainWindow::OnCommand )
	EVT_MENU( wxID_SAVEAS, MainWindow::OnCommand )
	EVT_MENU( wxID_CLOSE, MainWindow::OnCommand )
	EVT_MENU(wxID_EXIT, MainWindow::OnCommand)
	EVT_BUTTON(ID_BTN_START, MainWindow::OnCommand)
	EVT_BUTTON(ID_BTN_CANCEL, MainWindow::OnCommand)
	EVT_BUTTON(ID_BTN_INPUTFILE, MainWindow::OnCommand)
	EVT_BUTTON(ID_BTN_OUTPUTFILE, MainWindow::OnCommand)
	EVT_BUTTON(ID_BTN_SERIQCPATH, MainWindow::OnCommand)
	EVT_TEXT(ID_TXT_SERIQCPATH, MainWindow::OnCommand)
	EVT_TEXT(ID_GHIclassUncert, MainWindow::UpdateGHIUncertainty)
	EVT_TEXT(ID_GHIcalUncert, MainWindow::OnGHICalUncertainty)
	EVT_TEXT(ID_DNIclassUncert, MainWindow::UpdateDNIUncertainty)
	EVT_TEXT(ID_DNIcalUncert, MainWindow::OnDNICalUncertainty)
	EVT_TEXT(ID_DHIclassUncert, MainWindow::UpdateDHIUncertainty)
	EVT_TEXT(ID_DHIcalUncert, MainWindow::OnDHICalUncertainty)
	EVT_COMBOBOX(ID_GHIclass, MainWindow::UpdateClassCalGHIUncertainty)
	EVT_COMBOBOX(ID_DHIclass, MainWindow::UpdateClassCalDHIUncertainty)
	EVT_COMBOBOX(ID_DNIclass, MainWindow::UpdateClassCalDNIUncertainty)
	EVT_RADIOBUTTON(ID_DateFormat1, MainWindow::OnDateFormat)
	EVT_RADIOBUTTON(ID_DateFormat2, MainWindow::OnDateFormat)
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
	// for JSON type loading and saving
	m_typeInt = { "DateFormat","ExtendedRRpt", "MaxQC", "Interval"};
	m_typeDouble = {"GHIclassUncert", "GHIcalUncert", "GHIradUncert","DNIclassUncert", "DNIcalUncert", "DNIradUncert","DHIclassUncert", "DHIcalUncert", "DHIradUncert", "MinDNI", "MaxZEN"};

	m_mainMenuBar = new wxMenuBar;
	m_pythonInstalled = false;

	wxMenu *menu = new wxMenu ;
	menu->Append(wxID_SAVEAS, "Save Configuration");
	menu->Append(wxID_OPEN, "Open Configuration");
	menu->Append(wxID_EXIT, "Close");

	m_mainMenuBar->Append(menu, wxT("&File"));

	SetMenuBar(m_mainMenuBar);

	p = new wxScrolledWindow(this, wxID_ANY);

	wxStaticBoxSizer* sizer0 = new wxStaticBoxSizer(wxVERTICAL,p, "Files");
	//sizer0->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
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
	SERIQCpath = new wxTextCtrl(p, ID_TXT_SERIQCPATH, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "SERIQCpath");
	SERIQCpath->SetSizeHints(500, 24);
	sizer0->Add(SERIQCpath, 1, wxEXPAND | wxALL, 5);
	wxGridSizer* grdFiles = new wxGridSizer(2, 2, 2, 5);
	grdFiles->Add(new wxStaticText(p, wxID_ANY, "SERI QC Station ID"));
	grdFiles->Add(new wxStaticText(p, wxID_ANY, "Interval (minutes)"),1, wxALIGN_RIGHT);
	wxArrayString asStationID;
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
	//sizer1->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	wxFlexGridSizer* grdInstruments = new wxFlexGridSizer(4, 9, 25, 15);
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, " ", wxDefaultPosition, wxSize(50, 24)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument ID",wxDefaultPosition,wxSize(150,72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument model", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Instrument class", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Class Uncertainty (+/- %)", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Calibration Uncertainty (+/- %)", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Calibration Date", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Due Date", wxDefaultPosition, wxSize(75, 72)));
	grdInstruments->Add(new wxStaticText(p, wxID_ANY, "Radiometer Uncertainty (+/- %)", wxDefaultPosition, wxSize(100, 72)));
	GHIid = new wxTextCtrl(p, ID_GHIid, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIid");
	GHIid->SetSizeHints(150, 24);
	GHImodel = new wxTextCtrl(p, ID_GHImodel, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHImodel");
	GHImodel->SetSizeHints(150, 24);
	GHIclass = new wxComboBox(p, ID_GHIclass, "A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "GHIclass");
	GHIclass->SetSizeHints(50, 24);
	GHIclassUncert = new wxTextCtrl(p, ID_GHIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "GHIclassUncert");
	GHIclassUncert->SetSizeHints(50, 24);
	GHIcalUncert = new wxTextCtrl(p, ID_GHIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "GHIcalUncert");
	GHIcalUncert->SetSizeHints(50, 24);
	GHIcalDate = new wxTextCtrl(p, ID_GHIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "GHIcalDate");
	GHIcalDate->SetSizeHints(100, 24);
	GHIcalDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	GHIdueDate = new wxTextCtrl(p, ID_GHIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "GHIdueDate");
	GHIdueDate->SetSizeHints(100, 24);
	GHIdueDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	GHIradUncert = new wxTextCtrl(p, ID_GHIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "GHIradUncert");
	GHIradUncert->SetSizeHints(100, 24);
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
	DNImodel->SetSizeHints(150, 24);
	DNIclass = new wxComboBox(p, ID_DNIclass,"A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "DNIclass");
	DNIclass->SetSizeHints(50, 24);
	DNIclassUncert = new wxTextCtrl(p, ID_DNIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DNIclassUncert");
	DNIclassUncert->SetSizeHints(50, 24);
	DNIcalUncert = new wxTextCtrl(p, ID_DNIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DNIcalUncert");
	DNIcalUncert->SetSizeHints(50, 24);
	DNIcalDate = new wxTextCtrl(p, ID_DNIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DNIcalDate");
	DNIcalDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	DNIcalDate->SetSizeHints(100, 24);
	DNIdueDate = new wxTextCtrl(p, ID_DNIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DNIdueDate");
	DNIdueDate->SetSizeHints(100, 24);
	DNIdueDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	DNIradUncert = new wxTextCtrl(p, ID_DNIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DNIradUncert");
	DNIradUncert->SetSizeHints(100, 24);
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
	DHImodel->SetSizeHints(150, 24);
	DHIclass = new wxComboBox(p, ID_DHIclass, "A", wxDefaultPosition, wxDefaultSize, asClass, wxCB_READONLY, wxDefaultValidator, "DHIclass");
	DHIclass->SetSizeHints(50, 24);
	DHIclassUncert = new wxTextCtrl(p, ID_DHIclassUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DHIclassUncert");
	DHIclassUncert->SetSizeHints(50, 24);
	DHIcalUncert = new wxTextCtrl(p, ID_DHIcalUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DHIcalUncert");
	DHIcalUncert->SetSizeHints(50, 24);
	DHIcalDate = new wxTextCtrl(p, ID_DHIcalDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DHIcalDate");
	DHIcalDate->SetSizeHints(100, 24);
	DHIcalDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	DHIdueDate = new wxTextCtrl(p, ID_DHIdueDate, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DHIdueDate");
	DHIdueDate->SetSizeHints(100, 24);
	DHIdueDate->Connect(wxEVT_LEFT_DOWN, wxMouseEventHandler(MainWindow::OnDateClick), NULL, this);
	DHIradUncert = new wxTextCtrl(p, ID_DHIradUncert, wxEmptyString, wxDefaultPosition, wxDefaultSize, wxTE_READONLY, wxDefaultValidator, "DHIradUncert");
	DHIradUncert->SetSizeHints(100, 24);
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
	//sizer2->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
	wxBoxSizer* szH1 = new wxBoxSizer(wxHORIZONTAL);
	szH1->Add(new wxStaticText(p, wxID_ANY, "Maximum SERI QC Flag", wxDefaultPosition, wxSize(250, 24),wxALIGN_RIGHT));
	szH1->AddSpacer(10);
	//MaxQC = new wxTextCtrl(p, ID_MaxQC, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "MaxQC");
	// see p.32 of version 2 specifications. Updated per email 1/29/2024 from Steve Wilcox
	wxArrayString asMaxQC;
//	asMaxQC.Add("3");
	for (int i = 13; i <= 89; i=i+4)
		asMaxQC.Add(wxString::FromDouble(i));
//	asMaxQC.Add("87");
	MaxQC = new wxComboBox(p, ID_DHIclass, "89", wxDefaultPosition, wxDefaultSize, asMaxQC, wxCB_READONLY, wxDefaultValidator, "MaxQC");
	MaxQC->SetSizeHints(75, 30);
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
	asDateFormat.Add("MM/DD/YYYY");
	asDateFormat.Add("YYYY-MM-DD");
	DateFormat0 = new wxRadioButton(p, ID_DateFormat1, asDateFormat[0], wxDefaultPosition, wxDefaultSize, wxRB_GROUP, wxDefaultValidator, "DateFormat");
	DateFormat0->SetSizeHints(150, 24);
	szH5->Add(DateFormat0);
	DateFormat1 = new wxRadioButton(p, ID_DateFormat2, asDateFormat[1], wxDefaultPosition, wxDefaultSize, 0L, wxDefaultValidator, "DateFormat");
	DateFormat1->SetSizeHints(150, 24);
	szH5->Add(DateFormat1);
	sizer2->Add(szH5, 1, wxALIGN_CENTER, 5);



	wxStaticBoxSizer* sizer3 = new wxStaticBoxSizer(wxVERTICAL, p, "Processing");
	//sizer3->GetStaticBox()->SetWindowStyleFlag(wxSIMPLE_BORDER);
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
//	wxFlexGridSizer* sizerTop = new wxFlexGridSizer(2, 2, wxSize(50, 50));
	wxBoxSizer* sizerTop = new wxBoxSizer(wxVERTICAL);
	sizerTop->AddSpacer(10);
	sizerTop->Add(sizer0, 1, wxEXPAND, 5);
	sizerTop->AddSpacer(15);
	sizerTop->Add(sizer1, 1, wxEXPAND, 5);
	sizerTop->AddSpacer(15);
	sizerTop->Add(sizer2, 1, wxEXPAND, 5);
	sizerTop->AddSpacer(15);
	sizerTop->Add(sizer3, 1, wxEXPAND, 5);

	m_gProgress->SetValue(0);

	m_bCancel->Enable(false);
	m_cancelled = false;


	p->SetSizer(sizerTop);
	p->FitInside();
	p->SetScrollRate(5, 5);
//	sizerTop->SetSizeHints(this);

	wxBoxSizer* sizer = new wxBoxSizer(wxHORIZONTAL);
	sizer->Add(p, 1, wxEXPAND);
	this->SetSizer(sizer);

	// long initialization of Python
	//Layout();
	//SetupPython();
}

void MainWindow::OnDateClick(wxMouseEvent& event)
{
	wxTextCtrl* text = wxStaticCast(event.GetEventObject(), wxTextCtrl);
	wxDateTime dt;
	dt.ParseDate(text->GetValue());

	int dateFormat = 0;
	if (DateFormat1->GetValue()) {
		dateFormat = 1;
	}
	else {
		dateFormat = 0;
	}

	auto pos = event.GetPosition();
	pos = text->ClientToScreen(pos);

	CalendarDialog* dlg = new CalendarDialog(this, wxID_ADD, pos, dt, dateFormat);
	if (dlg->ShowModal() == wxID_OK) {
		text->SetValue(dlg->GetDate());
	}

}

void MainWindow::OnActivate(wxActivateEvent& evt)
{
	if (evt.GetActive())
		SetupPython();
}

void MainWindow::OnSetFocus(wxFocusEvent& evt)
{
	SetupPython();
	evt.Skip();
}

wxWindow* GetCurrentTopLevelWindow() {
	wxWindowList& wl = ::wxTopLevelWindows;
	for (wxWindowList::iterator it = wl.begin(); it != wl.end(); ++it)
		if (wxTopLevelWindow* tlw = dynamic_cast<wxTopLevelWindow*>(*it))
			if (tlw->IsShown() && tlw->IsActive())
				return tlw;

	return 0;
}


void MainWindow::OnIdle(wxIdleEvent& evt)
{
	if (!m_pythonInstalled) {
		if (CheckPythonPackage("suni"))
			m_pythonInstalled = true;
		else {
			wxBusyCursor wait;
			MyMessageDialog dlg(this, "Installing the SUNI model.\nPlease note that it may take a few minutes to complete the initial installation.\nOnce installed, you will be able to estimate the solar uncertainty using the 'Start' button.", "Solar Uncertainty Integrator", wxCENTER);
			dlg.Show();
			wxGetApp().SafeYieldFor(& dlg, true);
			InstallPython();
			InstallPythonPackage("suni");
			dlg.Close();
			m_pythonInstalled = true;
		}
	}
	m_bStart->Enable(CheckInputs());
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

void MainWindow::SetProjectFileName(const wxString& fn)
{
	m_projectFileName = fn;
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

bool MainWindow::CheckInputs()
{
	bool ret = true;
	for (auto& widget : p->GetChildren()) {
		auto ci = widget->GetClassInfo();
		wxString typeName = ci->GetClassName();
		wxString widgetName = widget->GetName();
		if (typeName == "wxTextCtrl") {
			// dates can be blank
			if (widgetName.Lower().Find("date") == wxNOT_FOUND)
				ret = ret && (((wxTextCtrl*)widget)->GetValue().length() > 0);
		}
		else if (typeName == "wxComboBox") {
			ret = ret && (((wxComboBox*)widget)->GetValue().length() > 0);
		}
	}
	return ret;

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
			ret = true;
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
						if (m_typeDouble.Index(widgetName) != wxNOT_FOUND)//(jValue->value.IsDouble())
							val = wxString::Format("%g", jValue->value.GetDouble());
						else if (m_typeInt.Index(widgetName) != wxNOT_FOUND)//(jValue->value.IsInt())
							val = wxString::Format("%d", jValue->value.GetInt());
						else //if (jValue->value.IsString())
							val = jValue->value.GetString();
						//else
						//	ret = false;// throw error?
						if (((wxTextCtrl*)widget)->IsEditable())
							((wxTextCtrl*)widget)->SetValue(val);
						else
							((wxTextCtrl*)widget)->ChangeValue(val);
					}
					else if (typeName == "wxComboBox") {
						wxString val; // to handle "Interval" as integer in JSON
						if (m_typeDouble.Index(widgetName) != wxNOT_FOUND)//(jValue->value.IsDouble())
							val = wxString::Format("%g", jValue->value.GetDouble());
						else if (m_typeInt.Index(widgetName) != wxNOT_FOUND)//(jValue->value.IsInt())
							val = wxString::Format("%d", jValue->value.GetInt());
						else //if (jValue->value.IsString())
							val = jValue->value.GetString();
						//else
						//	ret = false;// throw error?
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



bool MainWindow::FormatAllDates(const int& dateFormat) {
	FormatTextCtrl(GHIcalDate, dateFormat);
	FormatTextCtrl(GHIdueDate, dateFormat);
	FormatTextCtrl(DHIcalDate, dateFormat);
	FormatTextCtrl(DHIdueDate, dateFormat);
	FormatTextCtrl(DNIcalDate, dateFormat);
	FormatTextCtrl(DNIdueDate, dateFormat);
	return true;
}

bool MainWindow::FormatTextCtrl(wxTextCtrl* tc, const int& dateFormat)
{
	wxDateTime dt;
	wxString strdt;
	strdt = tc->GetValue();
	dt.ParseDate(strdt);
	if (dt.IsValid()) { // skip blank dates
		if (dateFormat == ID_DateFormat1)
			strdt = dt.Format(wxString::FromAscii("%m/%d/%Y"));
		else
			strdt = dt.FormatISODate();
		tc->SetValue(strdt);
	}
	return true;
}


void MainWindow::OnDateFormat(wxCommandEvent& evt)
{
	wxDateTime dt;
	wxString strdt;
	switch (evt.GetId()) {
		case ID_DateFormat1:
			FormatAllDates(ID_DateFormat1);
			break;
		case ID_DateFormat2:
			FormatAllDates(ID_DateFormat2);
			break;
	}
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
			if (m_typeDouble.Index(widgetName) != wxNOT_FOUND) 
				jValue = wxAtof(val);
			else if (m_typeInt.Index(widgetName) != wxNOT_FOUND)
				jValue = wxAtoi(val);
			else
				jValue.SetString(val.c_str(), doc.GetAllocator());
			doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());
		}
		else if (typeName == "wxComboBox") {
			wxString val = ((wxComboBox*)widget)->GetValue();
			if (m_typeDouble.Index(widgetName) != wxNOT_FOUND)
				jValue = wxAtof(val);
			else if (m_typeInt.Index(widgetName) != wxNOT_FOUND)
				jValue = wxAtoi(val);
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
//		else // like group boxes or static boxes - not a failure.
//			ret = false;// throw error?
	}
	// Add required MaxSysUncert that is not an input
	wxString widgetName = "MaxSysUncert";
	rapidjson::Value jValue;
	jValue = 100.0;
	doc.AddMember(rapidjson::Value(widgetName.c_str(), (rapidjson::SizeType)widgetName.size(), doc.GetAllocator()).Move(), jValue.Move(), doc.GetAllocator());


	rapidjson::StringBuffer os;
	rapidjson::PrettyWriter<rapidjson::StringBuffer> writer(os); 
	doc.Accept(writer);
	wxFFileOutputStream out(filename);
	out.Write(os.GetString(), os.GetSize());
	out.Close();
	return ret;
}

void MainWindow::GetInstrumentDataBaseUncertainties(const wxString& instClass, wxString* classUncert, wxString* calUncert )
{
	wxCSVData csv;
	wxFileName path(GetAppPath() + "/Instrument Files/Upyranometer.csv");
	path.Normalize();
	if (!csv.ReadFile(path.GetFullPath())) {
		wxMessageBox("Error opening instrument file:\n\n" + path.GetFullPath() + "\n\n", "Notice", wxOK, this);
		return;
	}
	size_t nr = csv.NumRows();
	size_t nc = csv.NumCols();
	if ((nr != 4) || (nc != 3)) {
		wxMessageBox("Error with instrument file:\n\n" + path.GetFullPath() + "\nnumber of (row, cols) incorrect - should be (4,3)\n", "Notice", wxOK, this);
		return;
	}
	for (size_t r = 0; r < nr; r++) {
		if (csv(r, 0).Lower() == instClass.Lower()) {
			*classUncert = csv(r, 1);
			*calUncert = csv(r, 2);
		}
	}
}


void MainWindow::UpdateClassCalGHIUncertainty(wxCommandEvent& evt)
{
	wxString instClass = GHIclass->GetValue();
	wxString classUncert = "";
	wxString calUncert = "";
	GetInstrumentDataBaseUncertainties(instClass, &classUncert, &calUncert);
	GHIclassUncert->SetValue(classUncert);
	GHIcalUncert->ChangeValue(calUncert);
	GHIcalUncert->SetBackgroundColour(*wxGREEN); // Database
	UpdateGHIUncertainty(evt);
}

void MainWindow::UpdateClassCalDHIUncertainty(wxCommandEvent& evt)
{
	wxString instClass = DHIclass->GetValue();
	wxString classUncert = "";
	wxString calUncert = "";
	GetInstrumentDataBaseUncertainties(instClass, &classUncert, &calUncert);
	DHIclassUncert->SetValue(classUncert);
	DHIcalUncert->ChangeValue(calUncert);
	DHIcalUncert->SetBackgroundColour(*wxGREEN); // Database
	UpdateDHIUncertainty(evt);
}

void MainWindow::UpdateClassCalDNIUncertainty(wxCommandEvent& evt)
{
	wxString instClass = DNIclass->GetValue();
	wxString classUncert = "";
	wxString calUncert = "";
	GetInstrumentDataBaseUncertainties(instClass, &classUncert, &calUncert);
	DNIclassUncert->SetValue(classUncert);
	DNIcalUncert->ChangeValue(calUncert);
	DNIcalUncert->SetBackgroundColour(*wxGREEN); // Database
	UpdateDNIUncertainty(evt);
}


void MainWindow::OnGHICalUncertainty(wxCommandEvent& evt)
{
	GHIcalUncert->SetBackgroundColour(*wxWHITE);
	UpdateGHIUncertainty(evt);
}

void MainWindow::OnDNICalUncertainty(wxCommandEvent& evt)
{
	DNIcalUncert->SetBackgroundColour(*wxWHITE);
	UpdateDNIUncertainty(evt);
}

void MainWindow::OnDHICalUncertainty(wxCommandEvent& evt)
{
	DHIcalUncert->SetBackgroundColour(*wxWHITE);
	UpdateDHIUncertainty(evt);
}


void MainWindow::UpdateGHIUncertainty(wxCommandEvent&)
{
	auto Uclass = GHIclassUncert->GetValue();
	auto Ucal = GHIcalUncert->GetValue();
	double dUclass, dUcal;
	if (Uclass.ToDouble(&dUclass) && Ucal.ToDouble(&dUcal)) {
		double Urad = sqrt(pow(dUclass, 2) + pow(dUcal, 2));
		GHIradUncert->SetValue(wxString::Format("%.2f",Urad));
	}
}

void MainWindow::UpdateDNIUncertainty(wxCommandEvent&)
{
	auto Uclass = DNIclassUncert->GetValue();
	auto Ucal = DNIcalUncert->GetValue();
	double dUclass, dUcal;
	if (Uclass.ToDouble(&dUclass) && Ucal.ToDouble(&dUcal)) {
		double Urad = sqrt(pow(dUclass, 2) + pow(dUcal, 2));
		DNIradUncert->SetValue(wxString::Format("%.2f", Urad));
	}
}

void MainWindow::UpdateDHIUncertainty(wxCommandEvent&)
{
	auto Uclass = DHIclassUncert->GetValue();
	auto Ucal = DHIcalUncert->GetValue();
	double dUclass, dUcal;
	if (Uclass.ToDouble(&dUclass) && Ucal.ToDouble(&dUcal)) {
		double Urad = sqrt(pow(dUclass, 2) + pow(dUcal, 2));
		DHIradUncert->SetValue(wxString::Format("%.2f", Urad));
	}
}

bool MainWindow::UpdateStationIDs(const wxString& dir)
{
	bool ret = true;

	if (!wxDirExists(dir)) {
		wxMessageBox("SERI QC path " + dir +  " does not exist.", "SERI QC Error", wxICON_ERROR);
		ret = false;
	}
	else {
		wxDir folder(dir);
		wxArrayString files;
		folder.GetAllFiles(dir, &files, "s_*.qc0");
		wxArrayString filenames;
		for (auto& f : files) {
			wxFileName fn = f;
			wxString fnStationID = fn.GetName();
			fnStationID = fnStationID.Right(fnStationID.length() - 2);
			wxTextFile tf(f);
			tf.Open();
			auto& str = tf.GetFirstLine();
			wxString stationID;
			int n_colon = str.Find(':');
			if (n_colon != wxNOT_FOUND) {
				stationID = str.SubString((size_t)n_colon + 1, str.length() - 1);
				int n_comma = stationID.Find(',');
				if (n_comma != wxNOT_FOUND) {
					stationID = stationID.SubString(0, (size_t)n_comma - 1);
					stationID = stationID.Trim(false);
					stationID = stationID.Trim(true);
				}
			}
			if (fnStationID == stationID) {
				filenames.push_back(stationID);
			}
			else {
				wxMessageBox("SERI QC file " + fn.GetFullPath() + " has suspect station ID " + stationID, "SERI QC Error", wxICON_ERROR);
			}
			tf.Close();
		}
		if (filenames.GetCount() > 0) {
			StationID->Set(filenames);
			StationID->SetSelection(0);
		}
		else {
			wxMessageBox("No valid SERI QC files found in " + dir, "SERI QC Error", wxICON_ERROR);
			ret = false;
		}
	}
	return ret;
}



void MainWindow::OnCommand( wxCommandEvent &evt )
{
	wxString dir;
	switch( evt.GetId() )
	{
	case wxID_OPEN:
		{
			wxFileDialog dlg(this, "Open Configuration File", wxEmptyString, wxEmptyString, "Configuration Files (*.json)|*.json", wxFD_OPEN );
			if (dlg.ShowModal() == wxID_OK) {
				if (!OpenConfiguration(dlg.GetPath()))
					wxMessageBox("Error opening configuration file:\n\n" + dlg.GetPath() + "\n\n", "Notice", wxOK, this);
				else {
					m_projectFileName = dlg.GetPath();
					SetTitle(m_projectFileName);
				}
			}
		}
		break;
	case wxID_SAVEAS:
		{
			wxFileDialog dlg(this, "Save Configuration File", wxEmptyString, wxEmptyString, "Configuration Files (*.json)|*.json", wxFD_SAVE | wxFD_OVERWRITE_PROMPT);
			if (dlg.ShowModal() == wxID_OK)
				if (!SaveConfiguration(dlg.GetPath()))
					wxMessageBox("Error saving configuration file:\n\n" + dlg.GetPath() + "\n\n", "Notice", wxOK, this);
				else {
					m_projectFileName = dlg.GetPath();
					SetTitle(m_projectFileName);
				}
		}
		break;
	case wxID_EXIT:
		Close();
		break;
	case ID_BTN_START:
		m_bCancel->Enable(true);
		try {
			InvokePython();
		}
		catch (std::runtime_error e) {
			wxMessageBox(e.what(), "Python Error");
		}
		m_bCancel->Enable(false);
		break;
	case ID_BTN_CANCEL: // enable after running
		m_cancelled = true;
		break;
	case ID_BTN_INPUTFILE:
		{
			wxFileDialog dlg(this, "Open Input File", wxEmptyString, wxEmptyString, "Input Files (*.csv)|*.csv", wxFD_OPEN);
			if (dlg.ShowModal() == wxID_OK) {
				InputFile->SetValue( dlg.GetPath());
			}
		}
		break;
	case ID_BTN_OUTPUTFILE:
		{
			wxFileName fn = InputFile->GetValue();
			wxString outfn = fn.GetName() + "_output.csv";
			wxFileDialog dlg(this, "Open Output File", wxEmptyString, outfn, "Output Files (*.csv)|*.csv", wxFD_OPEN);
			if (dlg.ShowModal() == wxID_OK) {
				OutputFile->SetValue(dlg.GetPath());
			}
		}
		break;
	case ID_BTN_SERIQCPATH:
		{
			StationID->Clear();
			dir = wxDirSelector("Choose folder SERI QC Path");
			if (!dir.empty()) {
				SERIQCpath->ChangeValue(dir);
				// populate SERI QC Station ID with list of valid files in folder
				UpdateStationIDs(dir);
			}
		}
		break;
	case ID_TXT_SERIQCPATH:
		{
			StationID->Clear();
			dir = SERIQCpath->GetValue();
			if (wxDirExists(dir))
				UpdateStationIDs(dir);
		}
		break;
	}
}


wxString MainWindow::GetAppPath()
{
	wxFileName path(g_appArgs[0]);
	if (!path.IsAbsolute())
		path.MakeAbsolute();

	return wxPathOnly(path.GetFullPath());
}

std::string MainWindow::GetPythonConfigPath() 
{
	wxFileName path(GetAppPath() + "/System Files");
	path.Normalize();
	return path.GetFullPath().ToStdString();
}


void MainWindow::LoadConfig() 
{
	std::string python_config_path = GetPythonConfigPath();

	if (python_config_path.empty())
		throw std::runtime_error("Path to SUNI python configuration directory not set. ");


	// load python configuration
	rapidjson::Document python_config_root;
	std::ifstream python_config_doc(python_config_path + "/python_config.json");
	if (python_config_doc.fail())
		throw std::runtime_error("Could not open 'python_config.json'. ");

#ifdef __WINDOWS__
	// check for byte-order mark indicating UTF-8 and skip if it exists since it's not JSON-compatible
	char a, b, c;
	a = (char)python_config_doc.get();
	b = (char)python_config_doc.get();
	c = (char)python_config_doc.get();
	if (a != (char)0xEF || b != (char)0xBB || c != (char)0xBF) {
		python_config_doc.seekg(0);
	}
#endif

	std::ostringstream tmp;
	tmp << python_config_doc.rdbuf();
	python_config_root.Parse(tmp.str().c_str());


	if (!python_config_root.HasMember("exec_path"))
		throw std::runtime_error( "Missing key 'exec_path' in 'python_config.json'.");
	if (!python_config_root.HasMember("python_version"))
		throw std::runtime_error( "Missing key 'python_version' in 'python_config.json'.");


	m_pythonExecPath = python_config_root["exec_path"].GetString();
	if (m_pythonExecPath.empty())
		throw std::runtime_error( "Missing key 'exec_path' in 'python_config.json'.");

	auto str_python = std::string(GetPythonConfigPath()) + "/" + m_pythonExecPath;
	if (!wxFileExists(str_python.c_str()))
		throw std::runtime_error( "Missing python executable 'exe_path' in 'python_config.json'.");

	auto python_version = python_config_root["python_version"].GetString();

	// load suni configuration
	rapidjson::Document suni_config_root;
	std::ifstream suni_config_doc(python_config_path + "/suni.json");
	if (suni_config_doc.fail())
		throw std::runtime_error( "Could not open 'suni.json'. ");

	std::ostringstream tmplb;
	tmplb << suni_config_doc.rdbuf();
	suni_config_root.Parse(tmplb.str().c_str());


	if (!suni_config_root.HasMember("run_cmd"))
		throw std::runtime_error("Missing key 'run_cmd' in 'suni.json'.");
	if (!suni_config_root.HasMember("min_python_version"))
		throw std::runtime_error( "Missing key 'min_python_version' in 'suni.json'.");

	m_pythonRunCmd = suni_config_root["run_cmd"].GetString();
	auto min_python_version = suni_config_root["min_python_version"].GetString();

	// check version works out
	std::stringstream min_ver(min_python_version);
	std::stringstream py_ver(python_version);
	std::string min_ver_token, py_ver_token;

	while (std::getline(min_ver, min_ver_token, '.')) {
		if (!std::getline(py_ver, py_ver_token, '.'))
			return;
		if (std::stoi(min_ver_token) > std::stoi(py_ver_token))
			throw std::runtime_error( "'min_python_version' requirement not met.");
	}
}


std::string MainWindow::CallPythonModule(const std::string& input_dict_as_text) {
	std::promise<std::string> python_result;
	std::future<std::string> f_completes = python_result.get_future();
	std::thread([&]
		{
			std::string cmd = std::string(GetPythonConfigPath()) + "/" + m_pythonExecPath + " -c \"" + m_pythonRunCmd + "\"";
			size_t pos = cmd.find("<input>");
			cmd.replace(pos, 7, input_dict_as_text);

			FILE* file_pipe = popen(cmd.c_str(), "r");
			if (!file_pipe) {
				python_result.set_value("SUNI error. Could not call python with cmd:\n" + cmd);
				return;
			}

			std::string mod_response;
			char buffer[BUFSIZE];
			while (fgets(buffer, sizeof(buffer), file_pipe)) {
				mod_response += buffer;
			}
			pclose(file_pipe);
			if (mod_response.empty())
				python_result.set_value("SUNI error. Function did not return a response.");
			else
				python_result.set_value(mod_response);
		}
	).detach();

	std::chrono::system_clock::time_point time_passed
		= std::chrono::system_clock::now() + std::chrono::seconds(60 * 5);

	if (std::future_status::ready == f_completes.wait_until(time_passed))
		return f_completes.get();
	else
		throw std::runtime_error("python handler error. Python process timed out.");
}


void MainWindow::replaceBackslash(std::string& str)
{
	// Regex pattern to match all backslashes in string
	std::regex regexPattern("\\");
	// Replace all occurrenecs of substrings that
	// matches the given regex pattern
	str = std::regex_replace(str, regexPattern, "\\");
}


/*
class SimulationThreadWindows : public wxThread
{
//	wxMutex m_currentLock, m_cancelLock, m_nokLock, m_logLock, m_percentLock;
	size_t m_current;
	bool m_canceled;
	size_t m_nok;
	wxArrayString m_messages;
	wxString m_update;
	wxString m_curName;
	float m_percent;
	int m_threadId;
	std::string m_pythonpath, m_pythonargs;

	PROCESS_INFORMATION m_pi;
	STARTUPINFO m_si;
	SECURITY_ATTRIBUTES m_sa;
	HANDLE m_stdin_rd = NULL;
	HANDLE m_stdout_wr = NULL;
	HANDLE m_stdout_rd = NULL;
	HANDLE m_stdin_wr = NULL;
	HANDLE m_stderr_rd = NULL;
	HANDLE m_stderr_wr = NULL;  //pipe handles

	char m_buf[BUFSIZE];           //i/o buffer
	char m_err_buf[BUFSIZE];           //i/o buffer
	char m_out_buf[BUFSIZE];           //i/o buffer

	unsigned long m_bread;   //bytes read
	unsigned long m_bread_last = 0;
	unsigned long m_avail;   //bytes available
	unsigned long m_err_bread;   //bytes read
	unsigned long m_err_bread_last = 0;
	unsigned long m_err_avail;   //bytes available
	unsigned long m_out_bread;   //bytes read
	unsigned long m_out_bread_last = 0;
	unsigned long m_out_avail;   //bytes available

public:

	SimulationThreadWindows(const std::string& pythonpath, const std::string& pythonargs)
		: wxThread(wxTHREAD_JOINABLE) {
		m_canceled = false;
		m_nok = 0;
		m_percent = 0;
		m_current = 0;
		m_pythonpath = pythonpath;
		m_pythonargs = pythonargs;

		m_canceled = false;

		memset(m_buf, 0, sizeof(m_buf));
		memset(m_err_buf, 0, sizeof(m_err_buf));
		memset(m_out_buf, 0, sizeof(m_out_buf));

		m_sa.nLength = sizeof(SECURITY_ATTRIBUTES);
		m_sa.bInheritHandle = TRUE;
		m_sa.lpSecurityDescriptor = NULL;
		if (!CreatePipe(&m_stdout_rd, &m_stdout_wr, &m_sa, 0)) {
			//			goto done;
		}
		if (!SetHandleInformation(m_stdout_rd, HANDLE_FLAG_INHERIT, 0)) {
			//			goto done;
		}
		//set startupinfo for the spawned process
		GetStartupInfo(&m_si);

		m_si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
		m_si.wShowWindow = SW_HIDE; // for production
//		m_si.wShowWindow = SW_SHOW; // for debugging
		//set the new handles for the child process
		m_si.hStdOutput = m_stdout_wr;
		//		m_si.hStdError = m_stderr_wr;
		//		m_si.hStdInput = m_stdin_rd;


	}


	size_t Size() { return 1; }
	size_t Current() {
		//wxMutexLocker _lock(m_currentLock);
		return m_current;
	}
	float GetPercent(wxString* update = 0) {
		//wxMutexLocker _lock(m_percentLock);
		//PeekNamedPipe(m_stdout_rd, m_buf, BUFSIZE - 1, &m_bread, &m_avail, NULL);
		wxString ret = wxString::FromUTF8(m_buf);
		ret.Replace("\n", "");
		ret.Replace("\r", "");
		ret = ret.Trim().Right(2);
		if (update)
			*update = ret;
		double dret;
		if (ret.ToDouble(&dret))
			return (float)dret;
		else
			return 0;
	}

	void Cancel()
	{
		//GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0);
		//wxMutexLocker _lock(m_cancelLock);
		GenerateConsoleCtrlEvent(CTRL_C_EVENT, m_pi.dwProcessId); // does nothing
		//GenerateConsoleCtrlEvent(CTRL_C_EVENT, m_pi.dwThreadId); // does nothing
		//TerminateProcess(m_pi.hProcess,0); //leaves all python instances running and kills console. 
		m_canceled = true;
	}

	size_t NOk() {
		//wxMutexLocker _lock(m_nokLock);
		return m_nok;
	}

	void Message(const wxString& text)
	{
		//wxMutexLocker _lock(m_logLock);
		wxString L(m_curName);
		if (!L.IsEmpty()) L += ": ";
		m_messages.Add(L + text);
	}

	virtual void Warn(const wxString& text)
	{
		Message(text);
	}

	virtual void Error(const wxString& text)
	{
		Message(text);
	}

	virtual void Update(float percent, const wxString& text)
	{
		//wxMutexLocker _lock(m_percentLock);
		m_percent = percent;
		m_update = text;
	}


	virtual bool IsCancelled() {
		//wxMutexLocker _lock(m_cancelLock);
		return m_canceled;
	}

	wxArrayString GetNewMessages()
	{
		//wxMutexLocker _lock(m_logLock);
		wxArrayString list = m_messages;
		m_messages.Clear();
		return list;
	}

	virtual void* Entry()
	{

		DWORD ReturnValue;

		CA2T programpath(m_pythonpath.c_str());
		CA2T programargs(m_pythonargs.c_str());

		if (CreateProcess(programpath, programargs, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &m_si, &m_pi)) { // production
//		if (CreateProcess(programpath, programargs, NULL, NULL, TRUE, CREATE_NEW_CONSOLE, NULL, NULL, &m_si, &m_pi)) { // debugging FALSE instead of TRUE shows console output but cannot capture buffer
			AttachConsole(m_pi.dwProcessId);
			SetConsoleCtrlHandler(NULL, true);
			while(1) {
				PeekNamedPipe(m_stdout_rd, m_buf, BUFSIZE - 1, &m_bread, &m_avail, NULL);
//				PeekNamedPipe(m_stderr_rd, m_err_buf, BUFSIZE - 1, &m_err_bread, &m_err_avail, NULL);
//				PeekNamedPipe(m_stdin_rd, m_out_buf, BUFSIZE - 1, &m_out_bread, &m_out_avail, NULL);
				//check to see if there is any data to read from stdout
				if (m_bread != 0) {
					if (ReadFile(m_stdout_rd, m_buf, BUFSIZE - 1, &m_bread, NULL)) {
						m_bread_last = m_bread;
					}
				}
				else if (m_bread_last > 0)
				{
					break;
				}
				this->Sleep(100);
//				::wxMilliSleep(10);
				
			}
//			WaitForSingleObject(m_pi.hProcess, INFINITE);
//			GetExitCodeProcess(m_pi.hProcess, &ReturnValue);

			SetConsoleCtrlHandler(NULL, false);
			FreeConsole();

			CloseHandle(m_pi.hThread);
			CloseHandle(m_pi.hProcess);
//			wxMutexLocker _lock(m_nokLock);
			m_nok++;
		}


//		m_currentLock.Lock();
//		m_current++;
//		m_currentLock.Unlock();

//		wxMutexLocker _lock(m_cancelLock);

//	done:
		std::vector<HANDLE> handles = { m_stdin_rd, m_stdin_wr, m_stdout_rd, m_stdout_wr, m_stderr_rd, m_stderr_wr };
		for (HANDLE handle : handles) {
			if (handle && handle != INVALID_HANDLE_VALUE) {
				CloseHandle(handle);
			}
		}
		if (m_buf[0] == '\0') {
			if (m_err_buf[0] == '\0')
				throw std::runtime_error("SUNI error. Function did not return a response and no error.");
			else
				return m_err_buf;
			throw std::runtime_error("SUNI error. Function did not return a response.");
		}
//		return buf;

		FreeConsole();

		if (m_canceled) {
			m_messages.Add("Process cancelled by user.");
		}
		else {
			wxString str(m_buf);
			m_messages = wxSplit(str, '\n');
		}
		return m_buf;
	}


};
*/

void MainWindow::UpdateProgressBar()
{
	wxCriticalSectionLocker lock(m_dataCS);
//	wxString ret = wxString::FromUTF8(m_data);
	wxString ret(m_data);
	wxArrayString as = wxSplit(ret, '\n');
//	ret.Replace("\n", "");
//	ret.Replace("\r", "");
//	ret = ret.Trim().Right(2); // percent
	if (as.GetCount() > 2) {// last value is garbled
		ret = as[as.GetCount() - 2];
		ret.Replace("\r", "");
	}
	double dret;
	int current = m_gProgress->GetValue();
	if (current < 0) current = 0;
	if (ret.ToDouble(&dret)) {
		if (dret - current > 0)
			m_gProgress->SetValue((int)dret);
	}

}

wxThread::ExitCode MainWindow::Entry()
{
	size_t offset = 0;
	unsigned long m_bread;   //bytes read
	unsigned long m_bread_last = 0;
	unsigned long m_avail;   //bytes available
	unsigned long m_bread_err;   //bytes read
	unsigned long m_bread_err_last = 0;
	unsigned long m_avail_err;   //bytes available
	PROCESS_INFORMATION m_pi;
	STARTUPINFO m_si;
	SECURITY_ATTRIBUTES m_sa;
	HANDLE m_stdin_rd = NULL;
	HANDLE m_stdout_wr = NULL;
	HANDLE m_stdout_rd = NULL;
	HANDLE m_stdin_wr = NULL;
	HANDLE m_stderr_rd = NULL;
	HANDLE m_stderr_wr = NULL;  //pipe handles

	CA2T programpath(m_pythonpath.c_str());
	CA2T programargs(m_pythonargs.c_str());


	m_sa.nLength = sizeof(SECURITY_ATTRIBUTES);
	m_sa.bInheritHandle = TRUE;
	m_sa.lpSecurityDescriptor = NULL;
	if (!CreatePipe(&m_stdout_rd, &m_stdout_wr, &m_sa, 0)) {
		return  (wxThread::ExitCode)1;
	}
	if (!SetHandleInformation(m_stdout_rd, HANDLE_FLAG_INHERIT, 0)) {
		return  (wxThread::ExitCode)1;
	}
	if (!CreatePipe(&m_stderr_rd, &m_stderr_wr, &m_sa, 0)) {
		return  (wxThread::ExitCode)1;
	}
	if (!SetHandleInformation(m_stderr_rd, HANDLE_FLAG_INHERIT, 0)) {
		return  (wxThread::ExitCode)1;
	}

	//set startupinfo for the spawned process
	GetStartupInfo(&m_si);

	m_si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
	m_si.wShowWindow = SW_HIDE; // for production
//	m_si.wShowWindow = SW_SHOW; // for debugging
	//set the new handles for the child process
	m_si.hStdOutput = m_stdout_wr;
	m_si.hStdError = m_stderr_wr;


	char buffer[BUFSIZE];
	char buffererr[BUFSIZE];

	if (CreateProcess(programpath, programargs, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &m_si, &m_pi)) { // production
		while (1) {
			PeekNamedPipe(m_stdout_rd, buffer, BUFSIZE - 1, &m_bread, &m_avail, NULL);
			//				PeekNamedPipe(m_stderr_rd, m_err_buf, BUFSIZE - 1, &m_err_bread, &m_err_avail, NULL);
			//				PeekNamedPipe(m_stdin_rd, m_out_buf, BUFSIZE - 1, &m_out_bread, &m_out_avail, NULL);
							//check to see if there is any data to read from stdout
			if (m_bread != 0) {
				if (ReadFile(m_stdout_rd, buffer, BUFSIZE - 1, &m_bread, NULL)) {
					m_bread_last = m_bread;
					{
						wxCriticalSectionLocker lock(m_dataCS);
						memcpy(m_data + offset, buffer, BUFSIZE - 1);
						if (m_cancelled) {
							if (AttachConsole(m_pi.dwProcessId)) {
								// Disable Ctrl-C handling for our program
								SetConsoleCtrlHandler(NULL, true);

								GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0); // SIGINT

								//Re-enable Ctrl-C handling or any subsequently started
								//programs will inherit the disabled state.
//								SetConsoleCtrlHandler(NULL, false);
//								FreeConsole();
//								WaitForSingleObject(m_pi.hProcess, 10000);// exception
//								wxMilliSleep(10000);
								while (1) {
									PeekNamedPipe(m_stderr_rd, buffererr, BUFSIZE - 1, &m_bread_err, &m_avail, NULL);
									if (m_bread_err != 0) {
										if (ReadFile(m_stderr_rd, buffererr, BUFSIZE - 1, &m_bread_err, NULL)) {
											m_bread_err_last = m_bread_err;
										}
									}
									else if (m_bread_err_last > 0) {
										break;
									}
									wxMilliSleep(500);
								}
								break;
							}
						}
						UpdateProgressBar();
					}
				}
			}
			else if (m_bread_last > 3) // 100%
			{
				break;
			}
			wxMilliSleep(500);
		//	wxGetApp().Yield();
		}

		CloseHandle(m_pi.hThread);
		CloseHandle(m_pi.hProcess);
	}


	std::vector<HANDLE> handles = { m_stdin_rd, m_stdin_wr, m_stdout_rd, m_stdout_wr, m_stderr_rd, m_stderr_wr };
	for (HANDLE handle : handles) {
		if (handle && handle != INVALID_HANDLE_VALUE) {
			CloseHandle(handle);
		}
	}
	if (m_cancelled) {
		m_messages.Add("Process cancelled by user.");
		wxString str(buffererr);
		m_messages = wxSplit(str, '\n');
	}
	else {
		wxString str(m_data);
		m_messages = wxSplit(str, '\n');
	}
	return  (wxThread::ExitCode)0;
}



void MainWindow::SendSIGINT(HANDLE hProcess)
{
	DWORD pid = GetProcessId(hProcess);
	FreeConsole();
	if (AttachConsole(pid))
	{
		// Disable Ctrl-C handling for our program
		SetConsoleCtrlHandler(NULL, true);

		GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0); // SIGINT

		//Re-enable Ctrl-C handling or any subsequently started
		//programs will inherit the disabled state.
		SetConsoleCtrlHandler(NULL, false);

//		WaitForSingleObject(hProcess, 10000);
	}
}

// Function to send a CTRL+C signal to a process
void MainWindow::SendCtrlC(DWORD dwProcessId)
{
	// Get a handle to the process
	HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, dwProcessId);
	if (hProcess == NULL){
		return;
	}

	// Generate a CTRL+C event
	GenerateConsoleCtrlEvent(CTRL_C_EVENT, dwProcessId);

	// Close the process handle
	CloseHandle(hProcess);
}



#ifdef __WINDOWS__
std::string MainWindow::CallPythonModuleWindows(const std::string& input_dict_as_text) {
	STARTUPINFO si;
	SECURITY_ATTRIBUTES sa;
	PROCESS_INFORMATION pi;
	HANDLE stdin_rd = NULL;
	HANDLE stdout_wr = NULL;
	HANDLE stdout_rd = NULL;
	HANDLE stdin_wr = NULL;
	HANDLE stderr_rd = NULL;
	HANDLE stderr_wr = NULL;  //pipe handles
	char buf[BUFSIZE];           //i/o buffer
	memset(buf, 0, sizeof(buf));
	char err_buf[BUFSIZE];           //i/o buffer
	memset(err_buf, 0, sizeof(err_buf));
	char out_buf[BUFSIZE];           //i/o buffer
	memset(out_buf, 0, sizeof(out_buf));

	std::string pythonpath = std::string(GetPythonConfigPath()) + "\\" + m_pythonExecPath;
	CA2T programpath(pythonpath.c_str());
	std::string pythonarg = " -c \"" + m_pythonRunCmd + "\"";
	size_t pos = pythonarg.find("<input>");
	std::string str = input_dict_as_text;
	std::replace(str.begin(), str.end(), '\\', '/');
	pythonarg.replace(pos, 7, str);
	CA2T programargs(pythonarg.c_str());

	sa.nLength = sizeof(SECURITY_ATTRIBUTES);
	sa.bInheritHandle = TRUE;
	sa.lpSecurityDescriptor = NULL;

	if (!CreatePipe(&stdin_rd, &stdin_wr, &sa, 0)) {
		goto done;
	}
	if (!SetHandleInformation(stdin_wr, HANDLE_FLAG_INHERIT, 0)) {
		goto done;
	}
	if (!CreatePipe(&stdout_rd, &stdout_wr, &sa, 0)) {
		goto done;
	}
	if (!SetHandleInformation(stdout_rd, HANDLE_FLAG_INHERIT, 0)) {
		goto done;
	}
	if (!CreatePipe(&stderr_rd, &stderr_wr, &sa, 0)) {
		goto done;
	}
	if (!SetHandleInformation(stderr_rd, HANDLE_FLAG_INHERIT, 0)) {
		goto done;
	}

	//set startupinfo for the spawned process
	/*The dwFlags member tells CreateProcess how to make the process.
	STARTF_USESTDHANDLES: validates the hStd* members.
	STARTF_USESHOWWINDOW: validates the wShowWindow member*/
	GetStartupInfo(&si);

	si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
	si.wShowWindow = SW_HIDE;
	//set the new handles for the child process
	si.hStdOutput = stdout_wr;
	si.hStdError = stderr_wr;
	si.hStdInput = stdin_rd;


	if (CreateProcess(programpath, programargs, NULL, NULL, TRUE, CREATE_NO_WINDOW,	NULL, NULL, &si, &pi)) {
		unsigned long bread;   //bytes read
		unsigned long bread_last = 0;
		unsigned long avail;   //bytes available
		unsigned long err_bread;   //bytes read
		unsigned long err_bread_last = 0;
		unsigned long err_avail;   //bytes available
		unsigned long out_bread;   //bytes read
		unsigned long out_bread_last = 0;
		unsigned long out_avail;   //bytes available
		size_t i = 0;
		size_t n_timeout_max = 100000000; // timeout
//		size_t n_timeout_max = 1000000000; // timeout
		for (i = 0; i < n_timeout_max; i++) {
			PeekNamedPipe(stdout_rd, buf, BUFSIZE - 1, &bread, &avail, NULL);
			PeekNamedPipe(stderr_rd, err_buf, BUFSIZE - 1, &err_bread, &err_avail, NULL);
			PeekNamedPipe(stdin_rd, out_buf, BUFSIZE - 1, &out_bread, &out_avail, NULL);
			//check to see if there is any data to read from stdout
			if (bread != 0) {
				if (ReadFile(stdout_rd, buf, BUFSIZE - 1, &bread, NULL)) {
					bread_last = bread;
				}
			}
			else if (bread_last > 0)
			{
				break;
			}
			if (err_bread != 0) {
				if (ReadFile(stderr_rd, err_buf, BUFSIZE - 1, &err_bread, NULL)) {
					err_bread_last = err_bread;
				}
			}
			else if (err_bread_last > 0)
			{
				break;
			}
			if (out_bread != 0) {
				if (ReadFile(stdin_rd, out_buf, BUFSIZE - 1, &out_bread, NULL)) {
					out_bread_last = out_bread;
				}
			}
			else if (out_bread_last > 0)
			{
				break;
			}
			wxMilliSleep(1000);
		}

		CloseHandle(pi.hThread);
		CloseHandle(pi.hProcess);

		if (i >= n_timeout_max) {
			throw std::runtime_error("SUNI error. Timeout while running.");
		}
	}
done:
	std::vector<HANDLE> handles = { stdin_rd, stdin_wr, stdout_rd, stdout_wr, stderr_rd, stderr_wr };
	for (HANDLE handle : handles) {
		if (handle && handle != INVALID_HANDLE_VALUE) {
			CloseHandle(handle);
		}
	}
	if (buf[0] == '\0') {
		if (err_buf[0] == '\0')
			throw std::runtime_error("SUNI error. Function did not return a response and no error.");
		else
			return err_buf;
//		throw std::runtime_error("SUNI error. Function did not return a response.");
	}
	return buf;
}
#endif


void MainWindow::CleanOutputString(std::string& output_json) {
	size_t pos = output_json.find("{");
	if (pos != std::string::npos)
		output_json = output_json.substr(pos);
	std::replace(output_json.begin(), output_json.end(), '\'', '\"');
}


bool MainWindow::CheckPythonPackage(const std::string& pip_name) {
	if (CheckPythonInstalled(pythonConfig)) {
		if (CheckPythonPackageInstalled(pip_name, pythonConfig))
			return true;
	}
	return false;
}

void MainWindow::InstallPython() {
	if (pythonConfig.pythonVersion.empty() && pythonConfig.minicondaVersion.empty())
		LoadPythonConfig();

	auto python_path = GetPythonConfigPath();
	// already installed and correctly configured
	if (CheckPythonInstalled(pythonConfig)) {
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

void MainWindow::InstallPythonPackage(const std::string& pip_name) {
	if (CheckPythonPackageInstalled(pip_name, pythonConfig))
		return;
	auto packageConfig = ReadPythonPackageConfig(pip_name, GetPythonConfigPath() + "/" + pip_name + ".json");

#ifdef __WXMSW__
	bool retval = InstallFromPipWindows(GetPythonConfigPath() + "\\" + pythonConfig.pipPath, packageConfig, GetPythonConfigPath() + "\\");
#else
	std::string pip_exec = GetPythonConfigPath() + "/" + pythonConfig.pipPath;
	bool retval = InstallFromPip(pip_exec, packageConfig, GetPythonConfigPath() + "\\"); // TODO - test
#endif
	if (retval == 0) {
		pythonConfig.packages.push_back(pip_name);
		WritePythonConfig(GetPythonConfigPath() + "/python_config.json", pythonConfig);
	}
	else {
		throw std::runtime_error("Error installing " + pip_name);
	}
}


void MainWindow::LoadPythonConfig() {
	pythonConfig = ReadPythonConfig(GetPythonConfigPath() + "/python_config.json");
	if (CheckPythonInstalled(pythonConfig)) {
		std::string python_path = GetPythonConfigPath();
		set_python_path(python_path.c_str());
		return;
	}
}



bool MainWindow::SetupPython()
{
	bool ret = false;

	if (CheckPythonPackage("suni"))
		ret = true;
	else {
		wxBusyCursor wait;
		MyMessageDialog dlg(this, "Installing the SUNI model.\nPlease note that it may take a few minutes to complete the initial installation.\nOnce installed, you will be able to estimate the solar uncertainty using the 'Start' button.", "Solar Uncertainty Integrator", wxCENTER);
		dlg.Show();
		wxGetApp().SafeYieldFor(&dlg, true);
		InstallPython();
		InstallPythonPackage("suni");
		dlg.Close();
		ret = true;
	}

	return ret;
}

bool MainWindow::InvokePython()
{
	if (m_projectFileName.empty())
		return false;

	// Install Python if necessary
	if (!SetupPython()) {
		throw std::runtime_error("Python setup failed");
		return false;
	}


	try {
		wxBusyCursor wait;

		LoadConfig();
#ifdef __WINDOWS__
		std::string str = m_projectFileName.ToStdString();
		m_pythonpath = std::string(GetPythonConfigPath()) + "\\" + m_pythonExecPath ;
		m_pythonargs = " -c \"" + m_pythonRunCmd + "\"";
		size_t pos = m_pythonargs.find("<input>");
		std::replace(str.begin(), str.end(), '\\', '/');
		m_pythonargs.replace(pos, 7, str);

		m_messages.clear();

		if (CreateThread(wxTHREAD_JOINABLE) != wxTHREAD_NO_ERROR)
		{
			wxMessageBox("Could not create the Python thread!");
			return false;
		}
		// go!
		if (GetThread()->Run() != wxTHREAD_NO_ERROR)
		{
			wxMessageBox("Could not run the Python thread!");
			return false;
		}

		while (GetThread() && GetThread()->IsRunning()) {
			wxGetApp().Yield(); // to update progress bar
		}


/*
		std::unique_ptr<SimulationThreadWindows> sth = std::make_unique<SimulationThreadWindows>(pythonpath, pythonarg);
			sth->Add(pythonpath, pythonarg);
		sth->Create();
		sth->Run();

		while (sth->IsRunning()) {
			wxString update;
			float per = sth->GetPercent(&update);
			m_gProgress->SetValue((int)per);
			m_gProgress->Refresh();
			m_gProgress->Layout();

			wxGetApp().Yield();

			if (m_cancelled) {
				sth->Cancel();
				m_cancelled = false;
			}

			::wxMilliSleep(10);
		}
		m_gProgress->SetValue(100);


*/
//			std::string output_json = CallPythonModuleWindows(str);
#else
		std::string output_json = CallPythonModule(m_projectFileName.ToStdString());
#endif


		// testing raw output
		//wxMessageBox(wxString(output_json), "Results");
			
		auto& strMessages = m_messages; // sth->GetNewMessages();

		// user cancelled
		if (m_cancelled) {
			m_cancelled = false;
			wxString sPythonMessage = "";
			for (size_t i = 0; i < strMessages.GetCount(); i++) {
				if (strMessages[i].Lower().Find("interrupt") != wxNOT_FOUND)
					sPythonMessage = strMessages[i];
			}
			if (sPythonMessage.length() > 0)
				sPythonMessage = "\nSUNI: " + sPythonMessage;
			wxMessageBox("Uncertainty analysis cancelled." + sPythonMessage, "User Cancelled", wxICON_INFORMATION);
		}
		else {
			bool bError = false;
			wxString sError = "";

			if (strMessages.GetCount() > 0) {
				bError = strMessages[0].Lower().Find("error") != wxNOT_FOUND;
				for (size_t i = 0; i < strMessages.GetCount(); i++) {
					if (bError) {
						sError += strMessages[i] + "\n";
					}
				}
			}


			if (sError.length() > 0) {
				wxMessageBox(sError, "Error", wxICON_ERROR);
			}
			else {
				// file retrieved to [Input File name]_Report.txt
				wxFileName fnInputFile = InputFile->GetValue();
				wxFileName fnOutputFile = OutputFile->GetValue();
				if (wxFileExists(fnOutputFile.GetFullPath())) {
					wxString sfn = fnOutputFile.GetPath() + "/" + fnInputFile.GetName() + "_Report.txt";
					if (wxFileExists(sfn)) {
						wxLaunchDefaultApplication(sfn);
						wxString s;
						wxTextFile tFile;
						tFile.Open(sfn);
						s = tFile.GetFirstLine() + "\n";
						while (!tFile.Eof())
							s += tFile.GetNextLine() + "\n";
						wxMessageBox(s, "Report", wxICON_NONE);
					}
				}
				else {
					sError = "Python run unsuccessful \n" + m_pythonpath + m_pythonargs;
					wxMessageBox(sError, "Error", wxICON_ERROR);
					wxString sfn = GetAppPath() + "/System Files/error.txt";
					wxTextFile tFile(sfn);
					tFile.AddLine(m_pythonpath + m_pythonargs);
					tFile.Write();
					wxLaunchDefaultApplication(sfn);
				}
			}
		}
		m_gProgress->SetValue(0);
	}
	catch (std::future_error& e) {
		throw std::runtime_error(e.what());
	}
	return true;
}

void MainWindow::OnClose( wxCloseEvent &evt )
{
	Raise();
	if ( !SaveConfiguration(m_projectFileName))
	{
		evt.Veto();
		return;
	}
	// save current configuration
	;
	SUIApp::Settings().Write("configuration_file", m_projectFileName);

	// save window position to settings
	wxRect rr;
	GetPosition( &rr.x,&rr.y );
	GetClientSize( &rr.width, &rr.height );
	SUIApp::Settings().Write( "window_x", rr.x);
	SUIApp::Settings().Write( "window_y", rr.y);
	SUIApp::Settings().Write( "window_width", rr.width);
	SUIApp::Settings().Write( "window_height", rr.height);
	SUIApp::Settings().Write( "window_maximized", IsMaximized() );

	// clean up running thread if necessary
	if (GetThread() &&
		GetThread()->IsRunning())
		GetThread()->Wait();

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
//	path.Normalize();
	if (!path.IsAbsolute())
		path.MakeAbsolute();
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
//	g_mainWindow->Show(true);

	bool first_load = true;
	wxString fl_key = wxString::Format("first_load");
	Settings().Read(fl_key, &first_load, true);
	wxString configurationFile;
	if (first_load)
	{
		// register the first load
		Settings().Write(fl_key, false);
		configurationFile = GetAppPath() + "/Configuration Files/CfgDefaultsV001.json";
	}
	else
	{
		Settings().Read("configuration_file", &configurationFile);

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
	if (g_mainWindow->OpenConfiguration(configurationFile)) {
		g_mainWindow->SetProjectFileName(configurationFile);
		g_mainWindow->SetTitle(configurationFile);
	}
	else
		wxMessageBox("Error loading file: " + configurationFile, "Initialization error", wxICON_ERROR);

// Check in MainWindow - may want to move here. main windows not fully rendered here
/*	try {
		g_mainWindow->SetupPython();
	}
	catch (std::exception e) {
		SUIException ex(e.what());
		wxMessageBox(ex.what(),"Initialization error", wxICON_ERROR);
	}
*/	
	SetTopWindow(g_mainWindow);
	g_mainWindow->Show();
//	g_mainWindow->SetupPython(); // main window not yet rendered
	/*
	bool ret = false;
	if (g_mainWindow->CheckPythonPackage("suni"))
		ret = true;
	else {
		wxBusyCursor wait;
		MyMessageDialog dlg(NULL, "Installing the SUNI model. Please note that it may take a few minutes to complete the initial installation. Once installed, you will be able to estimate the solar uncertainty using the 'Start' button.", "Solar Uncertainty Integrator", wxCENTER, wxDefaultPosition, wxDefaultSize);
		dlg.Show();
		dlg.CentreOnScreen();
		//wxGetApp().Yield(true);


		g_mainWindow->InstallPython();
		g_mainWindow->InstallPythonPackage("suni");
		dlg.Close();
		ret = true;
	}

	return ret;
	*/
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
/*
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
*/


IMPLEMENT_APP( SUIApp );
