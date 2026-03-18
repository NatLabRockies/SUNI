# SUNI

Solar Uncertainty Integrator (SUNI) estimates uncertainty for high-resolution, subhourly solar irradiance datasets. The framework combines quality screening from SERI QC with radiometer measurement uncertainty modeling to produce uncertainty-annotated outputs and summary reports.

## Key Features

- Supports one-minute and other subhourly irradiance datasets
- Integrates SERI QC flags into uncertainty processing
- Produces CSV outputs with component-level uncertainty fields
- Generates human-readable processing reports
- Available as both a GUI application and a Python CLI workflow

## Installation

SUNI can be used through either the CLI or the GUI.

### CLI Installation

From the repository root:

```bash
conda create -n suni python=3.11 -y
conda activate suni
pip install -e ./CLI/SERIQC
pip install -e ./CLI/SUNI
```

Confirm the CLI is installed:

```bash
suni --help
```

### GUI Installation

1. Download the installer for your platform from this repository's Releases page.
2. Complete the installation and launch the SUNI application.
3. Use the example files in `examples/` to validate your first run.

## How to Run

### Input Requirements

SUNI expects three inputs:

1. A JSON or INI configuration file
2. A solar irradiance CSV containing date/time and irradiance values
3. A SERI QC station file (`.qc0`)

See `examples/sample_config.json` for the expected configuration schema.

### CLI Workflow
Use the provided example files:

- Configuration: `examples/sample_config.json`
- Input data: `examples/SRRL2004_01_testing.csv`
- SERI QC file: `examples/s_NRELSR.qc0`

Run SUNI with:

```bash
suni examples/sample_config.json
```

The run creates:

- A processed output CSV (from the `OutputFile` value in the config)
- A text report named `<output_stem>_report.txt`

### GUI Workflow

The following walkthrough uses the example files in `examples/` and mirrors the GUI flow shown in `examples/screenshots/`.

1. Launch SUNI and open a configuration file.
	- In the application menu, select File -> Open Configuration.
	- Choose `examples/sample_config.json`.

	![Select Config File](examples/screenshots/select-config.png)

2. Confirm the configuration values are populated.
	- SUNI should populate input, output, and SERI QC fields based on the configuration.
	- Verify that paths point to your local copies of the example files.

3. Resolve a missing SERI QC path warning if shown.
	- If you see a SERI QC warning, click the SERI QC Path control and select the folder containing the `.qc0` file.

	<img src="examples/screenshots/seriqc-warning.png" alt="SERI QC Warning Message" width="420" />

4. Resolve a missing input file warning if shown.
	- If you see an input file warning, click the Input File control and select the irradiance CSV.

	<img src="examples/screenshots/inputfile-warning.png" alt="Input File Warning Message" width="420" />

5. Verify corrected paths before execution.
	- Confirm Input File, Output File, and SERI QC Path are all valid.
	- Absolute paths are recommended for reliability.

	![File Path Correction](examples/screenshots/filepath-corrected.png)

6. Review processing options.
	- Confirm date format matches your data file.
	- Enable extended reporting if required.

7. Start processing.
	- Click Start and monitor the progress bar.
	- Typical runtime for the included example is short (often under 10 seconds, system dependent).

8. Review results.
	- A report dialog appears when processing completes.
	- The output CSV and report text file are written to the configured output location.

	![Report](examples/screenshots/report.png)


## License and Citation

Please refer to repository licensing and project policy files for licensing terms and citation guidance.
