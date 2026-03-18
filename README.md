# SUNI

Solar Uncertianty Integrator (SUNI) determines the uncertainty of high-resolution, subhourly, solar irradiance data by incorporating operational uncertainties
identified by [SERI QC](https://docs.nrel.gov/docs/legosti/old/5608.pdf),
an existing data quality assessment
function, with estimates of radiometer measurement uncertainties determined by the [NLR’s “Radiometer Data Uncertainty Analysis” application](https://midcdmz.nrel.gov/radiometer_uncert.xlsx)
for the specific radiometers in use.


## Installation

We offer two installations options - Graphical User Interface (GUI) and Command Line Interface (CLI) to explore SUNI.

### GUI

The exectuables can be downloaded for Windows and MacOS from the Releases page of this repository.

Please allow a few mintues to complete the one-time installation. Once installed, you will be able to begin a process configuration.

#### Example Workflow
Three types of input files are required to run SUNI software. Refer to the ``example`` folder to understand what input files are needed.

1. Configuration File (refer to ``example/sample_config.json``) with the contents as follows:

```
{
    "InputFile": "SRRL2004_01_testing.csv",
    "OutputFile": "SRRL2004_01_Unc.csv",
    "SERIQCpath": ".",
    "StationID": "NRELSR",
    "Interval": 1,
    "GHIid": "14003",
    "GHImodel": "CMP22",
    "GHIclass": "A",
    "GHIclassUncert": 2.4,
    "GHIclassModFlg": 1,
    "GHIcalUncert": 1.9,
    "GHIcalDate": "2019-05-05",
    "GHIdueDate": "2020-05-05",
    "GHIradUncert": 3.1,
    "DNIid": "190042",
    "DNImodel": "CHP1",
    "DNIclass": "A",
    "DNIclassUncert": 0.9,
    "DNIclassModFlg": 1,
    "DNIcalUncert": 0.75,
    "DNIcalDate": "2019-05-05",
    "DNIdueDate": "2020-05-05",
    "DNIradUncert": 1.2,
    "DHIid": "140033",
    "DHImodel": "CMP22",
    "DHIclass": "A",
    "DHIclassUncert": 2.4,
    "DHIclassModFlg": 1,
    "DHIcalUncert": 1.9,
    "DHIcalDate": "2019-05-05",
    "DHIdueDate": "2020-05-05",
    "DHIradUncert": 3.1,
    "MaxQC": 89,
    "MinDNI": 25.0,
    "MaxZEN": 80.0,
    "MaxSysUncert": 100.0,
    "ExtendedRpt": 0,
    "DateFormat": 0
}
```


2. Solar Irradiance Data (refer to ``example/SRRL2004_01_testing.csv``) with Date, Time, GHI, DNI, DHI fields.

Note that the name should be matched with ``InputFile`` from the configuration file.

3. SERI QC File (refer to ``example/s_NRELSR.qc0``)


Find ``Open Configuration`` from the ``File`` menu, and choose the configuration file path.
This will automatically fill the blanks with the paths found.

![Select Config File](examples/screenshots/select-config.png)

If you encounter the SERI QC file not found error,

![SERI QC Warning Message](examples/screenshots/seriqc-warning.png)

Please click ``SERI QC Path`` button and verify its location.

If you encounter the Input file not found error,

![Input File Warning Message](examples/screenshots/inputfile-warning.png)

Please click ``Input File`` button and verify its location.

This should now look as follows. We highly recommend to put full file paths (not relative path).

![File Path Correction](examples/screenshots/filepath-corrected.png)

Please review all the contents if it is extracted correctly. Click ``Create Extended Report`` if you wish to generate it. Data format should match with the one from your solar irradiance data file.

Once everything is ready, click ``Start`` button to start processing. You might see the progress through the bar below. For your reference, it took less than 10 seconds to run the example.

Once it is completed, the report will pop up. And the Output file and reports can be found under your working folder.

![Report](examples/screenshots/report.png)

```
Uncertainty Processing Report for SRRL2004_01_testing.csv
Station ID: NRELSR (SRRL)
QC0 File: s_NRELSR.qc0
Processing date: 03/18/2026 16:55
From 1/1/2004 0:00 to 1/2/2004 8:00 (1-minute interval)

System Configuration:
GHI: s/n  14003 | Class: A | Class Uncert: +/-2.4%*| Cal Uncert: +/-1.9% | Cal Date: 2019-05-05 | Due Date: 2020-05-05 | Radiometer Uncert: +/-3.1%
DNI: s/n 190042 | Class: A | Class Uncert: +/-0.9%*| Cal Uncert: +/-0.8% | Cal Date: 2019-05-05 | Due Date: 2020-05-05 | Radiometer Uncert: +/-1.2%
DHI: s/n 140033 | Class: A | Class Uncert: +/-2.4%*| Cal Uncert: +/-1.9% | Cal Date: 2019-05-05 | Due Date: 2020-05-05 | Radiometer Uncert: +/-3.1%
   * indicates user override
SERI QC Max: 89
Zenith Angle Max: 80.0
DNI Min: 25.0
System Uncertainty Max: 100.0

Input Data Records: 1921
Three-component records: 0 (0.0%)
Above SERIQC Max: 0 (0.0%)
Above Zenith Angle Max: 0 (0.0%)
Below DNI Minimum: 0 (0.0%)
Above Max System Uncertainty: 0 (0.0%)
Mathematically Invalid: 0 (0.0%)
Total Eligible Uncertainty Records: 0 (0.0%)

GHI Mean U95: +/--9900.00% | Standard deviation: -9900.00
DNI Mean U95: +/--9900.00% | Standard deviation: -9900.00
DHI Mean U95: +/--9900.00% | Standard deviation: -9900.00

Urads Uncertainty Mean: +/--9900.00%
Mean of System Uncertainty ABS: -9900.00%
Field Uncertainty Mean: +/--9900.00%
```

### CLI

From a desired code directory, download this repository using ``git clone git@github.com:NREL/SUNI.git``

1. Create ``suni`` environment and install package
    1) Create a conda env: ``conda create -n suni python=3.11``
    2) Activate the newly-created environment using the command: ``conda activate suni``
    3) cd into the repo cloned in 1.
    4) Install ``suni`` and its dependencies by running: ``pip install .``

