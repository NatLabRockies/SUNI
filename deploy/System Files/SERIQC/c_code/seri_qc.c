/* **************************************************************************
* seri_qc.c  Version 1.1
*
* Procedures:
*         int seri_qc1
*         int SQC_2C
*         int SQC_3C
*         int SolPosPriv
* **************************************************************************
*
*         seri_qc1 Return Values:  0    Ok
*                              non-0   various error codes
* **************************************************************************
*
*                               DISCLAIMER FOR
*                         SOFTWARE SUBMITTED TO OSTI
*
* This Software is provided by the National Renewable Energy Laboratory ("NREL"),
* which is operated by the Alliance for Sustainable Energy, LLC ("ALLIANCE") for
* the U.S. Department of Energy ("DOE").
*
* Access to and use of this Software shall impose the following obligations on
* the user, as set forth herein.  The user is granted the right, without any fee
* or cost, to use, copy, modify, alter, enhance and distribute this Software for
* any purpose whatsoever, provided that this entire notice appears in all copies
* of the Software.  Further, the user agrees to credit DOE/NREL/ALLIANCE in any
* publication that results from the use of this Software.  The names
* DOE/NREL/ALLIANCE, however, may not be used in any advertising or publicity to
* endorse or promote any products or commercial entities unless specific written
* permission is obtained from DOE/NREL/ALLIANCE.  The user also understands that
* DOE/NREL/Alliance is not obligated to provide the user with any support,
* consulting, training or assistance of any kind with regard to the use of this
* Software or to provide the user with any updates, revisions or new versions of
* this Software.
*
* YOU AGREE TO INDEMNIFY DOE/NREL/ALLIANCE, AND ITS SUBSIDIARIES, AFFILIATES,
* OFFICERS, AGENTS, AND EMPLOYEES AGAINST ANY CLAIM OR DEMAND, INCLUDING
* REASONABLE ATTORNEYS' FEES, RELATED TO YOUR USE OF THIS SOFTWARE.  THIS
* OFTWARE IS PROVIDED BY DOE/NREL/ALLIANCE "AS IS" AND ANY EXPRESS OR IMPLIED
* WARRANTIES, INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
* MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO
* EVENT SHALL DOE/NREL/ALLIANCE BE LIABLE FOR ANY SPECIAL, INDIRECT OR
* CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER, INCLUDING BUT NOT LIMITED TO
* CLAIMS ASSOCIATED WITH THE LOSS OF DATA OR PROFITS, WHICH MAY RESULT FROM AN
* ACTION IN CONTRACT, NEGLIGENCE OR OTHER TORTIOUS CLAIM THAT ARISES OUT OF OR
* IN CONNECTION WITH THE ACCESS, USE OR PERFORMANCE OF THIS SOFTWARE.
*
* ***************************************************************************
*
* MODIFICATIONS:
*              1997/12/11 SMW changed routine for reading QC0 file to
*              eliminate an incorrect negative value for the one-minute Kt
*              max.
*
*              1999/12/09 SMW and MDR corrected leap year algorithm that
*              failed to designate year 2000 as a leap year.
*
*              1999/12/09 SMW changed scope of if block in the routine
*              to compute minute-by-minute solar position.  Now conforms
*              with original FORTRAN code.
*
*              1999/12/09 SMW changed the low limits on XT and XD from zero
*              to the limits in the original Fortran code (0.05 and 0.03).
*
*              1999/12/09 SMW and MDR corrected the logic to calculate the
*              solar position over the measurement interval.  The problem
*              manifested itself as a significant error in the solar position
*              at one minute before the hour when working with one-minute
*              data. Additionally, the time of the interval used to
*              calculate solar position was incorrect by one minute for all
*              data.
*
*              1999/12/09 SMW and MDR changed the error checking for time.
*              The previous version allowed hours 0-24 and minutes 0-59,
*              but would not allow a time of 00:00.  The unstated convention
*              validated only times of 00:01 - 24:00.  Now the time 24:00
*              on day x is the same as 00:00 of day x+1.  The effect of
*              this is small, but worth noting: When the calling program
*              submits a time of, for example, 00:00 on January 1, 1990,
*              the program interprets this as time 24:00 on December 31,
*              1989.  Hence it will use the boundary values from December
*              rather than January for that call (assuming that the sun is
*              up at midnight).
*
*              1999/12/09 SMW and MDR changed the rounding routine for
*              determining the index into the Gompertz boundaries.  The
*              fix corrects situtations where a floating point number
*              representation is slightly low (such as
*              84.49999999987 + 0.5) and hence will not truncate to the
*              intended integer (85 in the above example).
*
*              1999/12/30 SMW added NREL Solpos module (Michalsky
*              algorithms).
*
*              2000/1/4 SMW changed the Timezone argument in the SolPos
*              wraparound from int to double.
*
*              2000/1/18 SMW and MDR changed the minute-by-minute solar
*              position calculations to divide the accumulated ETR and
*              ETRN values by the interval rather than the number of
*              sunup minutes.  This should give ETR values that are
*              representative of averaged solar measurements for partial
*              sunup intervals.  Also added a bounds check for the input
*              interval argument Intrvl.
*
*              2000/1/20 SMW added pivot for two-digit years (two-digit
*              years from 50 to 99 become year + 1900; years from 00 to
*              49 become year + 2000.  Also added a bounds checker for
*              valid solpos years 1950-2050.  Out of bounds years are
*              converted to the nearest valid year (1950 or 2050) or
*              valid leap year (1952 or 2048).
*
*              2000/3/6 MAA converted from C++ to C. Added error codes
*              and decoder function seri_qc_decode().
*
* Version 1.1  ----------------------------------------------------------------
*
*              2002/2/22 SMW tightened up code for input error checking,
*              primarily to force the function to terminate when corrupt
*              inputs might cause nastier problems later.
*
*              Removed reference to __WIN32__ and replaced with __DQMS__;
*              changed DQMSDir input parameter to QC0Dir
*
* Version 1.2  ----------------------------------------------------------------
*              2004/10/14 SMW changed the bottom two bins on all left curves
*			   to -60.0 to assure that for all zero (or near zero) kn values
*              kt can fall to the left of the curve. Solves the problem where
*              under heavily overcast skies, low global was being flagged as
*              outside the boundaries (or flag 9). The -60.0 value will keep
*              the boundary <= 0 even when shifted to the right.
*
*              2010/12/02 PJM and SMW fixed bug that would cause the function
*              to read the QC0 file with every call (length of station ID
*              comparison was set to 2 bytes, apparently a throwback to
*              DOS/VAX 8.3 convention that allowed only a two-character ID.
*
* Version 1.3  ----------------------------------------------------------------
*              A few minor changes made to the following areas during
*              benchmarking testing for the Python version.
*
*              2023/08/02 SMW and PP corrected code in the date walk-back
*              routine (approx line 840) to reference Monnow rather than
*              the Month variable. Note: This would only affect data when
*              the sun is up around midnight (unlikely except for locations
*              on the pole sides of the arctic and antarctic circles, but
*              more likely for data with GMT timestamps).
*
*              2023/08/02 SMW changed the QC0 file open error handling to
*              blank the  lastSite variable on failure (approx line 695) to
*              force failure in subsequent calls.
*
*              2023/09/01 SMW added code at the error handler return-point
*              at approx lines 755 for bad QC0 format to set all QC flags
*              to 00 (untested) with a non-zero error code. The lastSite
*              variable was also blanked to force a re-read of the QC0 file
*              on subsequent calls.
*
*              2023/09/01 SMW added code at the error handler return-point
*              at approximately line 1070 for undefined QC0 boundaries to
*              set all QC flags to 00 (untested) with a non-zero error code.
*              An IF statement was added at approximately line 1055 to
*              prevent a fault with a negative index for the XDm[] array.
*
*
* ************************************************************************** */
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <stdio.h>

#include "solpos.h"
#include "spa.h"
#include "seri_qc.h"

/* Uncomment the following line for DQMS */
/* #define __DQMS__ */

/*
 * Local function prototypes
 */

// int SQC_2C (
//      int Kt2,                 /* The value of Kt (integer %) */
//      int Kn2,                 /* The value of Kn (integer %) */
//      int *IQCt2,              /* The GLOBAL quality control flag */
//      int *IQCn2,              /* The DIRECT quality control flag */
//      int Il,                  /* The number of the left shape of the Gompertz curve */
//      int Ir,                  /* The number of the right shape of the Gompertz curve */
//      int Jl,                  /* The position number of the left Gompertz curve */
//      int Jr,                  /* The position number of the right Gompertz curve */
//      int KTmax,               /* The maximum allowable Kt (integer %) */
//      int KNmax                /* The maximum allowable Kn (integer %) */
// );

// int SQC_3C (
//      int Kt3,                 /* The value of Kt (integer %) */
//      int Kn3,                 /* The value of Kn (integer %) */
//      int Kd3,                 /* The value of Kd (integer %) */
//      int *IQCt3,              /* The GLOBAL quality control flag */
//      int *IQCn3,              /* The DIRECT quality control flag */
//      int *IQCd3               /* The DIFUSE quality control flag */
// );

#define maxX(i, j) ((i) > (j) ? (i) : (j))
#define minX(i, j) ((i) < (j) ? (i) : (j))

#ifndef M_PI
#define M_PI            3.14159265358979323846  /* pi */
#endif

#define LEFT 0
#define RIGHT 1
#define deg2rad  M_PI/180  /* 0.017453293 */

/*
 * Global declarations
 */

