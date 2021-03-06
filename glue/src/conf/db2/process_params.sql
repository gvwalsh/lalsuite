-- This file is part of the Grid LSC User Environment (GLUE)
-- 
-- GLUE is free software: you can redistribute it and/or modify it under the
-- terms of the GNU General Public License as published by the Free Software
-- Foundation, either version 3 of the License, or (at your option) any later
-- version.
-- 
-- This program is distributed in the hope that it will be useful, but WITHOUT
-- ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
-- FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
-- details.
-- 
-- You should have received a copy of the GNU General Public License along
-- with this program.  If not, see <http://www.gnu.org/licenses/>.

CREATE TABLE process_params
(
-- This table contains input parameters for programs.

-- Database which created this entry
      creator_db         INTEGER NOT NULL WITH DEFAULT 1,

-- Program name
      program            VARCHAR(64) NOT NULL,
-- Unique process ID (not unix process ID)
      process_id         CHAR(13) FOR BIT DATA NOT NULL,

-- The triplet will store the value of a single parameter.
-- One example might be param = "mass", type="REAL"
-- and value = "12345.6789"
      param              VARCHAR(32) NOT NULL,
      type               VARCHAR(16) NOT NULL,
      value              VARCHAR(1024) NOT NULL,
      
-- Insertion time (automatically assigned by the database)
      insertion_time     TIMESTAMP WITH DEFAULT CURRENT TIMESTAMP,

      CONSTRAINT procpar_pk
      PRIMARY KEY (process_id, creator_db, param),

-- Foreign key relationship to process table.  The 'ON DELETE CASCADE'
-- modifier means that if a row in the process table is deleted, then
-- all its associated parameters are deleted too.
      CONSTRAINT procpar_fk_pid
      FOREIGN KEY (process_id, creator_db)
          REFERENCES process(process_id, creator_db)
          ON DELETE CASCADE
)
-- The following line is needed for this table to be replicated to other sites
DATA CAPTURE CHANGES
;
-- Create an index based on program name
CREATE INDEX procpar_ind_name ON process_params(program)
;
