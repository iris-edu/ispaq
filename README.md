# ISPAQ - IRIS System for Portable Assessment of Quality

ISPAQ is a python client that allows seismic data scientists and instrumentation operators
to run data quality metrics on their own workstation, using much of same code base as is
used in IRIS's MUSTANG data quality web service.

Users have the ability to create personalized _preference files_ that list combinations
of station specifiers and statistical metrics of interest, such that they can be run
repeatedly over data from many different time periods.

ISPAQ offers the option for access to FDSN Web Services to get raw data and metadata directly
from selected data centers supporting the FDSN protocol.  Alternately, users can ready local files
and metadata on their own workstations, possibly sourced directly from instrumentation, and construct
on-the-spot data quality analyses on that data.

Output is provided in csv format for tabular metrics, and Probability Density Functions can be
plotted to PNG image files.

The business logic for MUSTANG metrics is emulated through ObsPy and custom Python code and the
core calculations are performed using the same R packages as used by MUSTANG.  Currently, only
SEED formatted data and StationXML metadata is supported as source seismogram material.  RESP files
and FDSN Web Service event files are also used in some situations.

# Background

[IRIS](http://www.iris.edu/hq/) (Incorporated Research Institutions for Seismology)
 has developed a comprehensive quality assurance system called
[MUSTANG](http://service.iris.edu/mustang/).

The MUSTANG system was built to operate at the IRIS DMC and is not generally portable. 
The key MUSTANG component is the Metric Calculators, and those were always
intended to be shared.  Whereas the results of MUSTANG calculations are stored in a database, and
provided to users via web services, ISPAQ is intended to reproduce the process of calculating these
metrics from the source data, such that results can be verified and alternate data sources not
available in MUSTANG can be processed at the user's initiative.

IRIS currently has close to 50 MUSTANG algorithms that calculate metrics, most 
written in R, that are now publicly available in the CRAN repository under the name 
[IRISMustangMetrics](http://cran.r-project.org/).  ISPAQ comes with the latest version of these packages
available in CRAN and we provide an update capability in ISPAQ to allow users to seamlessly upgrade
their R packages as IRIS provides them.

The R package IRISMustangMetrics cannot include workflow and data selection
business logic implemented at scale in MUSTANG, as much of this code is non-portable.  However, it
is the goal of ISPAQ to provide a similar set of business logic in Python, such that the end result
is identical or very similar to the results you will see in MUSTANG.  The end result is a lightweight
and portable version of MUSTANG that users are free to leverage on their own hardware.

# Installation

ISPAQ must be installed on the user's system using very reliable tools for package transfer.  ISPAQ is being
distributed through _GitHub_, via IRIS's public repository.  You will use a simple command to get a copy of
the latest stable release.  In addition, you will use the _miniconda_ python package manager to create a
customized environment designed to run ISPAQ properly.  This will include an localized installation of ObsPy and R.
Just follow the steps below to begin running ISPAQ.

## Download the Source Code

You must first have ```git``` installed your system. Once you do, just:

```
git clone https://github.com/iris-edu/ispaq.git
```

Onced finished, ```cd ispaq``` before setting up the Anaconda environment.

## Install the Anaconda Environment

[Anaconda](https://www.continuum.io/why-anaconda) is quickly becoming the *defacto*
package manager for scientific applications written python or R. The following instructions
assume that you have installed [Miniconda](http://conda.pydata.org/miniconda.html) for
your system.

We will use conda to simplify installation and ensure that all dependencies
are installed with compatible verions.

By setting up a [conda virual environment](http://conda.pydata.org/docs/using/envs.html),
we assure that our ISPAQ installation is entirely separate from any other installed software.

### Alternative 1 for MacOSX ) Creating an environment from a 'spec' file

This method does everything at once.

```
conda create -n ispaq --file ispaq-explicit-spec-file.txt
source activate ispaq
```

> Note: if `source activate ispaq` does not work because your shell is csh/tcsh instead of bash
you will need to add the ispaq environment to your PATH in the terminal window that you are using.
e.g., `setenv PATH ~/miniconda2/envs/ispaq/bin:$PATH`)

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD INSTALL seismicRoll_1.1.2.tar.gz 
R CMD INSTALL IRISSeismic_1.3.9.tar.gz
R CMD INSTALL IRISMustangMetrics_2.0.2.tar.gz 
```

### Alternative 2 for MacOSX or Linux ) Creating an environment by hand

This method requires more user intput but lets you see what is being installed.

```
conda create --name ispaq python=2.7
source activate ispaq
conda install pandas=0.18.1
conda install -c conda-forge obspy=1.0.2
conda install -c r r=3.2.2
conda install -c r r-devtools=1.9.1
conda install -c r r-rcurl=1.95_4.7
conda install -c r r-xml=3.98_1.3 
conda install -c r r-dplyr=0.4.3
conda install -c r r-quadprog=1.5.5
conda install -c bioconda r-signal=0.7.6
conda install -c bioconda r-pracma=1.8.8
conda install -c bioconda rpy2=2.7.8
```

> Note: if `source activate ispaq` does not work because your shell is csh/tcsh instead of bash
you will need to add the ispaq environment to your PATH in the terminal window that you are using.
e.g., `setenv PATH ~/miniconda2/envs/ispaq/bin:$PATH`

See what is installed in our (ispaq) environment with:

```
conda list
...
```

Now install the IRIS R packages:

```
R CMD INSTALL seismicRoll_1.1.2.tar.gz 
R CMD INSTALL IRISSeismic_1.3.9.tar.gz
R CMD INSTALL IRISMustangMetrics_2.0.2.tar.gz 
```

# First use

Every time you use ISPAQ you must ensure that you are running in the proper Anaconda
environment. If you followed the instructions above you only need to:

```
source activate ispaq
```

after which your prompt should begin with ```(ispaq) ```.

> Note: if you are using a csh/tcsh shell there will be no prompt change.

A list of command line options is available with the ```--help``` flag:

```
(ispaq) $ ./run_ispaq.py --help
usage: run_ispaq.py [-h] [-V] [--starttime STARTTIME] [--endtime ENDTIME]
                    [-M METRICS] [-S STATIONS] [-P PREFERENCES_FILE]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-A]
                    [-U]

ispaq.ispaq: provides entry point main().

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  --starttime STARTTIME
                        starttime in ISO 8601 format
  --endtime ENDTIME     endtime in ISO 8601 format
  -M METRICS, --metrics METRICS
                        metric alias, defined in preference file
  -S STATIONS, --stations STATIONS
                        stations alias, defined in preference file
  -P PREFERENCES_FILE, --preferences-file PREFERENCES_FILE
                        path to preference file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        log level printed to console
  -A, --append          append to TRANSCRIPT file rather than overwriting
  -U, --update-r        check CRAN for more recent IRIS Mustang R package
                        versions
```

When calculating metrics, valid arguments for -M, -S, and --starttime must be provided. 
If -P is not provided, ISPAQ uses the default preference file located at ispaq/preference_files/default.txt.
If --log-level is not specified, the default log-level is INFO.

When --starttime is invoked without --endtime, metrics are run for a single day. Metrics that are defined  
as daylong metrics (24 hour window, see metrics documentation at [MUSTANG](http://services.iris.edu/mustang/measurements/1))
will be calculated for the time period 00:00:00-23:59:59.9999. An endtime of YYYY-DD-MM is interpreted as 
YYYY-DD-MM 00:00:00 so that e.g., --starttime=2016-01-01 --endtime=2016-01-02 will calculate one day of metrics. 
When an endtime greater than one day is requested, metrics will be calculated for multiple single days. 

The option -U should be used alone. No metrics are calculated when this option is invoked.

### Preference files

The ISPAQ system is designed to be configurable through the use of *preference files*.
These are usually located in the ```preference_files/``` directory.  Not surprisingly, the default
preference file is ```preference_files/default.txt``. This file is self describing
with the following comments in the header:

```
# Preferences fall into four categories:
#  * Metrics -- aliases for user defined combinations of metrics (Use with -M)
#  * Station SNCLs -- aliases for user defined combinations of SNCL patterns (Use with -S)
#                     SNCL patterns are station names formatted as network.station.location.channel
#                     wildcards * and ? are allowed (*.*.*.*)
#  * Data_Access -- FDSN web services or local files
#  * Preferences -- additional user preferences
#
# This file is in a very simple and somewhat forgiving format.  After
# each category heading, all lines containing a colon will be interpreted
# as key:value and made made available to ISPAQ.
#
# Text to the right of `#` are comments and are ignored by the parser

# Example invocations that use these default preferences:
#
#   run_ispaq.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO -A
#   run_ispaq.py -M gaps -S gaps --starttime 2013-01-05 --log-level INFO -A
#   run_ispaq.py -M spikes -S spikes --starttime 2013-01-03 --log-level INFO -A
#   run_ispaq.py -M STALTA -S STALTA --starttime 2013-06-02 --log-level INFO -A
#   run_ispaq.py -M SNR -S SNR --starttime 2013-06-02 --log-level INFO -A
#   run_ispaq.py -M PSD -S PSD --starttime 2011-05-18 --log-level INFO -A
#   run_ispaq.py -M PDF -S PDF --starttime 2013-06-01 --log-level INFO -A
#   run_ispaq.py -M crossTalk -S crossTalk --starttime 2013-09-21 --log-level INFO -A
#   run_ispaq.py -M pressureCorrelation -S pressureCorrelation --starttime 2013-05-02 --log-level INFO -A
#   run_ispaq.py -M crossCorrelation -S crossCorrelation --starttime 2011-01-01 --log-level INFO -A
#   run_ispaq.py -M orientationCheck -S orientationCheck --starttime 2015-11-24 --log-level INFO -A
#   run_ispaq.py -M transferFunction -S transferFunction --starttime 2012-10-03 --log-level INFO -A
```

### Output files

ISPAQ will always create a log file named ```ISPAQ_TRANSCRIPT.log``` to record all actions taken
and all logging messages generated during processing.

Results of metrics calculations will be written to .csv files using the following naming scheme:

*MetricSet*\_*StationSet*\_*date*\__*businessLogic*.csv

or

*MetricSet*\_*StationSet*\_*startdate*\_*enddate*\_*businessLogic*.csv

where businessLogic corresponds to which script is invoked:

| businessLogic | ISPAQ script | metrics |
| ----------|--------------|---------|
| simpleMetrics | simple_metrics.py | most metrics |
| SNRMetrics | SNR_metrics.py | sample_snr   |
| PSDMetrics | PSD_metrics.py | pct_above_nhnm, pct_below_nlnm, dead_channel_exp/lin/gsn |
| crossTalkMetrics | crossTalk_metrics.py | cross_talk |
| pressureCorrelationMetrics | pressureCorrelation_metrics.py | pressure_effects | 
| crossCorrelationMetrics | crossCorrelation_metrics.py | polarity_check | 
| orientationCheckMetrics | orientationCheck_metrics.py | orientation_check | 
| transferMetrics | transferFunction_metrics.py | transfer_function |

The MetricSet PSDText (or any user defined set with metrics psd_corrected or pdf_text) will generate 
corrected PSDs and PDFs in files named:

* *MetricSet*\_*StationSet*\_*date*\_*SNCL*\__correctedPSD.csv
* *MetricSet*\_*StationSet*\_*date*\_*SNCL*\__PDF.csv

while the MetricSet PDF (metric pdf_plot) will generate PDF plot images as:

* *SNCL*\.*JulianDate*\_PDF.png

### Command line invocation

Example invocations are found  in the ```EXAMPLES``` file. 

You can modify the information printed to the console by modifying the ```--log-level```.
To see detailed progress information use ```--log-level DEBUG```. To hide everything other
than an outright crash use ```--log-level CRITICAL```.

The following example demonstrates what will should see. 

```
(ispaq) $ run_ispaq.py -M basicStats -S basicStats --starttime 2010-04-20 --log-level INFO
2016-08-26 15:50:43 - INFO - Running ISPAQ version 0.7.6 on Fri Aug 26 15:50:43 2016

/Users/jonathancallahan/miniconda2/envs/ispaq/lib/python2.7/site-packages/matplotlib/font_manager.py:273: UserWarning: Matplotlib is building the font cache using fc-list. This may take a moment.
  warnings.warn('Matplotlib is building the font cache using fc-list. This may take a moment.')
2016-08-26 15:51:02 - INFO - Calculating simple metrics for 3 SNCLs.
2016-08-26 15:51:02 - INFO - 000 Calculating simple metrics for IU.ANMO.00.BH1
2016-08-26 15:51:04 - INFO - 001 Calculating simple metrics for IU.ANMO.00.BH2
2016-08-26 15:51:07 - INFO - 002 Calculating simple metrics for IU.ANMO.00.BHZ
2016-08-26 15:51:09 - INFO - Writing simple metrics to basicStats_basicStats_2010-04-20__simpleMetrics.csv.

2016-08-26 15:51:09 - INFO - ALL FINISHED!
(ispaq) $
```

> Note: Please ignore the warning message from matplotlib. It will only occur on first use. 

### Using Local Data Files

To be added ...

### Current List of Metrics

> Note: when using local data files, metrics based on miniSEED act_flags, io_flags, and timing blockette 1001 are not valid. 
Thse metrics are calibration_signal, clock_locked, event_begin, event_end, event_in_progress, timing_correction, 
and timing_quality.

* **amplifier_saturation**:
The number of times that the 'Amplifier saturation detected' bit in the 'dq_flags' byte is set within a miniSEED file. 
This data quality flag is set by some dataloggers in the fixed section of the miniSEED header. The flag was intended to 
indicate that the preamp is being overdriven, but the exact meaning is datalogger-specific.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/amplifier_saturation/)

* **calibration_signal**:
The number of times that the 'Calibration signals present' bit in the 'act_flags' byte is set within a miniSEED file. 
A value of 1 indicates that a calibration signal was being sent to that channel.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/calibration_signal/)

* **clock_locked**:
The number of times that the 'Clock locked' bit in the 'io_flags' byte is set within a miniSEED file. This clock flag 
is set to 1 by some dataloggers in the fixed section of the miniSEED header to indicate that its GPS has locked with 
enough satellites to obtain a time/position fix.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/clock_locked/)

* **cross_talk**:
The correlation coefficient of channel pairs from the same sensor. Data windows are defined by seismic events. 
Correlation coefficients near 1 may indicate cross-talk between those channels.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/cross_talk/)

* **dead_channel_exp**:
Dead channel metric - exponential fit. This metric is calculated from the mean of all the PSDs generated 
(typically 47 for a 24 hour period). Values of the PSD mean curve over the band expLoPeriod:expHiPeriod are fit to 
an exponential curve by a least squares linear regression of log(PSD mean) ~ log(period). The dead_channel_exp metric 
is the standard deviation of the fit residuals of this regression. Lower numbers indicate a better fit and a higher 
likelihood that the mean PSD is exponential - an indication of a dead channel.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/dead_channel_exp/)

* **dead_channel_gsn**:
A boolean measurement providing a TRUE or FALSE indication that the channel exhibits a 5dB deviation below the NLNM 
in the 4 to 8s period band as measured using a McNamara PDF noise matrix. The TRUE condition is indicated with a numeric 
representation of '1' and the FALSE condition represented as a '0'.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/dead_channel_gsn/)

* **dead_channel_lin**:
Dead channel metric - linear fit. This metric is calculated from the mean of all the PSDs generated (typically 47 
for a 24 hour period). Values of the PSD mean curve over the band linLoPeriod:linHiPeriod are fit to a linear curve 
by a least squares linear regression of PSD mean ~ log(period). The dead_channel_lin metric is the standard deviation 
of the fit residuals of this regression. Lower numbers indicate a better fit and a higher likelihood that the mean PSD 
is linear - an indication that the sensor is not returning expected seismic energy.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/dead_channel_lin/)

* **digital_filter_charging**:
The number of times that the 'A digital filter may be charging' bit in the 'dq_flags' byte is set within a miniSEED file. 
Data samples acquired while a datalogger is loading filter parameters - such as after a reboot - may contain a transient.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/digital_filter_charging/)

* **digitizer_clipping**:
The number of times that the 'Digitizer clipping detected' bit in the 'dq_flags' byte is set within a miniSEED file. 
This flag indicates that the input voltage has exceeded the maximum range of the ADC.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/digitizer_clipping/)

* **event_begin**:
The number of times that the 'Beginning of an event, station trigger' bit in the 'act_flags' byte is set within a miniSEED 
file. This metric can be used to quickly identify data days that may have events. It may also indicate when trigger 
parameters need adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_begin/)

* **event_end**:
The number of times that the 'End of an event, station detrigger' bit in the 'act_flags' byte is set within a miniSEED 
file. This metric can be used to quickly identify data days that may have events. It may also indicate when trigger 
parameters need adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_end/)

* **event_in_progress**:
The number of times that the 'Event in progress' bit in the 'act_flags' byte is set within a miniSEED file. This metric 
can be used to quickly identify data days that may have events. It may also indicate when trigger parameters need 
adjusting at a station.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/event_in_progress/)

* **glitches**:
The number of times that the 'Glitches detected' bit in the 'dq_flags' byte is set within a miniSEED file. This metric can 
be used to identify data with large filled values that data users may need to handle in a way that they don't affect 
their research outcomes.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/glitches/)

* **max_gap**:
Indicates the size of the largest gap encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_gap/)

* **max_overlap**:
Indicates the size of the largest overlap in seconds encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_overlap/)

* **max_stalta**:
The STALTAMetric function calculates the maximum of STA/LTA of the incoming seismic signal over a 24 hour period. In order 
to reduce computation time of the rolling averages, the averaging window is advanced in 1/2 second increments.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/max_stalta/)

* **missing_padded_data**:
The number of times that the 'Missing/padded data present' bit in the 'dq_flags' byte is set within a miniSEED file. This 
metric can be used to identify data with padded values that data users may need to handle in a way that they don't affect
their research outcomes.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/missing_padded_data/)

* **num_gaps**:
This metric reports the number of gaps encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_gaps/)

* **num_overlaps**:
This metric reports the number of overlaps encountered in a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_overlaps/)

* **num_spikes**:
This metric uses a rolling Hampel filter, a median absolute deviation (MAD) test, to find outliers in a timeseries. 
The number of discrete spikes is determined after adjacent outliers have been combined into individual spikes.
NOTE: not to be confused with the spikes metric, which is an SOH flag only.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_spikes/)

* **orientation_check**:
Determine channel orientations by rotating horizontal channels until the resulting radial component maximizes 
cross-correlation with the Hilbert transform of the vertical component. This metric uses Rayleigh waves from large, 
shallow events.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/num_spikes/)

* **pct_above_nhnm**:
Percent above New High Noise Model. Percentage of Probability Density Function values that are above the New High Noise 
Model. This value is calculated over the entire time period.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pct_above_nhnm/)

* **pct_below_nlnm**:
Percent below New Low Noise Model. Percentage of Probability Density Function values that are below the New Low Noise 
Model. This value is calculated over the entire time period.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pct_below_nlnm/)

* **pdf_plot**:
Probability density function plots. Generates one plot per station-day.
[Reference](https://profile.usgs.gov/myscience/upload_folder/ci2012Feb2217152844121McNamaraBuland_BSSA.pdf)

* **pdf_text**:
Probability density function text output (frequency, power, hits, target, starttime, endtime)
[Reference](https://profile.usgs.gov/myscience/upload_folder/ci2012Feb2217152844121McNamaraBuland_BSSA.pdf)

* **percent_availability**:
The portion of data available for each day is represented as a percentage. 100% data available means full coverage of 
data for the reported start and end time.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/percent_availability/)

* **polarity_check**:
The signed cross-correlation peak value based on the cross-correlation of two neighboring station channels in proximity 
to a large earthquake signal. A negative peak close to 1.0 can indicate reversed polarity.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/polarity_check/)

* **pressure_effects**:
The correlation coefficient of a seismic channel and an LDO pressure channel. Large correlation coefficients may 
indicate the presence of atmospheric effects in the seismic data.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/pressure_effects/)

* **psd_corrected**:
Power spectral density values, corrected for instrument response, in text format (starttime, endtime, 
frequency, power).
[Documentation](http://service.iris.edu/mustang/noise-psd/docs/1/help/)

* **sample_max**:
This metric reports largest amplitude value in counts encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_max/)

* **sample_mean**:
This metric reports the average amplitude value in counts over a 24-hour window. This mean is one measure of the 
central tendency of the amplitudes that is calculated from every amplitude value present in the time series. The mean 
value itself may not occur as an amplitude value in the times series.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_mean/)

* **sample_median**:
This metric reports the middle amplitude value in counts of sorted amplitude values from a 24-hour window. This median 
is one measure of the central tendency of the amplitudes in a time series when values are arranged in sorted order. 
The median value itself always occurs as an amplitude value in the times series.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_median/)

* **sample_min**:
This metric reports smallest amplitude value in counts encountered within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_min/)

* **sample_rms**:
Displays the RMS variance of trace amplitudes within a 24-hour window.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_rms/)

* **sample_snr**:
A ratio of the RMS variance calculated from data 30 seconds before and 30 seconds following the predicted 
first-arriving P phase.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_snr/)

* **sample_unique**:
This metric reports the number (count) of unique values in data trace over a 24-hour window. 
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/sample_unique/)

* **spikes**:
The number of times that the 'Spikes detected' bit in the 'dq_flags' byte is set within a miniSEED file. This data 
quality flag is set by some dataloggers in the fixed section of the miniSEED header when short-duration spikes have 
been detected in the data. Because spikes have shorter duration than the natural period of most seismic sensors, spikes 
often indicate a problem introduced at or after the datalogger.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/spikes/)

* **suspect_time_tag**:
The number of times that the 'Time tag is questionable' bit in the 'dq_flags' byte is set within a miniSEED file. 
This metric can be used to identify stations with GPS locking problems and data days with potential timing issues.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/suspect_time_tag/)

* **telemetry_sync_error**:
The number of times that the 'Telemetry synchronization error' bit in the 'dq_flags' byte is set within a miniSEED file. 
This metric can be searched to determine which stations may have telemetry problems or to identify or omit gappy data 
from a data request.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/telemetry_sync_error/)

* **timing_correction**:
The number of times that the 'Time correction applied' bit in the 'act_flags' byte is set within a miniSEED file. 
This clock quality flag is set by the network operator in the fixed section of the miniSEED header when a timing correction 
stored in field 16 of the miniSEED fixed header has been applied to the data's original time stamp. A value of 0 means 
that no timing correction has been applied.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/timing_correction/)

* **timing_quality**:
Daily average of the SEED timing quality stored in miniSEED blockette 1001. This value is vendor specific and expressed 
as a percentage of maximum accuracy. Percentage is NULL if not present in the miniSEED.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/timing_quality/)

* **transfer_function**:
Transfer function metric consisting of the gain ratio, phase difference and magnitude squared of two co-located sensors.
[Documentation](http://service.iris.edu/mustang/metrics/docs/1/desc/transfer_function/)

