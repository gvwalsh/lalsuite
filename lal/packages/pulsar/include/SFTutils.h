/*
 * Copyright (C) 2005 Reinhard Prix
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with with program; see the file COPYING. If not, write to the 
 *  Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, 
 *  MA  02111-1307  USA
 */

/**
 * \author Reinhard Prix, Badri Krishnan
 * \date 2005
 * \file 
 * \ingroup SFTfileIO
 * \brief Utility functions for handling of SFTtype and SFTVectors
 *
 * $Id$
 *
 *  The helper functions LALCreateSFTtype(), LALDestroySFTtype(), LALCreateSFTVector()
 * and LALDestroySFTVector() respectively allocate and free SFT-structs and SFT-vectors. 
 * Similarly, LALCreateTimestampVector() and LALDestroyTimestampVector() allocate and free 
 * a bunch of GPS-timestamps.
 *
 */

#ifndef _SFTUTILS_H  /* Double-include protection. */
#define _SFTUTILS_H

/* C++ protection. */
#ifdef  __cplusplus
extern "C" {
#endif

NRCSID( SFTUTILSH, "$Id$" );
/*---------- INCLUDES ----------*/

#include <lal/LALDatatypes.h>
#include <lal/DetectorSite.h>
#include <lal/Date.h>
#include <lal/SkyCoordinates.h>
#include <lal/RngMedBias.h>
#include <lal/LALRunningMedian.h>




/*---------- DEFINES ----------*/

/*----- Error-codes -----*/

#define SFTUTILS_ENULL 		1
#define SFTUTILS_ENONULL	2
#define SFTUTILS_EMEM		3
#define SFTUTILS_EINPUT		4
#define SFTUTILS_EFUNC		6

#define SFTUTILS_MSGENULL 	"Arguments contained an unexpected null pointer"
#define SFTUTILS_MSGENONULL	"Output pointer is not NULL"
#define SFTUTILS_MSGEMEM	"Out of memory"
#define SFTUTILS_MSGEINPUT	"Invald input parameter"
#define SFTUTILS_MSGEFUNC	"Sub-routine failed"

/*---------- exported types ----------*/

/** A vector of COMPLEX8FrequencySeries */
typedef struct {
  UINT4 			length;		/**< number of SFTs */
  COMPLEX8FrequencySeries 	*data;		/**< array of SFTs */
} COMPLEX8FrequencySeriesVector;

/** A vector of REAL8FrequencySeries */
typedef struct {
  UINT4                  length;
  REAL8FrequencySeries   *data;
} REAL8FrequencySeriesVector;


/** A so-called 'SFT' (short-Fourier-transform) will be stored in a COMPLEX8FrequencySeries */
typedef COMPLEX8FrequencySeries 	SFTtype;	


/** The corresponding vector-type to hold a vector of 'SFTs' */
typedef COMPLEX8FrequencySeriesVector 	SFTVector;

/** Special type for holding a PSD vector (over several SFTs) */
typedef REAL8FrequencySeriesVector PSDVector;

/** A collection of SFT vectors -- one for each IFO in a multi-IFO search */
typedef struct tagMultiSFTVector {
  UINT4      length;  	/**< number of ifos */
  SFTVector  **data; 	/**< sftvector for each ifo */
} MultiSFTVector;


/** A collection of PSD vectors -- one for each IFO in a multi-IFO search */
typedef struct {
  UINT4      length;  	/**< number of ifos */
  PSDVector  **data; 	/**< sftvector for each ifo */
} MultiPSDVector;

/** One noise-weight (number) per SFT (therefore indexed over IFOs and SFTs */
typedef struct {
  UINT4 length;		/**< number of ifos */
  REAL8Vector **data;	/**< weights-vector for each SFTs */
  REAL8 Sinv_Tsft;	/**< normalization factor used: \f$\mathcal{S}^{-1}\,T_\mathrm{SFT}\f$ */
} MultiNoiseWeights;

/** A collection of (multi-IFO) time-series */
typedef struct {
  UINT4 length;			/**< number of ifos */
  REAL4TimeSeries **data;	/**< vector of REAL4 timeseries */
} MultiREAL4TimeSeries;

/** A vector of 'timestamps' of type LIGOTimeGPS */
typedef struct {
  UINT4 	length;		/**< number of timestamps */
  LIGOTimeGPS 	*data;		/**< array of timestamps */
  REAL8		deltaT;		/**< 'length' of each timestamp (e.g. typically Tsft) */
} LIGOTimeGPSVector;

/** A vector of 'timestamps' of type LIGOTimeGPS */
typedef struct {
  UINT4 	        length;	   /**< number of timestamps vectors or ifos */
  LIGOTimeGPSVector 	**data;    /**< timestamps vector for each ifo */
} MultiLIGOTimeGPSVector;

/* A vector of strings */
typedef struct {
  UINT4 length;
  CHAR **data;
} LALStringVector;

/*---------- Global variables ----------*/
/* empty init-structs for the types defined in here */
extern const SFTtype empty_SFTtype;
extern const SFTVector empty_SFTVector;
extern const PSDVector empty_PSDVector;
extern const MultiSFTVector empty_MultiSFTVector;
extern const MultiPSDVector empty_MultiPSDVector;
extern const MultiNoiseWeights empty_MultiNoiseWeights;
extern const MultiREAL4TimeSeries empty_MultiREAL4TimeSeries;
extern const LIGOTimeGPSVector empty_LIGOTimeGPSVector;
extern const MultiLIGOTimeGPSVector empty_MultiLIGOTimeGPSVector;
extern const LALStringVector empty_LALStringVector;


/*---------- exported prototypes [API] ----------*/
/* ----------------------------------------------------------------------
 *  some prototypes for general functions handling these data-types 
 *----------------------------------------------------------------------*/
void LALCreateSFTtype (LALStatus *status, SFTtype **sft, UINT4 SFTlen);	
void LALCreateSFTVector (LALStatus *status, SFTVector **sftvect, UINT4 numSFTs, UINT4 SFTlen);
void LALCreateMultiSFTVector ( LALStatus *status, MultiSFTVector **out, UINT4 length, UINT4Vector *numsft );

COMPLEX8Vector *XLALrefineCOMPLEX8Vector (const COMPLEX8Vector *in, UINT4 refineby, UINT4 Dterms);
void upsampleMultiSFTVector (LALStatus *, MultiSFTVector *inout, UINT4 upsample, UINT4 Dterms);
void upsampleSFTVector (LALStatus *, SFTVector *inout, UINT4 upsample, UINT4 Dterms);

void LALDestroySFTtype (LALStatus *status, SFTtype **sft);
void LALDestroySFTVector (LALStatus *status, SFTVector **sftvect);
void LALDestroyPSDVector (LALStatus *status, PSDVector **vect);

void LALDestroyMultiSFTVector (LALStatus *status, MultiSFTVector **multvect);
void LALDestroyMultiPSDVector (LALStatus *status, MultiPSDVector **multvect);

void LALCopySFT (LALStatus *status, SFTtype *dest, const SFTtype *src);

void LALConcatSFTVectors (LALStatus *, SFTVector **outVect, const SFTVector *inVect1, const SFTVector *inVect2 );
void LALAppendSFT2Vector (LALStatus *, SFTVector *vect, const SFTtype *sft );

LIGOTimeGPSVector *XLALCreateTimestampVector (UINT4 len);
void XLALDestroyTimestampVector (LIGOTimeGPSVector *vect);

void LALCreateTimestampVector (LALStatus *status, LIGOTimeGPSVector **vect, UINT4 len);
void LALDestroyTimestampVector (LALStatus *status, LIGOTimeGPSVector **vect);

void LALMakeTimestamps (LALStatus *, LIGOTimeGPSVector **timestamps, const LIGOTimeGPS tStart, REAL8 duration, REAL8 Tsft);
void LALGetSFTtimestamps (LALStatus *, LIGOTimeGPSVector **timestamps, const SFTVector *sfts );

void XLALDestroyStringVector ( LALStringVector *vect );
void LALDestroyStringVector ( LALStatus *, LALStringVector **vect );
void LALAppendString2Vector (LALStatus *, LALStringVector *vect, const CHAR *string );

CHAR *XLALGetChannelPrefix ( const CHAR *name );
LALDetector *XLALGetSiteInfo ( const CHAR *name );

void LALComputeNoiseWeights  (LALStatus *status, REAL8Vector *weightV, const SFTVector *sftVect, 
			      INT4 blkSize, UINT4 excludePercentile);
void LALComputeMultiNoiseWeights  (LALStatus *status, MultiNoiseWeights **weightsV, const MultiPSDVector *multipsd, 
				   UINT4 blocksRngMed, UINT4 excludePercentile);
void LALDestroyMultiNoiseWeights  (LALStatus *status, MultiNoiseWeights **weights);

#ifdef  __cplusplus
}
#endif  
/* C++ protection. */

#endif  /* Double-include protection. */