int NAM = 0;
double Solzen = 100.0;
double KT = -999, KN = -999, KD = -999;
char lastSite[50];
int lastMonth;
int KTend[4], KNend;
int LeftS[3] = {0, 0, 0};
int LeftP[3] = {0, 0, 0};
int IrightS[3] = {0, 0, 0};
int IrightP[3][4] = {{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}};
double Xlat=0, Xlon=0, Tzone=0;

/*
 * The value of Curve(I,J,K) represents 100 * Kt.  It is this value that
 * is used as the Gompertz boundary by QCFIT.  The curve represented here
 * is the first position of each type (position = 1).
 */

float curveLeft[6][100] = {
     {-60.0,-60.0,13.1,14.6, 15.8, 16.9, 17.9, 18.7, 19.6, 20.3,
     21.0, 21.7, 22.3, 22.9, 23.5, 24.1, 24.7, 25.2, 25.7, 26.2,
     26.7, 27.2, 27.7, 28.2, 28.6, 29.1, 29.5, 30.0, 30.4, 30.8,
     31.3, 31.7, 32.1, 32.5, 33.0, 33.4, 33.8, 34.2, 34.6, 35.0,
     35.4, 35.8, 36.2, 36.6, 37.0, 37.4, 37.8, 38.2, 38.6, 39.0,
     39.4, 39.8, 40.2, 40.6, 41.0, 41.4, 41.9, 42.3, 42.7, 43.1,
     43.5, 43.9, 44.4, 44.8, 45.2, 45.7, 46.1, 46.5, 47.0, 47.4,
     47.9, 48.3, 48.8, 49.3, 49.7, 50.2, 50.7, 51.2, 51.7, 52.2,
     52.7, 53.3, 53.8, 54.3, 54.9, 55.4, 56.0, 56.6, 57.2, 57.8,
     58.4, 59.1, 59.7, 60.4, 61.1, 61.8, 62.5, 63.3, 64.0, 64.8},

     {-60.0,-60.0,10.3,11.9, 13.3, 14.6, 15.7, 16.6, 17.6, 18.4,
     19.2, 20.0, 20.7, 21.4, 22.1, 22.7, 23.3, 24.0, 24.5, 25.1,
     25.7, 26.2, 26.8, 27.3, 27.8, 28.3, 28.8, 29.3, 29.8, 30.3,
     30.8, 31.3, 31.8, 32.2, 32.7, 33.2, 33.6, 34.1, 34.5, 35.0,
     35.5, 35.9, 36.4, 36.8, 37.3, 37.7, 38.2, 38.6, 39.1, 39.5,
     40.0, 40.4, 40.9, 41.3, 41.8, 42.2, 42.7, 43.2, 43.6, 44.1,
     44.6, 45.0, 45.5, 46.0, 46.5, 46.9, 47.4, 47.9, 48.4, 48.9,
     49.4, 49.9, 50.5, 51.0, 51.5, 52.0, 52.6, 53.1, 53.7, 54.2,
     54.8, 55.4, 56.0, 56.6, 57.2, 57.8, 58.4, 59.1, 59.7, 60.4,
     61.1, 61.8, 62.5, 63.2, 64.0, 64.8, 65.5, 66.4, 67.2, 68.1},

     {-60.0,-60.0,3.9,  6.1,  7.9,  9.4, 10.8, 12.1, 13.3, 14.3,
     15.4, 16.3, 17.3, 18.1, 19.0, 19.8, 20.6, 21.3, 22.1, 22.8,
     23.5, 24.2, 24.9, 25.5, 26.2, 26.8, 27.4, 28.1, 28.7, 29.3,
     29.9, 30.5, 31.0, 31.6, 32.2, 32.8, 33.3, 33.9, 34.4, 35.0,
     35.5, 36.1, 36.6, 37.2, 37.7, 38.3, 38.8, 39.3, 39.9, 40.4,
     40.9, 41.5, 42.0, 42.6, 43.1, 43.6, 44.2, 44.7, 45.2, 45.8,
     46.3, 46.9, 47.4, 48.0, 48.5, 49.1, 49.6, 50.2, 50.7, 51.3,
     51.9, 52.4, 53.0, 53.6, 54.2, 54.8, 55.3, 55.9, 56.5, 57.1,
     57.8, 58.4, 59.0, 59.6, 60.3, 60.9, 61.6, 62.2, 62.9, 63.6,
     64.3, 65.0, 65.7, 66.4, 67.1, 67.9, 68.6, 69.4, 70.1, 70.9},

     {-60.0,-60.0,-4.5,-1.7,  0.6,  2.7,  4.5,  6.1,  7.6,  9.0,
     10.3, 11.5, 12.7, 13.8, 14.9, 15.9, 16.9, 17.9, 18.9, 19.8,
     20.7, 21.5, 22.4, 23.2, 24.0, 24.8, 25.6, 26.4, 27.2, 27.9,
     28.7, 29.4, 30.1, 30.8, 31.5, 32.2, 32.9, 33.6, 34.3, 35.0,
     35.7, 36.4, 37.0, 37.7, 38.3, 39.0, 39.7, 40.3, 41.0, 41.6,
     42.3, 42.9, 43.6, 44.2, 44.9, 45.5, 46.1, 46.8, 47.4, 48.1,
     48.7, 49.4, 50.0, 50.6, 51.3, 51.9, 52.6, 53.2, 53.9, 54.6,
     55.2, 55.9, 56.5, 57.2, 57.9, 58.5, 59.2, 59.9, 60.6, 61.3,
     62.0, 62.7, 63.4, 64.1, 64.8, 65.5, 66.2, 66.9, 67.7, 68.4,
     69.1, 69.9, 70.7, 71.4, 72.2, 73.0, 73.8, 74.6, 75.4, 76.2},

     {-60.0,-60.0,1.3,  3.5,  5.4,  7.0,  8.5,  9.8, 11.1, 12.2,
     13.3, 14.3, 15.3, 16.3, 17.2, 18.0, 18.9, 19.7, 20.5, 21.3,
     22.1, 22.8, 23.6, 24.3, 25.0, 25.7, 26.4, 27.1, 27.8, 28.5,
     29.1, 29.8, 30.5, 31.1, 31.8, 32.4, 33.1, 33.7, 34.4, 35.0,
     35.6, 36.3, 36.9, 37.6, 38.2, 38.8, 39.5, 40.1, 40.8, 41.4,
     42.1, 42.7, 43.4, 44.0, 44.7, 45.4, 46.0, 46.7, 47.4, 48.1,
     48.8, 49.5, 50.2, 50.9, 51.6, 52.3, 53.1, 53.8, 54.6, 55.3,
     56.1, 56.9, 57.7, 58.5, 59.3, 60.2, 61.0, 61.9, 62.8, 63.7,
     64.6, 65.6, 66.5, 67.5, 68.5, 69.6, 70.6, 71.7, 72.9, 74.0,
     75.2, 76.5, 77.8, 79.1, 80.5, 82.0, 83.5, 85.1, 86.8, 88.5},

     {-60.0,-60.0,5.6,  7.5,  9.0, 10.4, 11.6, 12.7, 13.8, 14.7,
     15.6, 16.5, 17.4, 18.2, 18.9, 19.7, 20.4, 21.2, 21.9, 22.5,
     23.2, 23.9, 24.5, 25.2, 25.8, 26.4, 27.1, 27.7, 28.3, 28.9,
     29.5, 30.1, 30.8, 31.4, 32.0, 32.6, 33.2, 33.8, 34.4, 35.0,
     35.6, 36.2, 36.8, 37.5, 38.1, 38.7, 39.4, 40.0, 40.6, 41.3,
     42.0, 42.6, 43.3, 44.0, 44.7, 45.4, 46.1, 46.8, 47.6, 48.3,
     49.1, 49.9, 50.7, 51.5, 52.3, 53.2, 54.1, 55.0, 55.9, 56.9,
     57.8, 58.9, 59.9, 61.0, 62.2, 63.4, 64.6, 65.9, 67.3, 68.7,
     70.3, 71.9, 73.6, 75.5, 77.5, 79.7, 82.2, 84.9, 88.0, 91.5,
     95.8,101.0,107.8,117.8,136.8,999.9,999.9,999.9,999.9,999.9}
};

