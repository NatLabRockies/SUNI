/*
 * File seri_qc.h Version 1.1
 * header file for seri_qc.c
 */

#ifndef __SERI_QC_H
#define __SERI_QC_H

/*
 * Enumerate the error codes.  The intent is to define a number of error
 * condtions and encode them in the SERI QC return code.  Each condition
 * is represented by one bit in the integer return code (could be 16 bits or
 * 32 bits depending on the platform).  When an error condition is
 * encountered, the appropriate bit is set.  Multiple bits may be set if
 * more than one error condition is encountered.  After the call to SERI QC,
 * the calling program should examine the return code; if it is zero (no
 * bits set), the other return parameters are considered valid.  If the
 * return code is non-zero, it can be decoded bit by bit to find out what
 * condition caused the function to terminate. The seri_qc_decode() function
 * does this and can also be a template for a more sophisticated decoder.
 *
 *         Code        Bit        Parameter           Range or Error
 *    ===============  ===   ==================     ==================   */
enum {E_SITE,       /*  0    Site name              missing              */
      E_MONTH,      /*  1    Month                  1 - 12               */
      E_DAY,        /*  2    Day                    1 - 31               */
      E_HOUR,       /*  3    Hour                   0 - 24               */
      E_MINUTE,     /*  4    Minute                 0 - 59               */
      E_TIME,       /*  5    Composite Time         00:00:00 - 24:00:00  */
      E_INTERVAL,   /*  6    Interval               1 - 60               */
      E_QC0_FILE,   /*  7    QC-ZERO file           missing              */
      E_QC0_FORMAT, /*  8    QC-ZERO format         file format corrupt  */
      E_R_BOUND,    /*  9    QC-ZERO right boundary boundary undefined   */
      E_L_BOUND,    /* 10    QC-ZERO left boundary  boundary undefined   */
      E_KT_MAX,     /* 11    QC-ZERO Kt max         boundary undefined   */
      E_KN_MAX};    /* 12    QC-ZERO Kn max         boundary undefined   */

__declspec( dllexport )  int seri_qc1 (
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
);

__declspec( dllexport ) int SQC_2C (
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
);

__declspec( dllexport ) int SQC_3C (
     int Kt3,                 /* The value of Kt (integer %) */
     int Kn3,                 /* The value of Kn (integer %) */
     int Kd3,                 /* The value of Kd (integer %) */
     int *IQCt3,              /* The GLOBAL quality control flag */
     int *IQCn3,              /* The DIRECT quality control flag */
     int *IQCd3               /* The DIFUSE quality control flag */
);

__declspec( dllexport )  void seri_qc_decode(int code);

#endif














