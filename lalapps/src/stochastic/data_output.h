/*
 * data_output.h - SGWB Standalone Analysis Pipeline
 *               - Data Output Function Prototypes
 * 
 * Copyright (C) 2002-2005 Adam Mercer
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
 * 02110-1301, USA
 *
 * $Id$
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <math.h>
#include <getopt.h>

#include <FrameL.h>

#include <lal/AVFactories.h>
#include <lal/Date.h>
#include <lal/FrameStream.h>
#include <lal/LALStdio.h>
#include <lal/FrequencySeries.h>
#include <lal/LIGOLwXML.h>
#include <lal/LIGOMetadataTables.h>
#include <lal/Units.h>

#include <lalapps.h>
#include <processtable.h>

/* save out ccSpectra as a frame file */
void write_ccspectra_frame(COMPLEX8FrequencySeries *series,
    CHAR *ifo_one,
    CHAR *ifo_two,
    LIGOTimeGPS epoch,
    INT4 duration);

/* save out xml tables */
void save_xml_file(LALStatus *status,
    LALLeapSecAccuracy accuracy,
    CHAR *program_name,
    CHAR *output_path,
    CHAR *base_name,
    StochasticTable *stochtable,
    MetadataTable proctable,
    MetadataTable procparams,
    ProcessParamsTable *this_proc_param,
    CHAR comment[LIGOMETA_COMMENT_MAX]);

/*
 * vim: et
 */
