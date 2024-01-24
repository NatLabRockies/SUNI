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

static PythonConfig pythonConfig;


enum { __idFirst = wxID_HIGHEST+592,

	ID_BTN_INPUTFILE, ID_BTN_OUTPUTFILE, ID_BTN_SERIQCPATH,
	ID_TXT_INPUTFILE, ID_TXT_OUTPUTFILE, ID_TXT_SERIQCPATH,
	ID_INTERNAL_DATAFOLDER
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
/*
	m_topBook = new wxSimplebook( this, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxBORDER_NONE );


	m_caseTabPanel = new wxPanel( m_topBook );
	m_topBook->AddPage( m_caseTabPanel, wxT("Main project window") );

*/
	//wxBoxSizer *tools = new wxBoxSizer( wxHORIZONTAL );
	m_mainMenuBar = new wxMenuBar;

	wxMenu *menu = new wxMenu ;
	menu->Append(wxID_SAVEAS, "Save Configuration");
	menu->Append(wxID_OPEN, "Get Configuration");
	menu->Append(wxID_EXIT, "Close");

	m_mainMenuBar->Append(menu, wxT("&File"));

	SetMenuBar(m_mainMenuBar);

	wxPanel* p = new wxPanel(this, wxID_ANY);

	wxStaticBoxSizer* sizer0 = new wxStaticBoxSizer(wxVERTICAL,p, "Files");
	m_bInputFile = new wxButton(p, ID_BTN_INPUTFILE, "Input File");
	sizer0->Add(m_bInputFile,0, wxALIGN_LEFT,5);
	m_tInputFile = new wxTextCtrl(p, ID_TXT_INPUTFILE);
	m_tInputFile->SetSizeHints(500, 24);
	sizer0->Add(m_tInputFile,1, wxEXPAND | wxALL,5);
	m_bOutputFile = new wxButton(p, ID_BTN_OUTPUTFILE, "Output File");
	sizer0->Add(m_bOutputFile, 0, wxALIGN_LEFT, 5);
	m_tOutputFile = new wxTextCtrl(p, ID_TXT_OUTPUTFILE);
	m_tOutputFile->SetSizeHints(500, 24);
	sizer0->Add(m_tOutputFile, 1, wxEXPAND | wxALL, 5);
	m_bSERIQCPath = new wxButton(p, ID_BTN_SERIQCPATH, "SERI QC Path");
	sizer0->Add(m_bSERIQCPath, 0, wxALIGN_LEFT, 5);
	m_tSERIQCPath = new wxTextCtrl(p, ID_TXT_SERIQCPATH);
	m_tSERIQCPath->SetSizeHints(500, 24);
	sizer0->Add(m_tSERIQCPath, 1, wxEXPAND | wxALL, 5);


	wxStaticBoxSizer* sizer1 = new wxStaticBoxSizer(wxVERTICAL, p, "Instruments and Uncertainty");
	m_bInputFile = new wxButton(p, ID_BTN_INPUTFILE, "Input File");
	sizer1->Add(m_bInputFile, 0, wxALIGN_LEFT, 5);
	m_tInputFile = new wxTextCtrl(p, ID_TXT_INPUTFILE);
	m_tInputFile->SetSizeHints(500, 24);
	sizer1->Add(m_tInputFile, 1, wxEXPAND | wxALL, 5);
	m_bOutputFile = new wxButton(p, ID_BTN_OUTPUTFILE, "Output File");
	sizer1->Add(m_bOutputFile, 0, wxALIGN_LEFT, 5);
	m_tOutputFile = new wxTextCtrl(p, ID_TXT_OUTPUTFILE);
	m_tOutputFile->SetSizeHints(500, 24);
	sizer1->Add(m_tOutputFile, 1, wxEXPAND | wxALL, 5);
	m_bSERIQCPath = new wxButton(p, ID_BTN_SERIQCPATH, "SERI QC Path");
	sizer1->Add(m_bSERIQCPath, 0, wxALIGN_LEFT, 5);
	m_tSERIQCPath = new wxTextCtrl(p, ID_TXT_SERIQCPATH);
	m_tSERIQCPath->SetSizeHints(500, 24);
	sizer1->Add(m_tSERIQCPath, 1, wxEXPAND | wxALL, 5);