float curveRight[5][100] = {
     {13.4,17.2, 19.6, 21.5, 23.1, 24.5, 25.8, 26.9, 27.9, 28.9,
     29.8, 30.7, 31.5, 32.3, 33.0, 33.8, 34.5, 35.1, 35.8, 36.5,
     37.1, 37.7, 38.3, 38.9, 39.5, 40.1, 40.6, 41.2, 41.7, 42.3,
     42.8, 43.4, 43.9, 44.4, 44.9, 45.5, 46.0, 46.5, 47.0, 47.5,
     48.0, 48.5, 49.0, 49.5, 50.0, 50.5, 51.0, 51.5, 52.0, 52.5,
     53.0, 53.5, 54.0, 54.5, 55.0, 55.5, 56.0, 56.5, 57.0, 57.5,
     58.0, 58.5, 59.0, 59.5, 60.1, 60.6, 61.1, 61.6, 62.2, 62.7,
     63.2, 63.8, 64.3, 64.9, 65.5, 66.0, 66.6, 67.2, 67.8, 68.4,
     69.0, 69.6, 70.2, 70.8, 71.4, 72.1, 72.7, 73.4, 74.1, 74.7,
     75.4, 76.1, 76.9, 77.6, 78.3, 79.1, 79.9, 80.7, 81.5, 82.4},

     {18.1,21.2, 23.3, 24.9, 26.3, 27.5, 28.5, 29.5, 30.4, 31.2,
     32.0, 32.7, 33.4, 34.1, 34.7, 35.4, 36.0, 36.6, 37.1, 37.7,
     38.3, 38.8, 39.3, 39.8, 40.4, 40.9, 41.4, 41.9, 42.4, 42.8,
     43.3, 43.8, 44.3, 44.7, 45.2, 45.7, 46.1, 46.6, 47.0, 47.5,
     48.0, 48.4, 48.9, 49.3, 49.8, 50.2, 50.7, 51.2, 51.6, 52.1,
     52.5, 53.0, 53.5, 53.9, 54.4, 54.9, 55.3, 55.8, 56.3, 56.8,
     57.3, 57.8, 58.3, 58.8, 59.3, 59.8, 60.3, 60.8, 61.4, 61.9,
     62.4, 63.0, 63.6, 64.1, 64.7, 65.3, 65.9, 66.5, 67.1, 67.7,
     68.4, 69.0, 69.7, 70.4, 71.1, 71.8, 72.5, 73.3, 74.1, 74.9,
     75.7, 76.5, 77.4, 78.3, 79.3, 80.2, 81.2, 82.3, 83.4, 84.6},

     {22.8,25.3, 27.0, 28.4, 29.5, 30.4, 31.3, 32.1, 32.8, 33.5,
     34.2, 34.8, 35.4, 36.0, 36.5, 37.0, 37.5, 38.1, 38.5, 39.0,
     39.5, 39.9, 40.4, 40.8, 41.3, 41.7, 42.1, 42.6, 43.0, 43.4,
     43.8, 44.2, 44.7, 45.1, 45.5, 45.9, 46.3, 46.7, 47.1, 47.5,
     47.9, 48.3, 48.7, 49.1, 49.5, 49.9, 50.4, 50.8, 51.2, 51.6,
     52.0, 52.5, 52.9, 53.3, 53.8, 54.2, 54.6, 55.1, 55.6, 56.0,
     56.5, 57.0, 57.4, 57.9, 58.4, 58.9, 59.4, 60.0, 60.5, 61.0,
     61.6, 62.1, 62.7, 63.3, 63.9, 64.5, 65.2, 65.8, 66.5, 67.2,
     67.9, 68.7, 69.4, 70.2, 71.1, 72.0, 72.9, 73.8, 74.8, 75.9,
     77.0, 78.2, 79.5, 80.9, 82.4, 84.0, 85.9, 87.9, 90.2, 92.8},

     {28.0,29.9, 31.3, 32.3, 33.2, 33.9, 34.6, 35.2, 35.8, 36.4,
     36.9, 37.4, 37.8, 38.3, 38.7, 39.1, 39.5, 39.9, 40.3, 40.7,
     41.1, 41.4, 41.8, 42.2, 42.5, 42.8, 43.2, 43.5, 43.9, 44.2,
     44.5, 44.9, 45.2, 45.5, 45.9, 46.2, 46.5, 46.8, 47.2, 47.5,
     47.8, 48.2, 48.5, 48.8, 49.2, 49.5, 49.8, 50.2, 50.5, 50.9,
     51.2, 51.6, 51.9, 52.3, 52.6, 53.0, 53.4, 53.7, 54.1, 54.5,
     54.9, 55.3, 55.7, 56.1, 56.5, 57.0, 57.4, 57.9, 58.3, 58.8,
     59.3, 59.8, 60.3, 60.8, 61.3, 61.9, 62.5, 63.1, 63.7, 64.3,
     65.0, 65.7, 66.4, 67.2, 68.0, 68.9, 69.8, 70.8, 71.8, 72.9,
     74.2, 75.5, 77.0, 78.8, 80.7, 83.0, 85.9, 89.6, 94.8,103.9},

     {32.2,33.7, 34.8, 35.6, 36.3, 36.9, 37.4, 37.9, 38.3, 38.7,
     39.1, 39.5, 39.9, 40.2, 40.6, 40.9, 41.2, 41.5, 41.8, 42.1,
     42.4, 42.7, 43.0, 43.3, 43.6, 43.8, 44.1, 44.4, 44.6, 44.9,
     45.2, 45.4, 45.7, 45.9, 46.2, 46.5, 46.7, 47.0, 47.2, 47.5,
     47.8, 48.0, 48.3, 48.5, 48.8, 49.1, 49.3, 49.6, 49.9, 50.2,
     50.4, 50.7, 51.0, 51.3, 51.6, 51.9, 52.2, 52.5, 52.8, 53.1,
     53.4, 53.7, 54.1, 54.4, 54.7, 55.1, 55.5, 55.8, 56.2, 56.6,
     57.0, 57.4, 57.8, 58.2, 58.7, 59.2, 59.6, 60.1, 60.7, 61.2,
     61.8, 62.4, 63.0, 63.7, 64.4, 65.2, 66.0, 66.9, 67.8, 68.9,
     70.1, 71.4, 73.0, 74.8, 77.0, 80.0, 84.2, 91.9,999.9,999.9}
};

/* returns next line from file as a string */
static void getline(FILE *fp, char *line) {
   int i=0, c;

   while( (c=fgetc(fp)) != '\n' ) {
     line[i++] = c; /* add next char */
   }

   line[i] = '\0'; /* terminate the string */

   return;
}

/*   Subroutine SERI_QC1 ( Site, Iyear, Month, Iday, Ihour, Minute,
                                    ^IN^   ^IN^   ^IN^  ^IN^   ^IN^   ^IN^

      2                    Intrvl, Global, Direct, Difuse,
                                     ^IN^    ^IN^ ^IN^ ^IN^

      3                         IQCglo, IQCdir, IQCdif )
                            ^OUT^   ^OUT^   ^OUT^

 February, 1990
 Martin Rymes
 The Solar Energy Research Institute, Golden, CO  80401

 Performs QC checks on the major broadband solar measurements:
     Global Horizontal or Total (T)
     Direct Normal (N)
     Diffuse Horizontal (D)
 The time passed to SERI_QC1 should be the time of the END of the
     measurement.
 Only limits checking will be performed if the solar zenith angle
     exceeds 80 degrees.
 If any parameter is greater than 8000, it is assumed missing.

 FORTRAN convention in force:
     I - N initial letter is VAX DEFAULT (Undeclared) INTEGER
     "Fin" is LOGICAL
     "Site", "Sitold", "Colon", and all variables preceded by "C_"
          are CHARACTER strings.
     All other variables are VAX DEFAULT REAL
     Arrays are explicitly sized

 Uses file:
     Infile  => S_<Site>.QC0, where <Site> is the site identifier.
             This file is opened as unit number 73.

 INPUTS:
     -REAL-
     Difuse    => Diffuse horizontal broadband solar radiation, W/sq m
     Direct    => Direct normal broadband solar radiation, W/sq m
     Global    => Global horizontal broadband solar radiation, W/sq m
     -INTEGER-
     Iday => The day of the month (1-31)
     Ihour     => The hour of the day (0-24)
     Intrvl    => The averaging interval in minutes (1-60)
     Iyear     => The year, e.g., 1988
     Minute    => The minute of the hour (0-59)
     Month     => The month of the year (1-12)
     -CHARACTER*6-
     Site => Site identifier.

 OUTPUTS (INTEGER):
     IQCdif    => The DIFUSE quality control flag
     IQCdir    => The DIRECT quality control flag
     IQCglo    => The GLOBAL quality control flag

 VALUES OF IQC:

      0 - untested parameter

      1 - only one parameter present; passed limits test
      2 - two parameters present; data fell within 3% of the expected
          2D boundaries for this station-month and airmass regime
          (supersedes 1)
      3 - three parameters present; internally consistent within 3%
          of expected values (supersedes 1 and 2)

 (4-6 UNUSED in this subroutine)
      4 - parameter inspected by hand and eye; passed inspection
          (superseded by 1-3)
      5 - parameter inspected by hand and eye; did not pass inspection
          (supersedes 1-3)
      6 - parameter was received as missing; was estimated

      7 - parameter LOWER than allowed minimum:
          ETR = 0, minimum is 0.0 W/sq m
          ETR > 0, minimum is Kn = 0.0, Kt = 0.1, Kd = 0.05
      8 - parameter HIGHER than allowed maximum:
          ETR = 0, maximum is 10.0 W/sq m
          ETR > 0, maximum is Knmax + 0.1, Ktmax, and Kdmax + 0.05
      9 - parameter value within 3% compared with the other two
          parameters, but failed 1-component or 2-component tests.

     10-93 - parameter exceeded the 3% tolerance in one of 4 ways:
               0 - TOO LOW by 3-parameter coupling
               1 - TOO HIGH by 3-parameter coupling
               2 - TOO LOW by 2D boundary comparison
               3 - TOO HIGH by 2D boundary comparison
          The particular error is determined by the remainder of
          MOD ( IQC + 2, 4 ).  The percentage error is determined
          by:
               IPCT = Int ( ( IQC + 2 ) / 4 )

          The error, then, is between IPCT% and ( IPCT + 1)%,
          except that when IPCT = 23, the error is greater than
          23%.

          EXAMPLE:
               IQC  = 67 becomes 69 when 2 is added.
               MOD ( 69, 4 ) = 1, or a "coupled high" error was
                    detected first.
               Ipct = Int ( 69 / 4 ) = 17, so the error is
                    between 17% and 18%.

          NOTE:     The percent error is:
                    100 x (Measured - Modeled) / ETR

     94-97:  KN = KT + ERR:

               FLAG ERR

                94   5% ETR =< ERR < 10% ETR
                95  10% ETR =< ERR < 15% ETR
                96  15% ETR =< ERR < 20% ETR
                97  20% ETR =< ERR

     99 - parameter is missing.

          2/1/91 Modified with the following line to allow linking with Turbo C

          BC EXTERNAL     SERI_QC1
*/