2. Check that ``suni`` was installed successfully
    1) From any directory, run the following command. This should return the
       help pages for the CLI.

        - ``suni --help``

You can now use the `sample config <https://github.com/NREL/SUNI/blob/main/examples/sample_config.json>`_
as a template to set up your own runs and then execute them using

``suni config.json``




<!-- Attached is the latest specifications document with revised user interface and changes to pseudocode. In summary:
![image](https://github.com/sjanzou/SolarUncertaintyIntegrator/assets/6498311/3d854ba1-9b1c-4768-a86a-ca733d407783)

 
With modification of the instrument uncertainty section of the UI, I propose this process:
* Enter instrument ID freehand
* Enter Instrument model freehand
* Use a pulldown to select instrument class (will be simple A, B, or C)
* The pulldown selection will look up and populate the Class Uncert and Cal uncert fields
* The user can, and likely will, modify the Cal Uncert field. The Class Uncert field is read only by user
* The user will enter Cal and Due Dates freehand
* A specific user action, such as doubleclick, will perform the Radiometer Uncert calculation.
* The Radiometer Uncert field will be populated by the uncertainty calculation (field will be read only by user)
* Any change to any instrument field will blank the Radiometer Uncert field to force a recalculation by user.
* Any suggestions to improve this from the user’s perspective?
 
Other notable parts of the document for your attention (based on document bottom page number)
 
Page 33. Implementation of the Cancel control. You may have this already figured out, but it is not so simple to me. Once the Python process is started, some method of communication will be required to quickly deliver a cancel command from the UI to the running process. The process could perhaps be killed using a captured process ID, but yuk, there are files open and cleanup is necessary before control returns to the UI. Polling a file would be costly. Shared memory? Having Python post a cancel popup when running? The pseudocode implements the cancel in the file loop near the bottom of page 37 (though Python might not implement the read/process loop that way).
 
Paage 37. Progress bar (near top of file loop). If I understand Steve’s email of 12/26/23 12:04 a.m., a file can be used to pass percent back to the UI. This can probably be done at a coarse interval such as 5% and still be useful.
 
Page 59. Instrument database. This has been greatly simplified with Aron’s new uncertainty paradigm. It is now just two small files holding the class uncertainty and default calibration uncertainty. This could be easily hard-wired into the code, but I chose the file approach with the possibility (likelihood?) that the numbers will change in the future or that other classes could be added. It’s easier to drop in new data files than redistribute new program files. Any thoughts on this?
 
Page 60. Configuration files. You likely have a better way to implement and name configuration files. Take it and run with it! -->