	wxStaticBoxSizer* sizer2 = new wxStaticBoxSizer(wxVERTICAL, p, "Defaults");
	m_bInputFile = new wxButton(p, ID_BTN_INPUTFILE, "Input File");
	sizer2->Add(m_bInputFile, 0, wxALIGN_LEFT, 5);
	m_tInputFile = new wxTextCtrl(p, ID_TXT_INPUTFILE);
	m_tInputFile->SetSizeHints(500, 24);
	sizer2->Add(m_tInputFile, 1, wxEXPAND | wxALL, 5);
	m_bOutputFile = new wxButton(p, ID_BTN_OUTPUTFILE, "Output File");
	sizer2->Add(m_bOutputFile, 0, wxALIGN_LEFT, 5);
	m_tOutputFile = new wxTextCtrl(p, ID_TXT_OUTPUTFILE);
	m_tOutputFile->SetSizeHints(500, 24);
	sizer2->Add(m_tOutputFile, 1, wxEXPAND | wxALL, 5);
	m_bSERIQCPath = new wxButton(p, ID_BTN_SERIQCPATH, "SERI QC Path");
	sizer2->Add(m_bSERIQCPath, 0, wxALIGN_LEFT, 5);
	m_tSERIQCPath = new wxTextCtrl(p, ID_TXT_SERIQCPATH);
	m_tSERIQCPath->SetSizeHints(500, 24);
	sizer2->Add(m_tSERIQCPath, 1, wxEXPAND | wxALL, 5);

	wxStaticBoxSizer* sizer3 = new wxStaticBoxSizer(wxVERTICAL, p, "Processing");
	m_bInputFile = new wxButton(p, ID_BTN_INPUTFILE, "Input File");
	sizer3->Add(m_bInputFile, 0, wxALIGN_LEFT, 5);
	m_tInputFile = new wxTextCtrl(p, ID_TXT_INPUTFILE);
	m_tInputFile->SetSizeHints(500, 24);
	sizer3->Add(m_tInputFile, 1, wxEXPAND | wxALL, 5);
	m_bOutputFile = new wxButton(p, ID_BTN_OUTPUTFILE, "Output File");
	sizer3->Add(m_bOutputFile, 0, wxALIGN_LEFT, 5);
	m_tOutputFile = new wxTextCtrl(p, ID_TXT_OUTPUTFILE);
	m_tOutputFile->SetSizeHints(500, 24);
	sizer3->Add(m_tOutputFile, 1, wxEXPAND | wxALL, 5);
	m_bSERIQCPath = new wxButton(p, ID_BTN_SERIQCPATH, "SERI QC Path");
	sizer3->Add(m_bSERIQCPath, 0, wxALIGN_LEFT, 5);
	m_tSERIQCPath = new wxTextCtrl(p, ID_TXT_SERIQCPATH);
	m_tSERIQCPath->SetSizeHints(500, 24);
	sizer3->Add(m_tSERIQCPath, 1, wxEXPAND | wxALL, 5);


	// add both columns to grid sizer
	wxFlexGridSizer* sizerTop = new wxFlexGridSizer(2, 2, wxSize(50, 50));
	sizerTop->Add(sizer0, 1, wxEXPAND);
	sizerTop->Add(sizer1, 1, wxEXPAND);
	sizerTop->Add(sizer2, 1, wxEXPAND);
	sizerTop->Add(sizer3, 1, wxEXPAND);
	sizerTop->AddGrowableCol(1);

	//sizerTop->Add(sizerCol2, 1, wxEXPAND);

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


void MainWindow::OnCommand( wxCommandEvent &evt )
{

	switch( evt.GetId() )
	{
	case wxID_OPEN:
		{
	/*		if (!CloseProject()) return;
			wxFileDialog dlg(this, "Open SAM file", wxEmptyString, wxEmptyString, "SAM Project Files (*.sam)|*.sam", wxFD_OPEN );
			if (dlg.ShowModal() == wxID_OK)
				if( !LoadProject( dlg.GetPath() ) )
					wxMessageBox("Error loading project file:\n\n"
						+ dlg.GetPath() + "\n\n" + m_project.GetLastError(), "Notice", wxOK, this );
	*/	}
		break;
	case wxID_SAVEAS:
		SaveAs();
		break;
	case wxID_SAVE:
		Save();
		break;
	case wxID_EXIT:
		Close();
		break;
	}
}


void MainWindow::Save()
{
	if ( m_projectFileName.IsEmpty() )
	{
		SaveAs();
		return;
	}

}

void MainWindow::SaveAs()
{
	wxFileDialog dlg( this, "Save SAM file as", wxPathOnly(m_projectFileName),
		m_projectFileName, "SAM Project File (*.sam)|*.sam",
		wxFD_SAVE|wxFD_OVERWRITE_PROMPT );
	if ( dlg.ShowModal() == wxID_OK )
	{
		if ( m_projectFileName == dlg.GetPath() )
			return;

		m_projectFileName = dlg.GetPath();
		Save();
	}
	else
		return;
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
