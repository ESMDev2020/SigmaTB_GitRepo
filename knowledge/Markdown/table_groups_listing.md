# Database Tables by Functional Group

This document organizes all database tables into functional groups based on their naming conventions and table functions. The list includes 150 tables categorized by business function.

## Table of Contents

1. [Accounts Payable (AP)](#accounts-payable)
2. [Accounts Receivable (AR)](#accounts-receivable)
3. [General Ledger (GL)](#general-ledger)
4. [Inventory Items (ITEM)](#inventory-items)
5. [Material Processing (MP)](#material-processing)
6. [Customer Management (CUST)](#customer-management)
7. [Vendor Management (VEND)](#vendor-management)
8. [Warehouse (WH)](#warehouse)
9. [Credit Management (CR)](#credit-management)
10. [Order Entry (OE)](#order-entry)
11. [Human Resources (EMP)](#human-resources)
12. [EDI Codes (EDIC)](#edi-codes)
13. [Additional Charges (ADDC)](#additional-charges)
14. [User Defined Data (UDFD)](#user-defined-data)
15. [Cutting Codes (CUTT)](#cutting-codes)
16. [Image Storage (IMAG)](#image-storage)
17. [Price Matrix (PMAT)](#price-matrix)
18. [Purchase Orders (POHE)](#purchase-orders)
19. [Sales (SALES)](#sales)
20. [Inventory Tags (TAG)](#inventory-tags)
21. [Other Tables](#other-tables)

## Accounts Payable {#accounts-payable}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| APBANKCD | AP | | Bank Disbursement Master |
| APCHKR | AP | | A/P Check Reconcilement file |
| APDEBH | AP | | A/P Debit Header File |
| APEDITR | AP | | A/P EDI transaction selection |
| APHCOD | AP | | A/P Handling Code File |
| APINVC | AP | | A/P Invoice Control File |
| APPROFL | AP | | A/P Profile |
| APVHEXC | APV | HEXC | A/P Vendor History Exchange File |
| APVOHST | APV | OHST | A/P Voucher History File |
| APVEND | APV | END | A/P Vendor Master File |
| APVNDHST | APV | NDHST | A/P Vendor History File |
| APWK856 | AP | WK | A/P Check Register Work File |

## Accounts Receivable {#accounts-receivable}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| ARCHEXC | AR | CHEXC | AR/Customer History Exchange File |
| ARCUSHST | ARCU | SHST | Customer Master History File |
| ARCUST | ARCU | ST | Customer Master File |
| ARCUST_B4 | ARCU | ST_B4 | Customer Master File |
| ARDELINQ | AR | DELINQ | Delinquent Accounts File |
| ARINFO | AR | INFO | Customer A/R Information |
| ARLOCK | AR | LOCK | A/R Lockbox Codes |
| ARDCNTP | AR | DCNTP | Discount Penalties |
| FCXREF | FC | XREF | Freight Carrier Cross Reference |
| CONTCODE | CONT | CODE | A/R Customer Contact Code |

## General Ledger {#general-ledger}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| GLACCT | GL | ACCT | Chart of Accounts |
| GLJRBA | GL | JRBA | G/L Journal Batch Header |
| GLMAJHD | GLMA | JHD | G/L Major Heading file |
| GLMAST | GLMA | ST | General Ledger Master File |

## Inventory Items {#inventory-items}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| ITEMCLSD | ITEM | CLSD | District Class File |
| ITEMBG | ITEM | BG | Item Master File |
| ITEMMAST | ITEM | MAST | Item Master File |
| ITEMCLS3 | ITEM | CLS3 | 3 Position Class Description File |
| ITEMCLS6 | ITEM | CLS6 | 6 Position Class Description File |
| ITEMCLS9 | ITEM | CLS9 | 9 Position Class Description File |
| ITEMHEAP | ITEM | HEAP | Finished Heat Item File |
| ITEMHEAT | ITEM | HEAT | Heat Number File |
| ITEMONHD | ITEM | ONHD | Item On Hand File |
| ITEMPCS | ITEM | PCS | Item Master Pieces File |
| ITEMPK | ITEM | PK | Item Packaging File |
| ITEMSHIP | ITEM | SHIP | Item In-Transit |
| ITEMVEND | ITEM | VEND | Item Vendor File |
| INVMAST | INV | MAST | Inventory Master File |
| ENDUSER | END | USER | End User File |
| UNKNOWN | UNK | NOWN | Unknown Item File |
| USET1 | US | ET1 | User Type 1 |

## Material Processing {#material-processing}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| MPDETAIL | MP | DETAIL | Material Processing Detail |
| MPHDRORD | MP | HDRORD | Material Processing Header Order |
| MPPROF | MP | PROF | Material Processing Profile |
| MPSEQWRK | MP | SEQWRK | Material Processing Sequence Work |
| MPSAWCAL | MP | SAWCAL | Saw Calculation File |
| MPHISTCH | MP | HISTCH | Material Processing History Changes |

## Customer Management {#customer-management}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| CUSTADD | CUST | ADD | Customer Master Add Code File |
| CUSTPARN | CUST | PARN | Customer Parent File |
| CUSINFO | CUS | INFO | Customer Information |
| CUSINSP | CUS | INSP | Customer Inspection |
| CUSPR | CUS | PR | Customer Price Class |
| SHIPINFO | SHIP | INFO | Customer Shipping Information |
| MWARCUST | MWAR | CUST | Customer Master File |
| WEBCUST | WEB | CUST | E/C Customer |
| WFOED | WF | OED | Web Order Entry Detail |
| PART1 | PART | 1 | Part Number Translation File |

## Vendor Management {#vendor-management}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| ACHINFO | ACH | INFO | Vendor ACH Bank Info |
| APVEND | APV | END | A/P Vendor Master File |
| VENDQUAL | VEND | QUAL | Vendor Quality Approval File |
| VENDREMT | VEND | REMT | Vendor Remit To Address File |

## Warehouse {#warehouse}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| WHSE | WH | SE | Warehouse Code File |
| WHPOTRC | WH | POTRC | Purchase Order Tracking |
| WHMPTRC | WH | MPTRC | Material Process Tracking Charges |

## Credit Management {#credit-management}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| CRAPPLY | CRAP | PLY | Credit Memo Apply File |
| CRHEADER | CRHE | ADER | Credit Memo Header File |
| OECRCMF | OECR | CMF | Credit Profile |

## Order Entry {#order-entry}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| OEOP | OE | OP | Order Entry Options |
| OEPROF | OE | PROF | Order Entry Profile |
| OECRCMF | OE | CRCMF | Credit Profile |
| MPMISC | MP | MISC | Miscellaneous Order |
| WFOED | WF | OED | Web Order Entry Detail |

## Human Resources {#human-resources}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| EMFOHST | EMF | OHST | Employee File History |
| EMPLOYEE | EMP | LOYEE | Employee File |
| EMPPARMS | EMP | PARMS | Employee Parameters |
| EMPQUOTE | EMP | QUOTE | Employee Quote File |
| EMPVAU | EMP | VAU | Employee Vacation |

## EDI Codes {#edi-codes}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| EDICD2 | EDIC | D2 | EDI 2 position codes |
| EDICD3 | EDIC | D3 | EDI 3 position codes |
| EDICD2A | EDIC | D2A | EDI 2A position codes |
| EDITTYPE | EDIT | TYPE | Edit Type Table |

## Additional Charges {#additional-charges}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| ADDCFTAX | ADDC | FTAX | Additional Charge Federal Tax File |
| ADDCHRG | ADDC | HRG | Additional Charge Code File |
| ADDCPTAX | ADDC | PTAX | Additional Charge Provincial Tax File |

## User Defined Data {#user-defined-data}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| UDFDATAL | UDFD | ATAL | User Defined Data - Validation List |
| UDFDATAT | UDFD | ATAT | User Defined Data - Data Type Definition |
| UDFDATAV | UDFD | ATAV | User Defined Data - Data Values |

## Cutting Codes {#cutting-codes}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| CUTTHEAD | CUTT | HEAD | Cutting Code Header File |
| CUTTOLD | CUTT | OLD | District - Cutting Code Tolerances |

## Image Storage {#image-storage}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| IMAGEPDF | IMAG | EPDF | Image PDF |
| IMAGEPDFB4 | IMAG | EPDFB4 | Image PDF |

## Price Matrix {#price-matrix}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| PMATRX | PM | ATRX | Price Matrix File |
| PMATRX_B4 | PM | ATRX_B4 | Price Matrix File |

## Purchase Orders {#purchase-orders}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| POHEADER | POHE | ADER | Purchase Order Header File |
| POHEADERBH | POHE | ADERBH | Purchase Order Header File |

## Sales {#sales}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| SALESMAN | SALES | MAN | Salesperson Master File |

## Inventory Tags {#inventory-tags}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| TAGBUILD | TAG | BUILD | Tag Building File |

## Other Tables {#other-tables}

| Table Code | Prefix | Suffix | Table Name |
|------------|--------|--------|------------|
| $DSPFDA | | | Output file for DSPFD TYPE(*MBRLIST) |
| BCCHKHST | BC | CHKHST | Bank Check History |
| BOOKNUM | BOOK | NUM | Book Number File |
| BUYER | BUYER | | Buyer Master File |
| CHEMTAGM | CHEM | TAGM | Chemical Analysis |
| COUNTRY | COU | NTRY | Country File |
| CRANFILE | CRAN | FILE | Crane File |
| CMMAST | CM | MAST | CM Master |
| CMMITEMF | CM | MITEMF | CM Item File |
| CURRCODE | CURR | CODE | Currency Code |
| COLCODES | COL | CODES | Collector Codes |
| DELVTERM | DEL | VTERM | Delivery Terms |
| DISTBILL | DIST | BILL | Distribution Billing |
| DUTYFILE | DUTY | FILE | Duty File |
| EMAIL | EMAIL | | Email |
| FASTPKEY | FAST | PKEY | Fast Path Keys |
| FCPARAMP | FCP | ARAMP | FC Parameter File |
| FRECONCL | FREC | ONCL | Freight Reconciliation File |
| FRTHITEM | FRTH | ITEM | Freight Item |
| IATRANS | IAT | RANS | IATRANS - Inventory Adj Transactions |
| IC | IC | | Intercompany Parameter File |
| IRECONCL | IREC | ONCL | Inventory Reconciliation File |
| LINECMNT | LINE | CMNT | Line Comment |
| MACH | MACH | | Machine Code |
| MNFEXPN | MNF | EXPN | Manufacturing Expense File |
| MASSPST | MASS | PST | Mass Post Parameter File |
| MAJRPT | MAJ | RPT | Major Reports File |
| MINRPTS | MIN | RPTS | Minor Reports Description |
| MRTRANS | MRT | RANS | Material Rejection Transaction File |
| METACODE | META | CODE | Meta Codes |
| MSWORD | MS | WORD | Word Interface Tables |
| PHYSTAGM | PHYS | TAGM | Physical Analysis File |
| PICKSLIP | PICK | SLIP | Pick Slip Profile |
| PORTNTRY | PORT | NTRY | Port of Entry File |
| POSTCALC | POST | CALC | Post Calculation Parameters |
| PRTRMK | PRT | RMK | Print Remarks |
| PURCHORD | PURC | HORD | Purchase Order Parameters |
| POCOMM | POC | OMM | Purchase Order Commodity |
| RISKCAT | RISK | CAT | Risk Category File |
| SAGPROF | SAG | PROF | Sales Agent Profile |
| SADAPARM | SADA | PARM | Sales Analysis Data Analysis Parameters |
| SICODE | SI | CODE | Standard Industry Code File |
| SURFMAST | SURF | MAST | Surface Master |
| SYSCNTL | SYS | CNTL | System Control File |
| TRKORD | TRK | ORD | Track Order |
| UPINMST | UPIN | MST | UPC/IN |
| UPLOGSEC | UPLO | GSEC | Upload Log Security |
| X820OAH | X820 | OAH | outbound 820 ach header |
| X820OAB | X820 | OAB | outbound 820 ach vendor |
| WFINDCOD | WFIN | DCOD | WF Industry Codes |
