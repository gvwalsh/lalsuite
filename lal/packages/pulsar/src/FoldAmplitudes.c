/************************************ <lalVerbatim file="FoldAmplitudesCV">
Author: Mendell, Greg A.
$Id$  
************************************* </lalVerbatim> */

/********************************************************** <lalLaTeX>
\subsection{Module \texttt{FoldAmplitudes.c}}

\subsubsection*{Prototypes}
\input{FoldAmplitudesCP}
\index{\texttt{LALFoldAmplitudes()}}

\subsubsection*{Description}

\begin{verbatim}
Contains source for function LALFoldAmplitudes:

inputs: a vector of amplitudes and a vector of phases.

params: number of phase bins, the minimum phase to bin, and the maximum phase to bin.

action: for each phase, the phase is first reduced by modulo arithmetic to a value
        between binMin and binMax.  The corresponding amplitudes is then added to
        the corresponding phase bins.  The width of each bin is (binMax - binMin)/numBins.

output: a vector of folded amplitude; component i is the folded amplitude for phase bin i.
\end{verbatim}

\subsubsection*{Algorithm}

%[A description of the method used to perform the calculation.]

\begin{verbatim}

  Algorithm for folding amplitudes into phase bins:

  1) Reduce the phase to a value between binMax and binMin. Note that binMax -binMin = binRange.
  2) Find the bin index corresponding to this phase.
  3) Add the amplitude from the input data vector to this phase bin.

  Notes:
  	(i) The function is more efficient if binRange == 1.
  	(ii) The results are stored in the REAL4Vector output structure data vector.
  	(iii) Only binMin = 0.0 is currently supported.

  Code:
  	
  if (binRange == 1.0) {
  	for ( i = 0 ; i < amplitudeVec->length ; ++i )
  	{
  		phase = phaseVec->data[i] - floor( phaseVec->data[i] );
  		binIndex = (INT4) floor( phase/binSize );
  		output->data[binIndex] += amplitudeVec->data[i];
  	}
  } else {
  	for ( i = 0 ; i < amplitudeVec->length ; ++i )
  	{
  		phase = phaseVec->data[i] - floor( phaseVec->data[i]/binRange ) * binRange;
  		binIndex = (INT4) floor( phase/binSize );
  		output->data[binIndex] += amplitudeVec->data[i];
  	}
  }

\end{verbatim}


\subsubsection*{Uses}

% List any external functions called by this function.

For use in known pulsar search.

\begin{verbatim}
\end{verbatim}

\subsubsection*{Notes}

%[Any relevant notes]

\vfill{\footnotesize\input{FoldAmplitudesCV}}

******************************************************* </lalLaTeX> */ 

/******* INCLUDE STANDARD LIBRARY HEADERS; ************/
/* note LALStdLib.h already includes stdio.h and stdarg.h */
#include <math.h>

/******* INCLUDE ANY LDAS LIBRARY HEADERS ************/

/******* INCLUDE ANY LAL HEADERS ************/
#include <lal/LALStdlib.h>
#include <lal/FoldAmplitudes.h>

/******* DEFINE RCS ID STRING ************/
NRCSID( FOLDAMPLITUDESC, "$Id$" );

/******* DEFINE LOCAL CONSTANTS AND MACROS ************/

/******* DECLARE LOCAL (static) FUNCTIONS ************/
/* (definitions can go here or at the end of the file) */

/******* DEFINE GLOBAL FUNCTIONS ************/

/* <lalVerbatim file="FoldAmplitudesCP"> */
void
LALFoldAmplitudes( LALStatus                      *status,
		     REAL4Vector         	  *output,
		     const FoldAmplitudesInput    *input,
		     const FoldAmplitudesParams   *params )
		
/* </lalVerbatim> */
{
  /******* DECLARE VARIABLES ************/

  	const REAL4Vector 	*amplitudeVec;   /* pointer to input vector of amplitudes */
   	const REAL4Vector  	*phaseVec;       /* pointer to input vector of phases */
   	REAL4			phase;           /* individual reduced phase  */
   	REAL4			binRange;        /* the range of phase bins, e.g., [0,2*pi]  */
   	REAL4			binSize;   	 /* the size of each bin */
   	INT4			binIndex;   	 /* individual bin index an amplitude belongs to */
   	INT4			i;               /* generic integer index */
/*   	INT4			n;     */          /* generic integer */

  INITSTATUS( status, "LALFoldAmplitudes", FOLDAMPLITUDESC );
  ATTATCHSTATUSPTR (status);

  /******* CHECK VALIDITY OF ARGUMENTS; for example ************/

  if ( output == NULL ) {
    ABORT( status, FOLDAMPLITUDESH_ENULLP, FOLDAMPLITUDESH_MSGENULLP );
  }

  if ( input->amplitudeVec->length != input->phaseVec->length) {
    ABORT( status, FOLDAMPLITUDESH_EVECSIZE , FOLDAMPLITUDESH_MSGEVECSIZE );
  }

  if ( params->numBins < 1) {
    ABORT( status, FOLDAMPLITUDESH_ENUMBINS, FOLDAMPLITUDESH_MSGENUMBINS );
  }

  if ( params->binMax <=  params->binMin) {
    ABORT( status, FOLDAMPLITUDESH_EBINSIZE, FOLDAMPLITUDESH_MSGEBINSIZE );
  }

  if ( params->binMin != 0.0 ) {
    ABORT( status, FOLDAMPLITUDESH_EBINMIN, FOLDAMPLITUDESH_MSGEBINMIN  );
  }

  /******* EXTRACT INPUTS AND PARAMETERS ************/

  phaseVec = input->phaseVec;
  amplitudeVec = input->amplitudeVec;

  binRange = params->binMax - params->binMin;
  binSize =  binRange/params->numBins;

  /******* DO ANALYSIS ************/

  /* Fold amplitudes into phase bins; store results in output  */
  /* Function is more efficient if binRange == 1 */
  if (binRange == 1.0) {
  	for ( i = 0 ; i < (INT4)amplitudeVec->length ; ++i )
  	{
  		phase = phaseVec->data[i] - floor( phaseVec->data[i] );
  		binIndex = (INT4) floor( phase/binSize );
  		output->data[binIndex] += amplitudeVec->data[i];
  	}
  } else {
  	for ( i = 0 ; i < (INT4)amplitudeVec->length ; ++i )
  	{
  		phase = phaseVec->data[i] - floor( phaseVec->data[i]/binRange ) * binRange;
  		binIndex = (INT4) floor( phase/binSize );
  		output->data[binIndex] += amplitudeVec->data[i];
  	}
  }

  /******* CONSTRUCT OUTPUT ************/

  /* Already done in the analysis section */

  DETATCHSTATUSPTR(status);
  RETURN(status);
}
