"""
ISPAQ Business Logic for Simple Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

from __future__ import (absolute_import, division, print_function)

import math
import numpy as np
import pandas as pd

from obspy import UTCDateTime

from .concierge import NoAvailableDataError

from . import utils
from . import irisseismic
from . import irismustangmetrics

def simple_metrics(concierge):
    """
    Generate *simple* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expediter.

    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger

    # Default parameters from IRISMustangUtils::generateMetrics_simple
    channelFilter = '.*'

    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All UN-available SNCLs ----------------------------------------------

    # TODO:  Create percent_availability metric with   0% available

    # ----- All available SNCLs -------------------------------------------------


    start = concierge.requested_starttime
    end = concierge.requested_endtime
    delta = (end-start)/(24*60*60)
    nday=int(delta)+1

    if nday > 1 and concierge.station_client is None:
        try:
            initialAvailability = concierge.get_availability(starttime=start, endtime=end)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.error("concierge.get_availability() failed: '%s'" % e)
            return None

    # Loop over days
    for day in range(nday):
        starttime = (start + day * 86400)
        starttime = UTCDateTime(starttime.strftime("%Y-%m-%d") + "T00:00:00Z")
        endtime = starttime + 86400

        if starttime == end:
            continue

        try:
            availability = concierge.get_availability(starttime=starttime, endtime=endtime)
        except NoAvailableDataError as e:
            raise
        except Exception as e:
            logger.debug(e)
            logger.error('concierge.get_availability() failed')
            return None 

        # NEW: If the station has no data, then skip it (used to raise NoAvailableDataError)
        if availability is None:
            logger.debug("skipping %s with no available data" % (starttime.date))
            continue

        # Apply the channelFilter
        availability = availability[availability.channel.str.contains(channelFilter)]      

        # function metadata dictionary
        function_metadata = concierge.function_by_logic['simple']

        logger.info('Calculating simple metrics for %d SNCLs on %s' % (availability.shape[0], str(starttime).split('T')[0]))

        # Loop over rows of the availability dataframe
        for (index, av) in availability.iterrows():

            logger.info('%03d Calculating simple metrics for %s' % (index, av.snclId))

            # Get the data ----------------------------------------------

            # NOTE:  Use the requested starttime, not just what is available
            try:
                r_stream = concierge.get_dataselect(av.network, av.station, av.location, av.channel, starttime, endtime, ignoreEpoch=True)
            except Exception as e:
                if str(e).lower().find('no data') > -1:
                    logger.info('No data available for %s' % (av.snclId))
                else:
                    logger.warning('No data available for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
                continue

            # Run the Gaps metric ----------------------------------------

            if function_metadata.has_key('gaps'):
                try:
                    df = irismustangmetrics.apply_simple_metric(r_stream, 'gaps')
                    dataframes.append(df)
                except Exception as e:
                    logger.warning('"gaps" metric calculation failed for %s: %s' % (av.snclId, e))
            
            
            # Run the State-of-Health metric -----------------------------
            if function_metadata.has_key('stateOfHealth'):
                try:
                    df = irismustangmetrics.apply_simple_metric(r_stream, 'stateOfHealth')
                    # for local miniSEED data, remove invalid state of health metrics
                    if concierge.dataselect_client is None:
                        df = df[~df.metricName.isin(["calibration_signal","clock_locked","event_begin","event_end","event_in_progess","timing_correction","timing_quality"])]
                    dataframes.append(df)
                except Exception as e:
                    logger.warning('"stateOfHealth" metric calculation failed for %s: %s' % (av.snclId, e))
                    
            
            # Run the Basic Stats metric ---------------------------------

            if function_metadata.has_key('basicStats'):
                try:
                    df = irismustangmetrics.apply_simple_metric(r_stream, 'basicStats')
                    dataframes.append(df)
                except Exception as e:
                    logger.warning('"basicStats" metric calculation failed for %s: %s' % (av.snclId, e))
                    

            # Run the STALTA metric --------------------------------------

            # NOTE:  To improve performance, we do not calculate STA/LTA at every single point in 
            # NOTE:  high resolution data.  Instead, we calculate STA/LTA at one point and then skip
            # NOTE:  ahead a few points as determined by the "increment" parameter.
            # NOTE:  An increment that translates to 0.2-0.5 secs seems to be a good compromise
            # NOTE:  between performance and accuracy.

            if function_metadata.has_key('STALTA'):
            
                # Limit this metric to BH. and HH. channels
                if av.channel.startswith('BH') or av.channel.startswith('HH'):
                    try:
                        r_stream_stalta = concierge.get_dataselect(av.network, av.station, av.location, av.channel, starttime, endtime)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.info('No data available for %s' % (av.snclId))
                        elif str(e).lower().find('multiple epochs') :
                            logger.info('Skipping %s because multiple metadata epochs are found' % (av.snclId))
                        else:
                            logger.warning('No data available for %s from %s: %s' % (av.snclId, concierge.dataselect_url, e))
                            continue

                    sampling_rate = utils.get_slot(r_stream_stalta, 'sampling_rate')
                    increment = math.ceil(sampling_rate / 2.0)
                
                    try:
                        df = irismustangmetrics.apply_simple_metric(r_stream_stalta, 'STALTA', staSecs=3, ltaSecs=30, increment=increment, algorithm='classic_LR')
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"STALTA" metric calculation failed for for %s: %s' % (av.snclId, e))
                    
                    
            # Run the Spikes metric --------------------------------------

            # NOTE:  Appropriate values for spikesMetric arguments are determined empirically
                    
            if function_metadata.has_key('spikes'):
               
                # Limit this metric to BH. and HH. channels
                if av.channel.startswith('BH') or av.channel.startswith('HH'):
                    windowSize = 41
                    thresholdMin = 10
                           
                    try:
                        df = irismustangmetrics.apply_simple_metric(r_stream, 'spikes', windowSize, thresholdMin, fixedThreshold=True)
                        dataframes.append(df)
                    except Exception as e:
                        logger.warning('"spikes" metric calculation failed for %s: %s' % (av.snclId, e))            
                        
    # Concatenate and filter dataframes before returning -----------------------
       
    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names
                
    if len(dataframes) == 0:
        logger.warning('"simple" metric calculation generated zero metrics')
        return None
    else:
        result = pd.concat(dataframes, ignore_index=True)    
        mask = result.metricName.apply(valid_metric)
        result = result[(mask)] 
        result.reset_index(drop=True, inplace=True)        
        return(result.drop_duplicates(['snclq']))
        

# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
