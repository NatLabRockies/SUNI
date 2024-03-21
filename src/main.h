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


#ifndef __sammain_h
#define __sammain_h

// to load binary ui forms and defaults uncomment following
//#define UI_BINARY 1

#include <exception>
#include <memory>

#include <wx/app.h>
#include <wx/scrolwin.h>
#include <wx/frame.h>
#include <wx/config.h>
#include <wx/filehistory.h>
#include <wx/dialog.h>
#include <wx/dataview.h>
#include <wx/button.h>
#include <wx/textctrl.h>
#include <wx/combobox.h>
#include <wx/spinctrl.h>
#include <wx/checkbox.h>
#include <wx/radiobox.h>
#include <wx/gauge.h>

/* Macros for C++11 support */
template <typename T>
struct smart_ptr
{
#if __cplusplus <= 201103L
	typedef std::unique_ptr<T> ptr;
#else
	typedef std::auto_ptr<T> ptr;
#endif
};


class wxPanel;

class SUIException : public std::exception
{
	wxString m_err;
public:
	SUIException( const wxString &err ) : m_err(err) { }
	virtual ~SUIException() throw() { }
	const char *what() const throw() { return (const char*)m_err.c_str(); };
};


class MainWindow : public wxFrame
{
public:
	MainWindow( );

	wxString GetProjectDisplayName();
	wxString GetProjectFileName();
	void SetProjectFileName(const wxString& fn);
	bool OpenConfiguration(const wxString& filename);
	bool SaveConfiguration(const wxString& filename);
	bool UpdateStationIDs(const wxString& dir);

	// Python specific functions
	void LoadPythonConfig();
	bool CheckPythonPackage(const std::string& pip_name);
	void InstallPython();
	void InstallPythonPackage(const std::string& pip_name);


protected:
	void OnClose( wxCloseEvent & );
	void OnCommand( wxCommandEvent & );
	void OnInternalCommand( wxCommandEvent & );
	void OnGHICalUncertainty(wxCommandEvent&);
	void OnDHICalUncertainty(wxCommandEvent&);
	void OnDNICalUncertainty(wxCommandEvent&);
	void UpdateClassCalGHIUncertainty(wxCommandEvent&);
	void UpdateClassCalDNIUncertainty(wxCommandEvent&);
	void UpdateClassCalDHIUncertainty(wxCommandEvent&);
	void UpdateGHIUncertainty(wxCommandEvent&);
	void UpdateDNIUncertainty(wxCommandEvent&);
	void UpdateDHIUncertainty(wxCommandEvent&);
	void OnDateClick(wxMouseEvent& event);

private:
	wxPanel *m_pFiles, *m_pDefaults, *m_pInstruments, *m_pProcessing;
	wxMenuBar *m_mainMenuBar;

	wxButton *m_bInputFile, *m_bOutputFile, *m_bSERIQCPath, *m_bStart, *m_bCancel;

	wxTextCtrl *InputFile, *OutputFile, *SERIQCpath;
	wxTextCtrl *GHIid, *GHImodel, *GHIclassUncert, *GHIcalUncert, *GHIcalDate, *GHIdueDate, *GHIradUncert;
	wxTextCtrl *DNIid, *DNImodel, *DNIclassUncert, *DNIcalUncert, *DNIcalDate, *DNIdueDate, *DNIradUncert;
	wxTextCtrl *DHIid, *DHImodel, *DHIclassUncert, *DHIcalUncert, *DHIcalDate, *DHIdueDate, *DHIradUncert;

//	wxSpinCtrl* MaxQC, * MinDNI, * MaxZEN;
	// wxSpinCtrl for integer values only
	//wxTextCtrl* MaxQC, * MinDNI, * MaxZEN;
	wxTextCtrl *MinDNI, *MaxZEN;
	// MaxQC changed to combo box per specifications v2 p.32
	wxComboBox *MaxQC, *StationID, *Interval, *GHIclass, *DNIclass, *DHIclass;

	wxCheckBox *ExtendedRpt;

	// wxRadioBox does not layout per specification and mockup
	wxRadioButton *DateFormat0, *DateFormat1;

	wxGauge *m_gProgress;

	wxScrolledWindow* p;

	wxString m_projectFileName;

	// track types for consistent loading and saving
	// initialize in constructor (can be a settings file)
	wxArrayString m_typeInt, m_typeDouble;


	void GetInstrumentDataBaseUncertainties(const wxString& instClass, wxString* classUncert, wxString* calUncert);

	bool SetupPython();
	bool InvokePython();
	void LoadConfig();
	std::string GetPythonConfigPath();
	wxString GetAppPath();
	std::string CallPythonModule(const std::string& input_dict_as_text);
	std::string CallPythonModuleWindows(const std::string& input_dict_as_text);
	void CleanOutputString(std::string& output_json);
	void replaceBackslash(std::string& str);

	std::string m_pythonExecPath, m_pythonRunCmd;
	bool m_cancelled;


	DECLARE_EVENT_TABLE();
};

static wxArrayString g_appArgs;
static MainWindow* g_mainWindow = 0;
static wxConfig* g_config = 0;
static wxLogWindow* g_logWindow = 0;


class SUIApp : public wxApp
{
public:

	struct ver { int major, minor, micro; };

	SUIApp();
	/*virtual*/ bool OnInit();
	virtual int OnExit();

	static wxString ReadProxyFile();
	static bool WriteProxyFile( const wxString & );
	static wxString GetAppPath();
	static wxString GetRuntimePath();
	static wxString GetUserLocalDataDir();
	static wxConfig &Settings();
	static MainWindow *Window();
	static wxFileHistory &FileHistory();
	static wxArrayString RecentFiles();
	static void ShowHelp( const wxString &context = wxEmptyString );

	static wxWindow *CurrentActiveWindow();

/*
	static std::string GetPythonConfigPath();
	static void LoadPythonConfig();
	static bool CheckPythonPackage(const std::string& pip_name);
	static void InstallPython();
    static void InstallPythonPackage(const std::string& pip_name);
*/

};


DECLARE_APP( SUIApp );


class wxCheckBox;
class wxMetroButton;
class wxMetroListBox;
class wxMetroDataViewCtrl;




#endif

