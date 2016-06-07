"""
ISPAQ Business Logic for transfer Metrics.

:copyright:
    Mazama Science
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

import math
import numpy as np
import pandas as pd

import utils
import irisseismic
import irismustangmetrics

import itertools # for combintations


def transferFunction_metrics(concierge):
    """
    Generate *transfer* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.

    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger

    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['transferFunction']

    # Get unique network-station pairs
    networkStationPairs = availability.network + '.' + availability.station
    networkStationPairs = networkStationPairs.drop_duplicates().sort_values().reset_index(drop=True)
    #networkStationPairs <- sort(unique(stringr::str_extract(availability$snclId,"[A-Z0-9]+\\.[A-Z0-9_]+")))
    
    for networkStation in networkStationPairs:
  
        # Subset the availability dataframe to contain only results for this networkStation
        (network,station) = networkStation.split('.')
        stationAvailability = availability[(availability.network == network) & (availability.station == station)].reset_index(drop=True)
        
        # Remove LOG and ACE text channels
        stationAvailability = stationAvailability[(stationAvailability.channel != 'LOG') & (stationAvailability.channel != 'ACE')].reset_index(drop=True)
        
        ##################################################################
        # Loop through all channels by dip looking for multiple locations.
        ##################################################################
    
        # Vertical and Horizontal channels will be handled differently
        dips = stationAvailability.dip.abs().drop_duplicates().sort_values().reset_index(drop=True)
    
        for dip in dips:
    
            # Find channels with the current dip
            channelAvailability = stationAvailability[abs(stationAvailability.dip) == dip].reset_index(drop=True)
    
            # Treat vertical channels as we've always done
            if dip == 90:
    
                # Bail if there is only one Z channel
                if channelAvailability.shape[0] <= 1:
                    logger.debug('skipping %s because there are no other channels for comparison' % (channelAvailability.snclId[0]))
                    continue
    
                # NOTE:  channelAvailability is a dataframe with one row per location for the current SN.L
                # NOTE:  Now we use itertools.combinations to generate all combinations of locations of rows.
                
                rowMatrix = []
                for combo in itertools.combinations(range(channelAvailability.shape[0]), 2):
                    rowMatrix.append(combo)
                
                # Convert to a numpy matrix for total agreement with original R code
                rowMatrix = np.matrix(rowMatrix)
                      
                ############################################################
                # Loop through all location pairs for this channel
                ############################################################
        
                for i in range(rowMatrix.shape[0]):
                    
                    Zav1 = channelAvailability.iloc[rowMatrix[i,0],]
                    Zav2 = channelAvailability.iloc[rowMatrix[i,1],]

                    # We don't want to compare 2 sample rates from the same instrument.
                    # We'll define the same instrument as one where the location code 
                    # and last 2 characters of the channel code match.
                    if ( (Zav1.location == Zav2.location) and (Zav1.channel[1:] == Zav2.channel[1:]) ):
                        continue
                
                
                    # Get primary (1) and secondary (2) traces
                    try:
                        Zst1 = concierge.get_dataselect(Zav1.network, Zav1.station, Zav1.location, Zav1.channel, inclusiveEnd=False)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.debug('No data for %s' % (Zav1.snclId))
                        else:
                            logger.debug('No data for %s from %s: %s' % (Zav1.snclId, concierge.dataselect_url, e))
                        continue
                    
                    try:
                        Zst2 = concierge.get_dataselect(Zav2.network, Zav2.station, Zav2.location, Zav2.channel, inclusiveEnd=False)
                    except Exception as e:
                        if str(e).lower().find('no data') > -1:
                            logger.debug('No data for %s' % (Zav2.snclId))
                        else:
                            logger.debug('No data for %s from %s: %s' % (Zav2.snclId, concierge.dataselect_url, e))
                        continue
                    
                    sampling_rate = min(utils.get_slot(Zst1,'sampling_rate'), utils.get_slot(Zst2,'sampling_rate'))
                
                    # Get primary (1), secondary (2) and orthogonal secondary spectra     
                    Zevalresp1 = irisseismic.getTransferFunctionSpectra(Zst1,sampling_rate)
                    Zevalresp2 = irisseismic.getTransferFunctionSpectra(Zst2,sampling_rate)          
                
                    # Run the transferFunction metric ----------------------------------------
            
                    logger.info('Calculating transferFunction metrics for %s:%s' % (Zav1.snclId, Zav2.snclId))
                    try:
                        df = irismustangmetrics.apply_correlation_metric(r_stream1, r_stream2, 'transferFunction', Zevalresp1, Zevalresp2)
                        # By default, this metrics returns value="N". Convert this to NaN
                        df.value = np.NaN
                        dataframes.append(df)
                    except Exception as e:
                        logger.error('"transfer_function" metric calculation failed for %s:%s: %s' % (Zav1.snclId, Zav2.snclId, e))
                    
                # END of for i (pairs) in rowMatrix

            elif dip == 0:
                
                # If azimuths don't agree for primary and secondary horizontal channels, 
                # we will first rotate secondary channels to match primary channels.
        
                # Bail if there are only two horizontal channels
                # TODO:  uncomment this sanity check
                #if channelAvailability.shape[0] <= 2:
                    #logger.debug('skipping %s because there are no other channels for comparison' % (channelAvailability.snclId[0]))
                    #continue
                 
                # Convert snclId into a snclPrefix that excludes the last character
                # Matching scnlPrefixes should be orthogonal Y and X channel pairs
                channelAvailability['snclPrefix'] = channelAvailability.snclId.str[:-1]
                snclPrefixes = channelAvailability.snclPrefix.drop_duplicates().sort_values().reset_index(drop=True)
        
                # Make sure we've sorted by snclPrefix before we loop through and assign X or Y to each entry
                channelAvailability = channelAvailability.sort_values(by='snclPrefix')

                # We're labeling orthogonal horizontal channels "Y" and "X" based on the Cartesian coordinate system
                # If we need to rotate the secondary channels, we'll need this information
                axisList = []
                for snclPrefix in snclPrefixes:
                    xyAvailability = channelAvailability[channelAvailability.snclId.str.contains(snclPrefix)]
        
                    # This should never happen, but just in case...
                    if xyAvailability.shape[0] <= 0:
                        continue
                    
                    # Channel with no orthogonal mate - we can use it straight, but we can't rotate it
                    # We'll mark the axis "U" for unknown
                    if xyAvailability.shape[0] == 1:
                        axisList.append('U')
                    
                    # END if 1 row
        
                    # Found an orthogonal channel pair - label X and Y channels
                    if xyAvailability.shape[0] == 2:
                        azim1 = xyAvailability.azimuth.iloc[0]
                        azim2 = xyAvailability.azimuth.iloc[1]
                        diffAzim = azim1 - azim2
        
                        if ( (diffAzim >= -93 and diffAzim <= -87) or (diffAzim >= 267 and diffAzim <= 273) ):
                            axisList.append("Y")
                            axisList.append("X")
                        elif ( (diffAzim >= -273 and diffAzim <= -267) or (diffAzim >= 87 and diffAzim <= 93) ):
                            axisList.append("X")
                            axisList.append("Y")      
                        else:
                            # These channels are mates, but they're not orthogonal enough 
                            # Use them individually if possible, but don't attempt to rotate them 
                            # Since they're not technically X and Y we'll mark both "U" (unknown) as well
                            axisList.append("U")
                            axisList.append("U")

                    # END if 2 rows     
        
                    # Hard telling why there are so many channels, so mark them "D" for drop
                    # Metadata errors can cause cases like this
                    if xyAvailability.shape[0] >= 3:
                        for i in range(xyAvailability.shape[0]):
                            axList.append("D")

                    # END if 3 or more rows
        
                # END for snclPrefixes
        
                # Add a "cartAxis" column to the horizontal channel availability data frame
                channelAvailability["cartAxis"] = axisList
        
                # Drop entries marked "D"
                channelAvailability = channelAvailability[channelAvailability.cartAxis != "D"].reset_index(drop=True)
        
                # Separate channel availability data frame into X and Y data frames 
                # Pair them across location codes
                XchannelAvailability = channelAvailability[channelAvailability.cartAxis != "Y"].reset_index(drop=True)
                YchannelAvailability = channelAvailability[channelAvailability.cartAxis != "X"].reset_index(drop=True)
        
                XrowMatrix = []
                for combo in itertools.combinations(range(XchannelAvailability.shape[0]), 2):
                    XrowMatrix.append(combo)
                
                # Convert to a pandas dataframe
                XrowMatrix = pd.DataFrame(XrowMatrix,columns=['Primary','Secondary'])
        
                YrowMatrix = []
                for combo in itertools.combinations(range(YchannelAvailability.shape[0]), 2):
                    YrowMatrix.append(combo)
                
                # Convert to a numpy matrix for total agreement with original R code
                YrowMatrix = pd.DataFrame(YrowMatrix,columns=['Primary','Secondary'])
                
                # Determine the difference in azimuth between primary and secondary channels for X and Y
                # Create a column called "azDiff" to store this difference
                azDiffList = []
                for i in range(XrowMatrix.shape[0]):
                    azDiff = XchannelAvailability.azimuth[XrowMatrix.iloc[i,0]] - XchannelAvailability.azimuth[XrowMatrix.iloc[i,1]]
                    if (azDiff < 0):
                        azDiff <- azDiff + 360
                    azDiffList.append(azDiff)
                    
                XrowMatrix['azDiff'] = azDiffList                   
                    
                azDiffList = []
                for i in range(YrowMatrix.shape[0]):
                    azDiff = YchannelAvailability.azimuth[YrowMatrix.iloc[i,0]] - YchannelAvailability.azimuth[YrowMatrix.iloc[i,1]]
                    if (azDiff < 0):
                        azDiff <- azDiff + 360
                    azDiffList.append(azDiff)
                    
                YrowMatrix['azDiff'] = azDiffList   
        
                # Separate pairs into those that need rotating and those that don't
                YrowMatrixRot = YrowMatrix[YrowMatrix.azDiff != 0].reset_index(drop=True)
                YrowMatrixNoRot = YrowMatrix[YrowMatrix.azDiff == 0].reset_index(drop=True)
                XrowMatrixRot = XrowMatrix[XrowMatrix.azDiff != 0].reset_index(drop=True)
                XrowMatrixNoRot = XrowMatrix[XrowMatrix.azDiff == 0].reset_index(drop=True)

                matrixListToRotate = (YrowMatrixRot, XrowMatrixRot)
                matrixListNotToRotate = (YrowMatrixNoRot, XrowMatrixNoRot)
                availabilityList = (YchannelAvailability, XchannelAvailability)
        
                # Get traces, spectra and transfer functions for horizontal channels that don't need rotating
                # First Y channels, then X
                for i in range(2):
        
                    debug_point = 1
                    
                    if matrixListNotToRotate[i].shape[0] != 0:
                    #if ( nrow(matrixListNotToRotate[[i]]) != 0 ) {
        
                        for j in range(matrixListNotToRotate[i].shape[0]):
                        #for ( j in seq(nrow(matrixListNotToRotate[[i]])) ) {
        
                            av1 = availabilityList[i].iloc[int(matrixListNotToRotate[i].iloc[j,0]),]
                            av2 = availabilityList[i].iloc[int(matrixListNotToRotate[i].iloc[j,1]),]
        
                            # We don't want to compare 2 sample rates from the same instrument.
                            # We'll define the same instrument as one where the location code 
                            # and last 2 characters of the channel code match.
                            if ( (av1.location == av2.location) and (av1.channel[:-1] == av2.channel[:-1]) ):
                                continue
        
                            ## Get primary (1) and secondary (2) traces
                            try:
                                st1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.debug('No data for %s' % (av1.snclId))
                                else:
                                    logger.debug('No data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                                continue
        
                            try:
                                st2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel, inclusiveEnd=False)
                            except Exception as e:
                                if str(e).lower().find('no data') > -1:
                                    logger.debug('No data for %s' % (av2.snclId))
                                else:
                                    logger.debug('No data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                                continue
        
                            sampling_rate = min( utils.get_slot(st1, 'sampling_rate'), utils.get_slot(st2, 'sampling_rate') )
        
                            # Get primary (1), secondary (2) and orthogonal secondary spectra     
                            evalresp1 = getTransferFunctionSpectra(st1, sampling_rate)
                            evalresp2 = getTransferFunctionSpectra(st2, sampling_rate)          
        
                            # Calculate the metrics and append them to the current list
                            logger.info('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
                            try:
                                df = irismustangmetrics.apply_transferFunction_metric(st1, st2, evalresp1, evalresp2)
                                # By default, this metrics returns value="N". Convert this to NaN
                                df.value = np.NaN
                                dataframes.append(df)
                            except Exception as e:
                                logger.error('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                            
        
                        # END for rows (pairs) in matrix
        
                    # END if matrix has rows
        
                # END for lists of pairs we don't need to rotate
        
        
        
                ## Get traces, spectra and transfer functions for horizontal channels that DO need rotating
                #for (i in 1:length(matrixListToRotate)) {
        
                    #if ( nrow(matrixListToRotate[[i]]) != 0 ) {
        
                        #for ( j in seq(nrow(matrixListToRotate[[i]])) ) {
        
                            #av1 <- availabilityList[[i]][matrixListToRotate[[i]][j,1],]   # Primary trace for Y (i=1) or X (i=2)
                            #av2 <- availabilityList[[i]][matrixListToRotate[[i]][j,2],]   # Secondary trace for Y (i=1) or X (i=2)
        
                            ## We don't want to compare 2 sample rates from the same instrument.
                            ## We'll define the same instrument as one where the location code 
                            ## and last 2 characters of the channel code match.
                            #if ( (av1$location == av2$location) && (substring(av1$channel,2) == substring(av2$channel,2) ) ) { next }
        
                            ## Orthogonal mate of av2 - we assume they will have matching snclPrefixes
                            #if (i == 1) {
                                #av3 = subset(availabilityList[[i+1]], grepl(av2$snclPrefix,snclPrefix))
                                #} else {
                                    #av3 = subset(availabilityList[[i-1]], grepl(av2$snclPrefix,snclPrefix))
                                #}  
        
                            ## We need to have exactly 1 orthogonal trace for rotation
                            #if (nrow(av3) != 1) {
                                #next
                            #}
        
                            #rotAngle <- matrixListToRotate[[i]][j,3]
        
                            ## Get primary (1), secondary (2), and secondary orthogonal traces
                            #result <- try( st1 <- IRISSeismic::getDataselect(iris, av1$network, av1$station, av1$location, av1$channel, starttime, endtime, inclusiveEnd=FALSE),
                                           #silent=TRUE )
        
                            #if (class(result)[1] == "try-error" ) {      
                                #setProcessExitCode( MCRErrorMessage(geterrmessage(),"DATASELECT",id=av1$snclId) )
                                #next
                            #}
        
                            #result <- try( st2 <- IRISSeismic::getDataselect(iris, av2$network, av2$station, av2$location, av2$channel, starttime, endtime, inclusiveEnd=FALSE),
                                           #silent=TRUE )
        
                            #if (class(result)[1] == "try-error" ) {      
                                #setProcessExitCode( MCRErrorMessage(geterrmessage(),"DATASELECT",id=av2$snclId) )
                                #next
                            #}
        
                            #result <- try( st3 <- IRISSeismic::getDataselect(iris, av3$network, av3$station, av3$location, av3$channel, starttime, endtime, inclusiveEnd=FALSE),
                                           #silent=TRUE )
        
                            #if (class(result)[1] == "try-error" ) {      
                                #setProcessExitCode( MCRErrorMessage(geterrmessage(),"DATASELECT",id=av3$snclId) )
                                #next
                            #}
        
                            #sampling_rate <- min(st1@traces[[1]]@stats@sampling_rate, st2@traces[[1]]@stats@sampling_rate)
        
                            ## Get primary (1), secondary (2) and orthogonal secondary spectra     
                            #evalresp1 <- getTransferFunctionSpectra(st1,sampling_rate)
                            #evalresp2 <- getTransferFunctionSpectra(st2,sampling_rate)          
                            #evalresp3 <- getTransferFunctionSpectra(st3,sampling_rate)
        
                            ## Determine which secondary trace is Y vs. X
                            #if (av2$cartAxis == "Y") {
                                #Yst2 <- st2
                                #Xst2 <- st3
                                #Yevalresp2 <- evalresp2
                                #Xevalresp2 <- evalresp3
                                #} else if (av2$cartAxis == "X") {
                                    #Yst2 <- st3
                                    #Xst2 <- st2
                                    #Yevalresp2 <- evalresp3
                                    #Xevalresp2 <- evalresp2
                                    #} else {
                                        #next
                                    #}
        
                            ## Rotate the secondary traces
                            #traceRotList <- list()          
                            #result <- try(traceRotList <- IRISSeismic::rotate2D(Yst2,Xst2,rotAngle), silent=TRUE)
        
                            #if (class(result)[1] == "try-error" ) {
                                #setProcessExitCode( MCRWarning(paste("transfer_function rotate2D", stringr::str_trim(geterrmessage()), ": start=",starttime, "end=", endtime)) )
                                #next
                            #}
        
                            #RYst2 <- traceRotList[[1]]
                            #RXst2 <- traceRotList[[2]]
        
                            ## Rotate the secondary spectra
                            #radians <- rotAngle * pi/180
        
                            #RYevalresp2 <- Yevalresp2
                            #RXevalresp2 <- Xevalresp2
        
                            ## sin**2(rotAngle) + cos**2(rotAngle) = 1
                            #RYevalresp2$amp <-  (cos(radians))^2 * Yevalresp2$amp + (sin(radians))^2 * Xevalresp2$amp
                            #RXevalresp2$amp <- (-sin(radians))^2 * Yevalresp2$amp + (cos(radians))^2 * Xevalresp2$amp
        
                            ## Determine whether primary trace was X or Y
                            ## Calculate the metric and append it to the current list
                            #if (av1$cartAxis == "Y") {
                                #result <- try( tempList <- transferFunctionMetric(st1,RYst2,evalresp1,RYevalresp2),
                                               #silent=TRUE )
                                #} else if (av1$cartAxis == "X") {
                                    #result <- try( tempList <- transferFunctionMetric(st1,RXst2,evalresp1,RXevalresp2),
                                                   #silent=TRUE )
                                    #} else {
                                        #setProcessExitCode( MCRWarning(paste("transfer_function Skipping ",av1$snclPrefix,"- axis",channelAvailability[i,]$cartAxis,"indicates that it cannot be rotated", ": start=",starttime, " end=",endtime)) )
                                        #next
                                    #}
        
                            #if (class(result)[1] == "try-error" ) {
                                #setProcessExitCode( MCRWarning(geterrmessage()) )
                                #next
                                #} else {
                                    #result <- try( metricList <- appendTFMetric(tempList, metricList),
                                                   #silent=TRUE )
        
                                    #if (class(result)[1] == "try-error" ) {
                                        #setProcessExitCode( MCRWarning(geterrmessage()) )
                                        #next
                                    #} 
                                #}
        
                            #} # END of for location pairs in matrix
        
                        #} # END if matrix has rows
        
                    #} # END for lists of pairs we DO rotate
        
            #} else {
        
                ## Write warning if dip are neither vertical nor horizontal.
                ## They would require 3D rotation that isn't available here.
                #for (i in seq(nrow(channelAvailability))) {
                    #setProcessExitCode( MCRWarning(paste("transfer function skipping",channelAvailability[i,]$snclId, "- dip",channelAvailability[i,]$dip,"requires 3D rotation", ": start=",starttime, " end=",endtime)) )
                #}
        
            #} # END of if dip = ...


# ------------------------------------------------------------------------------
#      Utility Functions
# ------------------------------------------------------------------------------


# getTransferFunctionSpectra is needed in transferFunction_metrics.py
def getTransferFunctionSpectra(st, sampling_rate):
    # This function returns an evalresp fap response for trace st using sampling_rate 
    # to determine frequency limits

    # Min and Max frequencies for evalresp will be those used for the cross spectral binning
    alignFreq = 0.1

    if (sampling_rate <= 1):
        loFreq = 0.001
    elif (sampling_rate > 1 and sampling_rate < 10):
        loFreq = 0.0025
    else:
        loFreq = 0.005

    # No need to exceed the Nyquist frequency after decimation
    hiFreq = 0.5 * sampling_rate

    log2_alignFreq = math.log(alignFreq,2)
    log2_loFreq = math.log(loFreq,2)
    log2_hiFreq = math.log(hiFreq,2)
    
    if alignFreq >= hiFreq:
        octaves = []
        octave = log2_alignFreq
        while octave >= log2_loFreq:
            if octave <= log2_hiFreq:
                octaves.append(octave)
            octave -= 0.125
            octaves = pd.Series(octaves).sort_values().reset_index(drop=True)
            
    else:
        octaves = []
        octave = log2_alignFreq
        loOctaves = []
        while octave >= log2_loFreq:
            loOctaves.append(octave)
            octave -= 0.125
        loOctaves = pd.Series(loOctaves)
            
            
        octave = log2_alignFreq
        hiOctaves = []
        while octave <= log2_hiFreq:
            hiOctaves.append(octave)
            octave += 0.125
        hiOctaves = pd.Series(hiOctaves)
            
        octaves = loOctaves.append(hiOctaves).drop_duplicates().sort_values().reset_index(drop=True)
        
    binFreq = pow(2,octaves)

    # Argurments for evalresp
    minfreq = min(binFreq)
    maxfreq = max(binFreq)
    nfreq = len(binFreq)
    units = 'def'
    output = 'fap'

    network = utils.get_slot(st,'network')
    station = utils.get_slot(st,'station')
    location = utils.get_slot(st,'location')
    channel = utils.get_slot(st,'channel')
    starttime = utils.get_slot(st,'starttime')
    
    evalResp = irisseismic.getEvalresp(network, station, location, channel, starttime,
                                       minfreq, maxfreq, nfreq, units, output)

    return(evalResp)




# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def OLD_transferFunction_metrics(concierge):
    """
    Generate *transfer* metrics.

    :type concierge: :class:`~ispaq.concierge.Concierge`
    :param concierge: Data access expiditer.

    :rtype: pandas dataframe
    :return: Dataframe of simple metrics.

    .. rubric:: Example

    TODO:  doctest examples
    """
    # Get the logger from the concierge
    logger = concierge.logger

    # Container for all of the metrics dataframes generated
    dataframes = []

    # ----- All available SNCLs -------------------------------------------------
    
    availability = concierge.get_availability()

    # function metadata dictionary
    function_metadata = concierge.function_by_logic['transferFunction']

    # Find the locations associated with seismic channels
    channels = sorted(set(availability.channel))
    
    ############################################################
    # Loop through all channels looking for multiple locations.
    ############################################################

    for channel in channels:
        
        channelAvailability = availability[availability.channel == channel]
        
        # Bail if there is only one location
        if channelAvailability.shape[0] == 1:
            continue
        
        # NOTE:  channelAvailability is a dataframe with one row per location for the current SN.L
        # NOTE:  Now we use itertools.combinations to generate all combinations of locations of rows.
        
        rowMatrix = []
        for combo in itertools.combinations(range(channelAvailability.shape[0]), 2):
            rowMatrix.append(combo)
        
        # Convert to a numpy matrix for total agreement with original R code
        rowMatrix = np.matrix(rowMatrix)
              
        ############################################################
        # Loop through all location pairs for this channel
        ############################################################

        for i in range(rowMatrix.shape[0]):
            
            av1 = channelAvailability.iloc[rowMatrix[i,0],]
            av2 = channelAvailability.iloc[rowMatrix[i,1],]
        
            # Only continue if azimuths are within 5 degrees of eachother
            azimuthAngle = abs(av1.azimuth - av2.azimuth) * math.pi/180.0
            maxAzimuthAngle = 5.0 * math.pi/180.0
            if (math.cos(azimuthAngle) < math.cos(maxAzimuthAngle)):
                logger.debug('\tskipping %s:%s because azimuths differ by more than 5 degrees' % (av1.snclId, av2.snclId))
                continue
        
            # Only continue if dips are within 5 degrees of eachother
            dipAngle = abs(av1.dip - av2.dip) * math.pi/180.0
            maxDipAngle = 5.0 * math.pi/180.0
            if (math.cos(dipAngle) < math.cos(maxDipAngle)):
                logger.debug('\tskipping %s:%s because dips differ by more than 5 degrees' % (av1.snclId, av2.snclId))
                continue
        
            # Channels OK so proceed
        
            try:
                r_stream1 = concierge.get_dataselect(av1.network, av1.station, av1.location, av1.channel)
            except Exception as e:
                logger.warning('\tunable to obtain data for %s from %s: %s' % (av1.snclId, concierge.dataselect_url, e))
                continue
            
            try:
                r_stream2 = concierge.get_dataselect(av2.network, av2.station, av2.location, av2.channel)
            except Exception as e:
                logger.warning('\tunable to obtain data for %s from %s: %s' % (av2.snclId, concierge.dataselect_url, e))
                continue
            
            
            # Run the transferFunction metric ----------------------------------------
    
            logger.info('Calculating transferFunction metrics for %s:%s' % (av1.snclId, av2.snclId))
            try:
                df = irismustangmetrics.apply_correlation_metric(r_stream1, r_stream2, 'transferFunction')
                # By default, this metrics returns value="N". Convert this to NaN
                df.value = np.NaN
                dataframes.append(df)
            except Exception as e:
                logger.error('"transfer_function" metric calculation failed for %s:%s: %s' % (av1.snclId, av2.snclId, e))
                
        
        # END of location-pairs loop
        
        
    # END of channel loop
            

    # Create a boolean mask for filtering the dataframe
    def valid_metric(x):
        return x in concierge.metric_names

    result = pd.concat(dataframes, ignore_index=True)
    mask = result.metricName.apply(valid_metric)
    result = result[(mask)]
    result.reset_index(drop=True, inplace=True)

    return(result)


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import doctest
    doctest.testmod(exclude_empty=True)
