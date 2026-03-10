# SUNI

Solar Uncertianty Integrator (SUNI) determines the uncertainty of high-resolution, subhourly, solar irradiance data by incorporating operational uncertainties
identified by [SERI QC](https://docs.nrel.gov/docs/legosti/old/5608.pdf),
an existing data quality assessment
function, with estimates of radiometer measurement uncertainties determined by the [NLR’s “Radiometer Data Uncertainty Analysis” application](https://midcdmz.nrel.gov/radiometer_uncert.xlsx)
for the specific radiometers in use.

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