int seri_qc1 (
     char *Site,         /* S_<Site>.QC0, where <Site> is the site identifier. */
     char *QC0Dir,       /* directory where QC0 files are installed */
     int Iyear,          /* The year, e.g., 1988 */
     int Month,          /* The month of the year (1-12) */
     int Iday,           /* The day of the month (1-31) */
     int Ihour,          /* The hour of the day (0-24) */
     int Minute,         /* The minute of the hour (0-59) */
     int Intrvl,         /* The averaging interval in minutes (1-60) */
     double Global,      /* Global horizontal broadband solar radiation, W/sq m */
     double Direct,      /* Direct normal broadband solar radiation, W/sq m */
     double Difuse,      /* Diffuse horizontal broadband solar radiation, W/sq m */
     int *IQCglo,        /* The GLOBAL quality control flag */
     int *IQCdir,        /* The DIRECT quality control flag */
     int *IQCdif         /* The DIFUSE quality control flag */
)


{
     int Mondays[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

     double Alog_4=1.386294361; /*, DegRad=0.017453292; */
     double XDm[5] = { 0.19, 0.22, 0.24, 0.28, 0.32 };

     char C_3in[4], C_mon3[12][4] = {
          "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"};

     char Sitold[51]="                                                  ";

     int Itime, ly;
     double XT, XN, XD;
     double ETR, ETRN, Sunup, Fraction, airMass;
     int Minnow, Ihrnow, Idynow, Monnow, Iyrnow;
     double Solznow, ETRnow, ETRNnow;
     int Ires, Intbin;
     int Il, Jl, Ir, Jr;
     double  XDmax, XNmax, XTmax;
     int Numpar, KNmax, KTmax, I;
     int retval = 0;

     static struct posdata spdata, *spdat; /* solpos structure and pointer */
     static spa_data pdata, *pdat; /* SPA structure and pointer */


/* If no checks are made, the flags should be 0. */

     /* preliminaries for S_solpos */
     spdat = &spdata;  /* point to solpos structure */
     pdat = &pdata;  /* point to solpos structure */

     *IQCglo = *IQCdir = *IQCdif = 0;

// #if DEBUG
        fprintf(stderr, "Site=%s QC0Dir=%s Iyear=%d Month=%d Iday=%d Ihour=%d Minute=%d Intrvl=%d Global=%.2f Direct=%.2f Difuse=%.2f\n",
                                  Site, QC0Dir, Iyear, Month, Iday, Ihour, Minute, Intrvl, Global, Direct, Difuse);
// #endif
     /*
         * SERI_QC1 was invoked, but the inputs are incorrect.
         * Notify the user and leave SERI_QC1.
      */

     Itime = Ihour * 60 + Minute;
     if ( strcmp(Site, "      ") == 0 ) {
                retval |= (1 << E_SITE);
     }
     if ( (Month<1) || (Month>12) ) {
          retval |= (1 << E_MONTH);
     }
     if (( Iday < 1 ) || ( Iday > 31 )) {
          retval |= (1 << E_DAY);
     }
     if (( Ihour < 0 ) || ( Ihour > 24 ))    {
          retval |= (1 << E_HOUR);
     }
     if (( Minute < 0 ) || ( Minute > 59 )) {
          retval |= (1 << E_MINUTE);
     }

/*
 * 1999/12/09 SMW and MDR changed the following minimum bound for Itime
 *   else if (( Itime < 1 ) || ( Itime > 1440 )) {
 */
     if (( Itime < 0 ) || ( Itime > 1440 )) {
                retval |= (1 << E_TIME);
     }
        if (( Intrvl < 1 ) || ( Intrvl > 60 )) {
          retval |= (1 << E_INTERVAL);
     }


     if (retval != 0){
        fprintf(stderr, "Return 1: %d\n", retval);
        return retval;
     }
/*
 * 1999/12/09 SMW and MDR added the following block to standardize midnight
 */

     /* Convert time 00:00 to time 24:00 of the previous day */
     if (Ihour == 0 && Minute == 0)
     {
       Ihour = 24;
       Iday = Iday - 1;
       if (Iday == 0)
       {
         Month = Month - 1;
         if (Month == 0)
         {
           Month = 12;
           Iyear = Iyear - 1;
           if (Iyear < 0)
             Iyear = 99;
         }
         Iday = Mondays[Month-1];

         /* leap year */
         if (Iyear % 4 == 0 &&
             (Iyear % 100 != 0 || Iyear % 400 == 0 ) &&
             Month == 2)
               Iday = Iday + 1;
       }
     }

/*
 * 2000/01/21 SMW added the following block to bound years to conform
 * to the 1950-2050 valid range of S_solpos
 */

    /* convert two-digit years with a pivot:
     * 50-99 become 1950-1999; 00-49 become 2000-2049
     */
     if (Iyear < 50)
       Iyear += 2000;
     else if (Iyear < 100)
       Iyear += 1900;

     /*
      * map out of bound years to the closest valid year (1950 or 2050,
      * or leap year (1952 or 2048)
      */

     ly = 0; /* leap year modifier */
     if (Iyear % 4 == 0 && (Iyear % 100 != 0 || Iyear % 400 == 0 ))
       ly = 2;

     /* remap errant years */
     if (Iyear < 1950)
       Iyear = 1950 + ly;
     if (Iyear > 2050)
       Iyear = 2050 - ly;


/*
 * If this is the current site and month, continue processing it (3000).
 *
 *   If ( Site .eq. Sitold .and. Month .eq. Monold )   Go to 3000
 *
 */
     /* read QC0 file if site or month has changed */
     if ((strncmp(Site,lastSite,50)!=0) || (lastMonth!=Month))
     {
          char QC0FileName[30];
                FILE *QC0File;
          char inputline[400];
          char dummy[50];
          char *endptr;
                int i,j;

          S_init( spdat ); /* initialize the solpos structure */
          spdat->second = 0;  /* minute resolution */
//          spdat->function = ( S_REFRAC | S_ETR ); /* choose functions */
          spdat->function &= ~S_DOY; /* configure for month and day */

		  /* init the SPA structure */
          pdat->second = 0;  /* minute resolution */
		  pdat->function = SPA_ALL;
    pdat->delta_ut1     = 0;
    pdat->delta_t       = 67;
    pdat->pressure      = 820;
    pdat->temperature   = 11;
    pdat->slope         = 0;
    pdat->azm_rotation  = 0;
    pdat->atmos_refract = 0.5667;

          /*
           * Read site-specific information.
           * Convert the site I.D. into a filename.
           */
          strncpy(lastSite,Site,50);
          lastMonth = Month;

          /*
           * Attempt to open the file.  If the site name does not conform to a
           * S_<id>.QC0 identifier, abort (at 2000).
           */

          /* setup QC0FileName */
#ifdef __DQMS__
          sprintf(QC0FileName,"%s\\CONFIG\\s_%s.qc0", QC0Dir, Site);
#else
          sprintf(QC0FileName,"%ss_%s.qc0", QC0Dir, Site);
#endif
          fprintf(stderr, "QC0FileName: %s\n", QC0FileName);
          QC0File = fopen(QC0FileName, "r");
          if (!QC0File) {
              // 8/2/23 SMW added following line
			  // Blank lastSite if invalid to force error on future calls
			  strcpy(lastSite, "");
               retval |= (1 << E_QC0_FILE);
               /* no sense continuing if the QC-ZERO file isn't found */
            fprintf(stderr, "Return 2: %d\n", retval);
            return retval;
          }

          /*
           * Read the S_<id>.QC0 file.  The reading of C_1IN is a dummy read that
           * skips lines.  Since only one month is read, lines are skipped down
           * to that month.  Checks are made to confirm that the QC0 file is in
           * the proper format.
           */

          getline(QC0File, inputline);
          (void)fscanf(QC0File, "%s %s %lf\n", dummy, dummy, &Xlat);
          (void)fscanf(QC0File, "%s %s %lf\n", dummy, dummy, &Xlon);
          (void)fscanf(QC0File, "%s %s %s %lf\n", dummy, dummy, dummy, &Tzone);
// #if DEBUG
          fprintf(stderr, "inputline(first): %s\n", inputline);
          fprintf(stderr, "Xlat=%f Xlon=%f Tzone=%f\n", Xlat, Xlon, Tzone);
// #endif

          /* inform SPA of the site parameters */
          pdat->latitude  = Xlat;
          pdat->longitude = Xlon;
          pdat->timezone  = Tzone;

          /* inform solpos of the site parameters */
          spdat->latitude  = Xlat;
          spdat->longitude = Xlon;
          spdat->timezone  = Tzone;


// #if DEBUG
          fprintf(stderr, "Month=%d\n", Month);
// #endif
          /* (Fast-forward to the month in question.)
                   - adjusted to skip 5 comment lines - MAA */
          for (i=1;i<(Month+5);i++) {
               getline(QC0File, inputline);
          }
// #if DEBUG
          fprintf(stderr, "inputline(i=%d): %s\n", i, inputline);
// #endif
          strncpy(C_3in,inputline,4);

          KNend = (int)strtol(inputline+5, &endptr, 10);
          /* 971212 RJN Bug fix KTend[0] = (int)strtol(endptr, &endptr, 10); */
          KTend[0] = (int)strtol(endptr+1, &endptr, 10);
          KTend[1] = (int)strtol(endptr+1, &endptr, 10);
          KTend[2] = (int)strtol(endptr+1, &endptr, 10);
          KTend[3] = (int)strtol(endptr+1, &endptr, 10);
          for (i=0;i<3;i++) {
               LeftS[i] = (int)strtol(endptr+1, &endptr, 10);
               LeftP[i] = (int)strtol(endptr+1, &endptr, 10);
               IrightS[i] = (int)strtol(endptr+1, &endptr, 10);
               for (j=0;j<4;j++) {
                    IrightP[i][j] = (int)strtol(endptr+1, &endptr, 10);
               }
          }
          if ( strncmp(C_3in,C_mon3[Month-1],3) != 0 ) {
               retval |= (1 << E_QC0_FORMAT);
            /* no sense continuing if the QC-ZERO file is corrupt */
            /* 2023/09/01 SMW added the following five lines to force QC flags
		       to 00 when returning error codes and to force a re-read of the
               qc0 file if the calling program doesn't terminate. */
 			fclose(QC0File);
			strcpy(lastSite, "");
            *IQCglo = 0;
            *IQCdir = 0;
            *IQCdif = 0;
            fprintf(stderr, "Return 3: %d\n", retval);
            return retval;
          }
          (void)fclose(QC0File);
     }

#if 0
 //
 //  Go to 3000
 // Label 3000 is achieved if either SITOLD = SITE and MONOLD = MONTH
 // or the S_<fn>.QC0 file was successfully read.
 // 3000 Continue

 //  if (MEMDEBUG) cout << "\n        sB " << coreleft() << " " << farcoreleft();
 //
#endif

/*
 * The input data seem to be valid.  Remember them as the "old" values
 * so that S_<id>.QC0 files do not need to be reopened.
 */

     strcpy(Sitold,Site);
#if 0
//   long Monold = Month;
#endif

/*
 * Initial assumed values for the last 4 output parameters, in case
 * SERI_QC1 never computes them (nighttime assumed, bogus AMASS).
 */
     XT = 0.0;
     XN = 0.0;
     XD = 0.0;

/*
 * Where is the sun?  Compute the zenith angle, ETR, and ETRN by
 * averaging the per-minute values
 */

     Solzen   = 0.0;
     ETR      = 0.0;
     ETRN     = 0.0;
     Sunup    = 0.0;
     Fraction = 0.0;
     airMass  = -9.99;

     Minnow = Minute - Intrvl;
     Ihrnow = Ihour;
     Idynow = Iday;
     Monnow = Month;
     Iyrnow = Iyear;

/* If necessary, begin in the previous hour (day (month (year))) */

     if ( Minnow < 0 ) {
          Minnow = 60 + Minnow;
          Ihrnow = Ihrnow - 1;
          if ( Ihrnow < 0 ) {
               Ihrnow = 23;
               Idynow = Idynow - 1;
/* 1999/12/09 SMW corrected if block below to conform with original Fortran code */
               if ( Idynow == 0 ) {
                          Monnow = Monnow - 1;
                 if ( Monnow == 0 ) {
                    Monnow = 12;
                         Iyrnow = Iyrnow - 1;
                       if ( Iyrnow < 0 ) Iyrnow = 99;
                 }
                 Idynow = Mondays[Monnow-1];
#if 0
                 // update leap year checker ??? for 400
                 // if ( Iyear%4 == 0 ) && ( Month > 2 ) && ( Iyear%400 != 0 ) Numday = Numday + 1
#endif
/*
 * 1999/12/09 SMW and MDR changed leap year algorithm below
 *               if (( Monnow == 2 ) && ( Iyrnow%4 == 0 )) Idynow = Idynow + 1;
 */
                if ( (( Iyear%4) == 0) &&
                     (((Iyear%100) != 0) || ((Iyear%400) == 0)) &&
/* 2023/08/02 SMW and PP corrected the following line to Monnow
					 (Month == 2) )
 */					 (Monnow == 2) )
                  Idynow = Idynow + 1;
              }
            }
          }

          for (I=0;I<=Intrvl;I++) {
/*
 * 1999/12/09 SMW and MDR moved the following line to the end of the loop
 *        Minnow = Minnow + 1;
 * 1999/12/09 SMW and MDR introduced the floating point variable Fraction to
 *            properly weight the contribution of each minute to the interval
 *            average solar position.  Also removed the integer minute
 *            accumulator Msunup and substituted the floating point Sunup
 */
            if ( I == 0 || I == Intrvl)
              Fraction = 0.5;
            else
              Fraction = 1.0;

            if ( Minnow == 60 ) {
              Minnow = 0;
              Ihrnow = Ihour;
              Idynow = Iday;
              Monnow = Month;
              Iyrnow = Iyear;
            }

            Solznow=0;
            ETRnow=0;
            ETRNnow=0;

            /* give SPA a timecheck */
            pdat->year    = Iyrnow;
            pdat->month   = Monnow;
            pdat->day     = Idynow;
            pdat->hour    = Ihrnow;
            pdat->minute  = Minnow;

            /* give solpos a timecheck */
            spdat->year    = Iyrnow;
            spdat->month   = Monnow;
            spdat->day     = Idynow;
            spdat->hour    = Ihrnow;
            spdat->minute  = Minnow;

            /* call SPA for zenith angle */
            spa_calculate( pdat );

            /* call solpos for ETR and ETRN */
          spdat->function = ( S_REFRAC | S_ETR ); /* choose function to populate erv */
          spdat->function &= ~S_DOY; /* configure for month and day */

		  retval = S_solpos( spdat ); // calculates erv
//printf("%d-%d-%d, %d:%d, %f, %f, %f\n", Iyrnow, Monnow, Idynow, Ihrnow, Minnow, spdat->zenetr, spdat->zenref, pdat->zenith);
		  spdat->coszen = cos(deg2rad*(pdat->zenith));  // overwrite solpos zenith angle with that from SPA
          spdat->function = ( L_ETR ); /* choose function to calculate etr and etrn */
		  S_solpos( spdat );

            /* extract solar stuff */
            Solznow = pdat->zenith;
            ETRnow  = spdat->etr;
            ETRNnow = spdat->etrn;

            if ( ETRnow > 0.0 ) {
              Sunup = Sunup + 1.0 * Fraction;
              Solzen = Solzen + Solznow * Fraction;
              ETR = ETR + ETRnow * Fraction;
              ETRN = ETRN + ETRNnow * Fraction;
            }
            Minnow = Minnow + 1;
          } /* for (I=0;I<=Intrvl;I++) */

         if ( Sunup > 0.0 ) {
           Solzen = Solzen / Sunup;
           ETR    = ETR    / (float) Intrvl;
           ETRN   = ETRN   / (float) Intrvl;
         }
         else {
           Solzen = 100.0;
         }

/*
 * Missing parameters are 99.  Otherwise, assume the data pass test
 * level 1.
 */

/* reset KT etc. */
          KT = -999, KN = -999, KD = -999;

          *IQCglo = 1;
          if ( Global > 8000.0 ) {
            *IQCglo = 99;
            KT    = 9900;
          }

          *IQCdir = 1;
          if ( Direct > 8000.0 ) {
            *IQCdir = 99;
            KN    = 9900;
          }

          *IQCdif = 1;
          if ( Difuse > 8000.0 ) {
            *IQCdif = 99;
            KD    = 9900;
          }


/*
 * Compute Kt, Kn, Kd (called XT, XN, XD).  The number should be between
 * 0 and 1.  If ETR = 0, it is night.
 */

         if ( *IQCglo < 99 ) {
           if ( ETR == 0.0 ) {
             if ( Global < -10.0 ) *IQCglo = 7;
           else if ( Global > 10.0 ) *IQCglo = 8;
         }
         else
           XT = Global / ETR;
     }

     if ( *IQCdir < 99 ) {
       if ( ETR == 0.0 ) {
         if ( Direct < -10.0 ) *IQCdir = 7;
         else if ( Direct > 10.0 ) *IQCdir = 8;
       }
       else
         XN = Direct / ETRN;
       }

       if ( *IQCdif < 99 ) {
         if ( ETR == 0.0 ) {
           if ( Difuse < -10.0) *IQCdif = 7;
           else if ( Difuse > 10.0 ) *IQCdif = 8;
         }
         else
           XD = Difuse / ETR;
       }

/* Done with processing of nighttime values. */

      if ( ETR == 0.0 ) {
        fprintf(stderr, "Return 4: %d (Solzen: %.4f)\n", retval, Solzen);
        return retval;
    }

/* KT, KN, and KD are PERCENT Kt, Kn, Kt in integer form. */

#if 0
//   if ( KT != 9900 ) KT = (int)( XT * 100.0 + 0.5 );
//   if ( KN != 9900 ) KN = (int)( XN * 100.0 + 0.5 );
//   if ( KD != 9900 ) KD = (int)( XD * 100.0 + 0.5 );
#endif

     /*
      * RJN 920210 - Before truncating with int, make sure KT, KN, KD
      *   are within bounds of int (-32768, 32768)
      */

     if ( KT != 9900 ) KT = ( XT * 100.0 + 0.5 );
     if ( KN != 9900 ) KN = ( XN * 100.0 + 0.5 );
     if ( KD != 9900 ) KD = ( XD * 100.0 + 0.5 );
     fprintf(stderr, "    - C - XT: %.6f, XN: %.6f, KT: %.4f, KN: %.4f\n", XT, XN, KT, KN);

     if (KT >= 32768.) KT = 32768.;
     else if (KT <= -32768.) KT = -32768.;
     else KT = (int)KT;

     if (KN >= 32768.) KN = 32768.;
     else if (KN <= -32768.) KN = -32768.;
     else KN = (int)KN;

     if (KD >= 32768.) KD = 32768.;
     else if (KD <= -32768.) KD = -32768.;
     else KD = (int)KD;

     /*
      * Calculate airmass.
      *   (From F. Kasten and A. T. Young, Revised optical air mass tables and
      *    approximation formula, Applied Optics, 14 (22), 4735-4738, 1989.)
      */

     airMass = 1.0 / (cos(Solzen*deg2rad) + 0.50572 / pow(96.07995-Solzen,1.6364) );

     /* Airmass regimes:  1 = low, 2 = middle, 3 = high. */

     if ( airMass > 2.5 ) NAM = 3;
     else if ( airMass > 1.25 ) NAM = 2;
     else NAM = 1;


     fprintf(stderr, "Airmass: %.4f ", airMass);
     fprintf(stderr, "Solzen: %.4f ", Solzen);
     fprintf(stderr, "ETR: %.4f\n", ETR);

     /*
      * INTBIN is an integer from 1 to 4, signifying the place of the digit
      * containing the information in the S_<id>.QC0 file.  If data approx-
      * imate 1-minute resolution, 1 is chosen; if the resolution approx-
      * imates 64 minutes, 4 is chosen.  INTRVL should be bounded by 1 and 60.
      */

     Ires = maxX( Intrvl, 1 );
     Ires = minX( Ires, 60 );
     Intbin = (int) ( 1.49 + log(Ires) / Alog_4 );

     /*
      * The Gompertz curve numbers were read from the .QC0 file.
      * "l" stands for "left" and "r" stands for "right".  "I" represents
      * the shape and "J" represents the position.
      */

     Il = LeftS[NAM-1];
     Jl = LeftP[NAM-1];
     Ir = IrightS[NAM-1];
     Jr = IrightP[NAM-1][Intbin-1];

     if ( Il == 0 ) {
       retval |= (1 << E_L_BOUND);
     }
     if ( Jl == 0 ) {
       retval |= (1 << E_L_BOUND);
     }
     if ( Ir == 0 ) {
       retval |= (1 << E_R_BOUND);
     }
     if ( Jr == 0 ) {
       retval |= (1 << E_R_BOUND);
     }

     /*
      * Get theoretical maximum insolation values, KTmax, KNmax, KDmax
      * (called XTmax, XNmax, and XDmax, respectively).  The formula for XDmax
      *  is justified in the user guide.
      */

     /* 2023-09-01 SMW added the following if statement to prevent index error */
     if (Ir > 0)
		 XDmax = XDm[Ir-1] + 0.025 * ( Jr + 3 );
     XNmax = KNend / 100.0;
     XTmax = KTend[Intbin-1] / 100.0;

     if ( KNend == 0 ) {
       retval |= (1 << E_KN_MAX);
     }
     if ( KTend[Intbin-1] == 0 ) {
       retval |= (1 << E_KT_MAX);
     }

     fprintf(stderr, "    - C - Solzen: %.6f, ETR: %.6f, ETRN %.6f, XT: %.6f, KT: %.6f, XN: %.6f, KN: %.6f, XD: %.6f, KD: %.6f, ", Solzen, ETR, ETRN, XT, XT * 100.0 + 0.5, XN, XN * 100.0 + 0.5, XD, XD * 100.0 + 0.5);

     /* all tests are complete, bail out if necessary */
     if (retval != 0)
     /* 2023/09/01 SMW added the following three lines of code to force QC flags
	    to 00 when returning error codes */
	 {
	    *IQCglo = 0;
	    *IQCdir = 0;
	    *IQCdif = 0;
        fprintf(stderr, "Return 5: %d\n", retval);
        return retval;
     }

     /*
      * As the user guide explains, Ktmax and Knmax must be adjusted
      * downwards for increasing airmass.
      */

     if ( NAM == 2 ) {
       XTmax = XTmax - 0.025;
       XNmax = XNmax - 0.050;
     }
     else if ( NAM == 3 ) {
       XTmax = XTmax - 0.1;
       XNmax = XNmax - 0.15;
     }
     fprintf(stderr, "XTmax: %.6f, XNmax: %.6f, XDmax: %.6f\n", XTmax, XNmax, XDmax);
/* Is each parameter within theoretical limits? (1-parameter check) */

/* Global (NOTE:  Max Kt is 0.10 larger than the Gompertz right boundary): */

     if ( *IQCglo < 99 ) {
       /* 1999/12/09 SMW corrected low limit on XT to conform to original Fortran */
       /* if ( XT < 0.0 ) *IQCglo = 7; */

       if ( XT < 0.05 ) *IQCglo = 7;
       else if ( XT > (XTmax + 0.10) ) *IQCglo = 8;
     }

/* Direct: */

     if ( *IQCdir < 99 ) {
       if ( Direct < -10.0 ) *IQCdir = 7;
       else if ( XN > XNmax ) *IQCdir = 8;
     }

/* Diffuse: */

     if ( *IQCdif < 99 ) {
       /* 1999/12/09 SMW corrected low limit on XD to conform to original Fortran */
       /* if ( XD < 0.0 ) *IQCdif = 7; */

       if ( XD < 0.03 ) *IQCdif = 7;
       else if ( XD > XDmax ) *IQCdif = 8;
     }

     /*
      * Go no further if the solar zenith angle is greater than 80 degrees.
      * However, don't use a flag of 7 if the GLOBAL or DIFUSE are not less
      * than -10 W/sq m (thermocouple response effect).  Also, if the ETR is
      * 25 W/sq m or less, a GLOBAL value of 10 W/sq m should not be
      * considered too high.
      */

     if ( Solzen > 80.0 )     {
       if (( *IQCglo == 7 ) && ( Global >= -10.0 )) *IQCglo = 1;
       if (( *IQCdif == 7 ) && ( Difuse >= -10.0 )) *IQCdif = 1;
       if (( *IQCglo == 8 ) && ( ETR <= 25.0 ) && ( Global <= 10.0 )) *IQCglo = 1;
       fprintf(stderr, "Return 6: %d\n", retval);
       return retval; /* changed from exit */
     }

/* If no more than 2 parameters are present (count them first), stop. */

     fprintf(stderr, "glo, dir, dif: %d, %d, %d\n", *IQCglo, *IQCdir, *IQCdif);
     Numpar = 0;
     if ( *IQCglo == 1 ) Numpar = 1;
     if ( *IQCdir == 1 ) Numpar = 1 + Numpar;
     if ( *IQCdif == 1 ) Numpar = 1 + Numpar;

     if ( Numpar <= 1 ) {
        fprintf(stderr, "Return 7: %d\n", retval);
        return retval; /* was exit */
    }

/* Do the KN < KT check: */

     if (( *IQCglo == 1 ) && ( *IQCdir == 1 )) {
          int Khigh = KN - KT;
          fprintf(stderr, "KN: %.6f, KT: %.6f, Khigh: %d\n", KN, KT, Khigh);
          if ( Khigh >= 20 ) {
               *IQCglo = 97;
               *IQCdir = 97;
               fprintf(stderr, "Return 8: %d\n", retval);
               return retval;
          }
          else if ( Khigh >= 15 ) {
               *IQCglo = 96;
               *IQCdir = 96;
               fprintf(stderr, "Return 9: %d\n", retval);
               return retval;
          }
          else if ( Khigh >= 10 ) {
               *IQCglo = 95;
               *IQCdir = 95;
               fprintf(stderr, "Return 10: %d\n", retval);
               return retval;
          }
          else if ( Khigh >=  5 ) {
               *IQCglo = 94;
               *IQCdir = 94;
               fprintf(stderr, "Return 11: %d\n", retval);
               return retval;
          }
     }
/* Perform the 3-parameter test.  Exit if it is negative. */

     if ( Numpar == 3 ) {
          fprintf(stderr, "%.2f, %.2f, %.2f, %d, %d, %d\n", KT, KN, KD, *IQCglo, *IQCdir, *IQCdif);
          SQC_3C( KT, KN, KD, IQCglo, IQCdir, IQCdif );
          if ( *IQCglo > 3 )  {
            fprintf(stderr, "Return 12: %d\n", retval);
            return retval;
        }
     }

     /*
      * Prepare for the 2-parameter test by establishing the maximum
      * percent KT and KN.

      * 1999/12/09 SMW and MDR changed the following two lines to correct a
      * rounding problem due to floating point representation.  The
      * extra .01 fixes any value that's a low representation and is
      * outside the granularity of the number being rounded.

      * int KNmax = XNmax * 100.0 + 0.5;
      * int KTmax = XTmax * 100.0 + 0.5;
      */

     KNmax = XNmax * 100.0 + 0.51;
     KTmax = XTmax * 100.0 + 0.51;

/* Perform the 2-parameter test.  Try KT/KN. */

     if (( *IQCglo <= 3 ) && ( *IQCdir <= 3 )) {
          fprintf(stderr, "IQCglo <= 3 && IQCdir <= 3 branch\n");
          fprintf(stderr, "%.2f, %.2f, %d, %d, %d, %d, %d, %d, %d, %d\n", KT, KN, *IQCglo, *IQCdir, Il, Ir, Jl, Jr, KTmax, KNmax);
          SQC_2C ( KT, KN, IQCglo, IQCdir, Il, Ir, Jl, Jr, KTmax, KNmax );

/* if 3 components were not valid, exit. */

#if 0
//        if (MEMDEBUG) cout << "\n        sC " << coreleft() << " " << farcoreleft();
#endif
          if ( *IQCdif != 3 ) {
            fprintf(stderr, "Return 13: %d\n", retval);
            return retval;
        }

          /*
           * If the 2-parameter test returned a flag of greater than 5%,
           * all flags should be 9.  Otherwise, retain the 3's.  Then exit.
           */

          if ( *IQCglo > 21 ) {
               *IQCglo = 9;
               *IQCdir = 9;
               *IQCdif = 9;
          }
          else {
               *IQCglo = 3;
               *IQCdir = 3;
          }
          fprintf(stderr, "Return 14: %d\n", retval);
          return retval;
     }

     /* If IQCGLO is 1, then test KT/KD.  Otherwise, test KN/KD. */

     fprintf(stderr, "KNmax: %d ", KNmax);
     fprintf(stderr, "KTmax: %d\n", KTmax);
     fprintf(stderr, "2C test in: glo, dir, dif: %d, %d, %d\n", *IQCglo, *IQCdir, *IQCdif);


     if ( *IQCglo == 1 ) {
          fprintf(stderr, "IQCglo == 1 branch\n");
          int KN2 = KT - KD;
          fprintf(stderr, "%.2f, %d, %d, %d, %d, %d, %d, %d, %d, %d\n", KT, KN2, *IQCdif, *IQCdir, Il, Ir, Jl, Jr, KTmax, KNmax);
          SQC_2C ( KT, KN2, IQCglo, IQCdif, Il, Ir, Jl, Jr, KTmax, KNmax );
     }
     else {
          fprintf(stderr, "IQCglo != 1 branch\n");
          int KT2 = KN + KD;
          fprintf(stderr, "%d, %.2f, %d, %d, %d, %d, %d, %d, %d, %d\n", KT2, KN, *IQCdif, *IQCdir, Il, Ir, Jl, Jr, KTmax, KNmax);
          SQC_2C ( KT2, KN, IQCdif, IQCdir, Il, Ir, Jl, Jr, KTmax, KNmax );
          *IQCdif = *IQCdir;
     }

    //  int Itime, ly;
    //  double XT, XN, XD;
    //  double ETR, ETRN, Sunup, Fraction, airMass;
    //  int Minnow, Ihrnow, Idynow, Monnow, Iyrnow;
    //  double Solznow, ETRnow, ETRNnow;
    //  int Ires, Intbin;
    //  int Il, Jl, Ir, Jr;
    //  double  XDmax, XNmax, XTmax;
    //  int Numpar, KNmax, KTmax, I;
    //  int retval = 0;
    // int NAM = 0;
    // double Solzen = 100.0;
    // double KT = -999, KN = -999, KD = -999;
    // char lastSite[50];
    // int lastMonth;
    // int KTend[4], KNend;
    // int LeftS[3] = {0, 0, 0};
    // int LeftP[3] = {0, 0, 0};
    // int IrightS[3] = {0, 0, 0};
    // int IrightP[3][4] = {{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}};
    // double Xlat=0, Xlon=0, Tzone=0;

     return (0);
        /* Leave SERI_QC1. */
}



  /*
   * Performs 2-component checking for SERI_QC1.
   * The position of KT and KN is evaluated against the selected Gompertz
   * curves and the flags IQCglo and IQCdir are evaluated.
   *
   */

  /*
   * Il, Ir, Jl, and Jr are read from the S_<Site>.QC0 file by SERI_QC1.
   * SERI_QC1 explains the meanings of the quality control flags.
   */

int SQC_2C (
     int Kt2,                 /* The value of Kt (integer %) */
     int Kn2,                 /* The value of Kn (integer %) */
     int *IQCt2,              /* The GLOBAL quality control flag */
     int *IQCn2,              /* The DIRECT quality control flag */
     int Il,                  /* The number of the left shape of the Gompertz curve */
     int Ir,                  /* The number of the right shape of the Gompertz curve */
     int Jl,                  /* The position number of the left Gompertz curve */
     int Jr,                  /* The position number of the right Gompertz curve */
     int KTmax,               /* The maximum allowable Kt (integer %) */
     int KNmax                /* The maximum allowable Kn (integer %) */
)
{

/*
 * The Gompertz boundaries are defined here.  The indices of
 * Curve(I,J,K) are:
 *        I := 0 if the left boundary, 1 if the right.
 *
 *        (in below discussion, subtract 1 from index)
 *        J := the curve type.  When I is 1, J spans 1 to 6;
 *             when I is 2, J spans 1 to 5.
 *        K := the value of 100 * Kn, rounded to the nearest
 *             integer.  If L < 1, L is reassigned to 1.  If
 *             K > 100, K is reassigned to 100.  This is
 *             because such values are both meaningless and
 *             troublesome for the Gompertz function.
 */


/* Assume success. */
     int IQC=0;
     int J=0;

     int Iflg=0;
     int IQClo=0;
     int IQChi=0;

     double Bot_R=0;
     double Top_R=0;
     double Off_R=0;
     double Bot_L=0;
     double Top_L=0;
     double Off_L=0;
     double XNmax=0;
     double Xn2=0;
     double Xt2=0;
     double XTmax=0;
     double Xn=0;
     double Dist=0;
     double Xt, Ydir, Dprev;

     *IQCn2 = 2;
     *IQCt2 = 2;

     /*
      * If KN is negative or greater than KNMAX, but KT lies within the
      * Gompertz bounds, we should measure the vertical distance only.
      */

     Xt2 = Kt2;
     XTmax = KTmax;
     Xn2 = Kn2;
     XNmax = KNmax;

     Off_L = 2.5 * ( Jl - 1 );
     Top_L = curveLeft[Il-1][KNmax-1] + Off_L;
     Top_L = maxX( Top_L, 0.0 );
     Top_L = minX( Top_L, XTmax );

     Bot_L = curveLeft[Il-1][1-1] + Off_L;
     Bot_L = maxX( Bot_L, 0.0 );
     Bot_L = minX( Bot_L, XTmax );

     Off_R = 2.5 * ( Jr - 1 );
     Top_R = curveRight[Ir-1][KNmax-1] + Off_R;
     Top_R = maxX( Top_R, 0.0 );
     Top_R = minX( Top_R, XTmax );

     Bot_R = curveRight[Ir-1][1-1] + Off_R;
     Bot_R = maxX( Bot_R, 0.0 );
     Bot_R = minX( Bot_R, XTmax );

     fprintf(stderr, "Top_L: %.2f, Bot_L: %.2f, Top_R: %.2f, Bot_R: %.2f,\n", Top_L, Bot_L, Top_R, Bot_R);

     if (( Xn2 > XNmax ) && ( Xt2 <= Top_R ) && ( Xt2 >= Top_L )) {
          IQC = Kn2 - KNmax;
          if ( IQC >= 3 ) {
               *IQCt2 = 4 * minX( IQC, 23 );
               *IQCn2 = *IQCt2 + 1;
          }
          return(-1);
     }
     else if (( Xn2 > XNmax ) && ( Xt2 > Top_R )) {
          IQC = sqrt( pow(Xn2-XNmax,2) + pow(Xt2-Top_R,2) );
          if ( IQC >= 3 ) {
               *IQCn2 = 4 * minX( IQC, 23 );
               *IQCt2 = *IQCn2 + 1;
          }
          return(-1);
     }
     else if (( Xn2 < 0.0 ) && ( Xt2 <= Bot_R ) && ( Xt2 >= Bot_L )) {
          IQC = -Kn2;
          if ( IQC >= 3 ) {
               *IQCn2 = 4 * minX( IQC, 23 );
               *IQCt2 = *IQCn2 + 1;
          }
          return(-1);
     }
     else if (( Xn2 < 0.0 ) && ( Xt2 < Bot_L )) {
          IQC = (int)sqrt( pow(Xn2,2) + pow(Xt2-Bot_L,2) );
          if ( IQC >= 3 ) {
               *IQCt2 = 4 * minX( IQC, 23 );
               *IQCn2 = *IQCt2 + 1;
          }
          return(-1);
     }

     /*
      * Figure out where the point on the left Gompertz curve corresponding
      * to Kn2 is.  This point is (Xt,Xn).
      */

     Xn = Xn2;
     Xn = minX( Xn, XNmax );
     Xn = maxX( Xn, 1.0 );
     J = Xn;

     Xt = curveLeft[Il-1][J-1] + Off_L;
     Xt = minX( Xt, XTmax );
     Xt = maxX( Xt, 1.0 );

/* Initialize the direction to UP and the distance to 100 (squared). */

     Ydir = 1.0;
     Dprev = 10000.0;

     /*
      * The point (Kt2,Kn2) is to the right of (Xt,Xn), as it should be.
      * If Kn2 is above KNmax, that counts as "to the left".
      */
     fprintf(stderr, "Starting - Xn2: %.2f, Xt2: %.2f\n", Xn2, Xt2);
     fprintf(stderr, "Starting - Xn: %.2f, Xt: %.2f, XNmax: %.2f\n", Xn, Xt, XNmax);
     if (( Xt <= Xt2 ) && ( Xn2 <= XNmax )) goto label3000;

     /*
      * The point is to the left of the left curve.
      * I seek the  distance (squared) (x^2 + y^2) to each point on
      * the curve and compare that to the minimum distance that I had
      * saved earlier.  I start with the point on the curve directly to
      * the right of my point and march up the curve.  As soon as the
      * distance increases (the curve moves away from my point, I reverse
      * my direction (YDIR) and move down the curve.  The closest point
      * determines the flag value.
      */

/* Loop:  find minimum distance. */

     label2000: ; /* Continue */
     Dist = pow(Xn2-Xn,2) + pow(Xt2-Xt,2);
     fprintf(stderr, "Label 2000 - Xn2: %.2f, Xn: %.2f, Xt2: %.2f, Xt: %.2f\n", Xn2, Xn, Xt2, Xt);
     fprintf(stderr, "Label 2000 - Dprev: %.2f, Dist: %.2f\n", Dprev, Dist);

     /*
      * New distance is new minimum.  Increment the value of Kn*100 (J),
      * and, if we haven't run off the map, get another curve point
      * and try again.
      */

     if ( Dist <= Dprev ) {
          Xn = Xn + Ydir;
          if (( Xn <= XNmax ) && ( Xn >= 1.0 )) {
               J = Xn;
               Xt = curveLeft[Il-1][J-1] + Off_L;
               Xt = minX( Xt, XTmax );
               Xt = maxX( Xt, 1.0 );
               Dprev = Dist;
               goto label2000;
          }
          else if ( Xn < 1.0 ) {
               Xt = XTmax;
               Dprev = Dist;
               goto label2000;
          }
     }

     /*
      * The new distance is greater than the old one.  If we were going
      * up, reverse direction and go down.  If we are not off the map,
      * get another curve point and try again.
      */

     if ( Ydir > 0 ) {
          Xn    = Xn - 1.0;
          Ydir = -1.0;
          if ( Xn >= 1.0 ) {
               J = Xn;
               Xt = curveLeft[Il-1][J-1] + Off_L;
               Xt = minX( Xt, XTmax );
               Xt = maxX( Xt, 1.0 );
               Dprev = Dist;
               goto label2000;
          }
     }

     /*
      * We have found the local minimum distance.  Convert it into a data
      * flag (take the square root, multiply by 4, etc. as in documentation).
     */

     fprintf(stderr, "Label 2000 - Xn: %.2f, Xt: %.2f\n", Xn, Xt);
     fprintf(stderr, "Label 2000 - Dprev: %.2f, Dist: %.2f\n", Dprev, Dist);

     Iflg = (int)sqrt( minX( Dprev, Dist ) );
     IQClo = 4 * minX( Iflg, 23 );
     IQChi = IQClo + 1;

     fprintf(stderr, "Label 2000 - Iflg: %d, IQClo: %d, IQChi: %d\n", Iflg, IQClo, IQChi);

/* The distance is large enough to trigger a 2-component flag. */

     if ( Iflg >= 3 ) {
          *IQCn2 = maxX( IQChi, *IQCn2 );
          *IQCt2 = maxX( IQClo, *IQCt2 );
          fprintf(stderr, "Label 2000 - IQCn2: %d, IQCt2: %d\n", *IQCn2, *IQCt2);
     }
     return(-1);    /* was exit */

     /*
      * Figure out where the point on the right Gompertz curve corresponding
      * to Kn2 is.  This point is (I,Kn2).
      */

     label3000: ; /* Continue */

     Xt = curveRight[Ir-1][J-1] + Off_R;
     Xt = minX( Xt, XTmax );
     Xt = maxX( Xt, 1.0 );

     /*
      * The point (Kt2,Kn2) is to the left of (Xt,Xn), as it should be.
      * If Kn2 is below 0, that counts as "to the right".
      */
     fprintf(stderr, "Label 3000 - Xn: %.2f, Xt: %.2f\n", Xn, Xt);
     if (( Xt >= Xt2 ) && ( Xn2 >= 0.0 )) return(-1);

     /*
      * The point is to the right of the right curve.
         * I seek the  distance (squared) (x^2 + y^2) to each point on
         * the curve and compare that to the minimum distance that I had
         * saved earlier.  I start with the point on the curve directly to
         * the left of my point and march up the curve.  As soon as the
         * distance increases (the curve moves away from my point, I reverse
         * my direction (YDIR) and move down the curve.  Closest point
         * determines the flag value.
      */

/* Loop:  find minimum distance. */

     label4000: ; /* Continue */
     Dist = pow(Xn2-Xn,2) + pow(Xt2-Xt,2);
     fprintf(stderr, "Label 4000 - Xn: %.2f, Xt: %.2f: \n", Xn, Xt);
     fprintf(stderr, "Label 4000 - Dprev: %.2f, Dist: %.2f\n", Dprev, Dist);

     /*
      * New distance is new minimum.  Increment the value of Kn*100 (J),
      * and, if we haven't run off the map, get another curve point
      * and try again.
      */

     if ( Dist <= Dprev ) {
          Xn = Xn + Ydir;
          if (( Xn <= XNmax ) && ( Xn >= 1.0 )) {
               J = Xn;
               Xt = curveRight[Ir-1][J-1] + Off_R;
               Xt = minX( Xt, XTmax );
               Xt = maxX( Xt, 1.0 );
               Dprev = Dist;
               goto label4000;
          }
          else if ( Xn < 1.0 ) {
               Xt = 0.0;
               Dprev = Dist;
               goto label4000;
          }
     }

     /*
      * The new distance is greater than the old one.  If we were going
      * up, reverse direction and go down.  If we are not off the map,
      * get another curve point and try again.
      */

     if ( Ydir > 0.0 ) {
          Xn = Xn - 1.0;
          Ydir = -1.0;
          if ( Xn >= 1.0 ) {
               J = Xn;
               Xt = curveRight[Ir-1][J-1] + Off_R;
               Xt = minX( Xt, XTmax );
               Xt = maxX( Xt, 1.0 );
               Dprev = Dist;
               goto label4000;
          }
     }

     /*
      * We have found the local minimum distance.  Convert it into a data
      * flag (take the square root, multiply by 4, etc. as in documentation).
      */
     fprintf(stderr, "Xn: %.2f, Xt: %.2f\n", Xn, Xt);
     fprintf(stderr, "Dprev: %.2f, Dist: %.2f\n", Dprev, Dist);

     Iflg = (int)sqrt( minX( Dprev, Dist ) );
     IQClo = 4 * minX( Iflg, 23 );
     IQChi = IQClo + 1;

     fprintf(stderr, "Iflg: %d, IQClo: %d, IQChi: %d\n", Iflg, IQClo, IQChi);

/* The distance is large enough to trigger a 2-component flag. */

     if ( Iflg >= 3 ) {
          *IQCn2 = maxX( IQClo, *IQCn2 );
          *IQCt2 = maxX(  IQChi, *IQCt2 );
          fprintf(stderr, "IQCn2: %d, IQCt2: %d\n", *IQCn2, *IQCt2);
     }
     return (0);
}


/*
 * ======================================================================
 *   Subroutine SQC_3C (  Kt3,   Kn3,   Kd3,
 *                  ^IN^   ^IN^   ^IN^
 *    2                  IQCT3, IQCn3, IQCd3 )
 *                  ^OUT^  ^OUT^  ^OUT^
 *
 * Performs 3-component checking for SERI_QC1.
 * Deviations from the equation
 *        Kt3 = Kn3 + Kd3
 * are flagged according to the convention explained in SERI_QC1.
 */

int SQC_3C (
     int Kt3,                 /* The value of Kt (integer %) */
     int Kn3,                 /* The value of Kn (integer %) */
     int Kd3,                 /* The value of Kd (integer %) */
     int *IQCt3,              /* The GLOBAL quality control flag */
     int *IQCn3,              /* The DIRECT quality control flag */
     int *IQCd3               /* The DIFUSE quality control flag */
)

{
        int IQC, Itog, IQC0, IQC1;

/* Assume success. */

     *IQCd3 = 3;
     *IQCn3 = 3;
     *IQCt3 = 3;

/* IQC = absolute % difference, Itog = "toggle" = direction failed, +/- 1 */

     IQC = Kn3 + Kd3 - Kt3;

     Itog = 1;
     if ( IQC < 0 ) {
          Itog = -1;
          IQC = -IQC;
     }

     IQC0 = 4 * minX( IQC, 23 ) - 1 ;
     if ( Itog == 1 ) IQC0 = IQC0 - 1;

/* IQC1 has to take on the opposite sense (TOO HIGH/TOO LOW) from IQC0. */

     IQC1 = IQC0 + Itog;

     /*
      * The deviation (IQC) is significant enough to be flagged.
      * IQCt3, being on the left side of the equation, gets flagged
      * in a different direction from the other two.
      */

     if ( IQC >= 3 ) {
          *IQCt3 = IQC0;
          *IQCn3 = IQC1;
          *IQCd3 = IQC1;
     }
     return(0);
}

/*
 * return error message based on bitwise-OR of seri_qc error codes defined in
 * seri_qc.h
 */
void seri_qc_decode(int code)
{
  if ( code & (1 << E_SITE) )
    fprintf(stderr, "SQC-decode ==> Site not found\n");
  if ( code & (1 << E_MONTH) )
    fprintf(stderr, "SQC-decode ==> Invalid month\n");
  if ( code & (1 << E_DAY) )
    fprintf(stderr, "SQC-decode ==> Invalid day\n");
  if ( code & (1 << E_HOUR) )
    fprintf(stderr, "SQC-decode ==> Invalid hour\n");
  if ( code & (1 << E_MINUTE) )
    fprintf(stderr, "SQC-decode ==> Invalid minute\n");
  if ( code & (1 << E_TIME) )
    fprintf(stderr, "SQC-decode ==> Invalid time\n");
  if ( code & (1 << E_INTERVAL) )
    fprintf(stderr, "SQC-decode ==> Invalid interval\n");
  if ( code & (1 << E_QC0_FILE) )
    fprintf(stderr, "SQC-decode ==> Cannot open QC-ZERO file\n");
  if ( code & (1 << E_QC0_FORMAT) )
    fprintf(stderr, "SQC-decode ==> Incorrect QC-ZERO file format\n");
  if ( code & (1 << E_R_BOUND) )
    fprintf(stderr, "SQC-decode ==> Right Gompertz boundary undefined\n");
  if ( code & (1 << E_L_BOUND) )
    fprintf(stderr, "SQC-decode ==> Left Gompertz boundary undefined\n");
  if ( code & (1 << E_KT_MAX) )
    fprintf(stderr, "SQC-decode ==> Kt max undefined\n");
  if ( code & (1 << E_KN_MAX) )
    fprintf(stderr, "SQC-decode ==> Kn max undefined\n");
  return;
}
