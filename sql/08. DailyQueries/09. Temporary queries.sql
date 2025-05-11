SELECT TOP (100) 
IOITEM,
IOQOH,
IOQOO,
IOACST,
IOBPRC
FROM [SigmaTB].[dbo].[ITEMONHD]

UNION ALL

SELECT 
	'Total' AS IOITEM,
	null as IOQOH,
	null as IOQOO,
	null as IOACST,
	CAST(COUNT(*) AS VARCHAR(10)) AS IOBPRC
FROM [SigmaTB].[dbo].[ITEMONHD];


select   top 10
from ITEMHIST
where IHITEM = '50002'

select   top 10 *
from ITEMMAST

select   top 30 *
from MPDETAIL

select   top 30 *
from oedetail

select top 30 * from OEOPNORD;
select top 30 * from PODETAIL;
select top 30 * from itemtag;

select top 30 * from  ARCUST

select top 30 * from  APVEND

select top 30 * from  ITEMHIST

select top 30 * from  ITEMONHD

select top 30 * from OEOPNORD


/****************************************************************************************/
--review... sales totals by customer
/****************************************************************************************/

SELECT
	SUM(CASE WHEN GLA.GARP3 = 500 THEN GLAMT ELSE 0 END) AS TotalSales,
	SUM(CASE WHEN GLA.GARP3 = 530 THEN GLAMT ELSE 0 END) AS ReturnAllow,
	SUM(CASE WHEN GLA.GARP3 = 600 THEN GLAMT ELSE 0 END) AS COGs_Material,
	SUM(CASE WHEN GLA.GARP3 = 610 THEN GLAMT ELSE 0 END) AS COGs_Freight
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE GLREF LIKE '%965835%'
  AND GLA.GARP3 IN (500, 530, 600, 610)
  AND GLTRN# <> '0'
  AND GLAMT <> 0


SELECT
	GLTRN# AS GLTRN#TransNum,
	GLDESC AS Title_GLDESC,
	GLCUST AS GLCUST_ID,
	SUM(CASE WHEN GLA.GARP3 = 500 THEN GLAMT ELSE 0 END) AS TotalSales,
	SUM(CASE WHEN GLA.GARP3 = 530 THEN GLAMT ELSE 0 END) AS ReturnAllow,
	SUM(CASE WHEN GLA.GARP3 = 600 THEN GLAMT ELSE 0 END) AS COGs_Material,
	SUM(CASE WHEN GLA.GARP3 = 610 THEN GLAMT ELSE 0 END) AS COGs_Freight
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE  GLT.GLPYY = 25     AND GLT.GLPMM = 2  AND GLTRN#<>'0'
  AND GLA.GARP3 IN (500, 530, 600, 610)
  GROUP BY GLTRN#, GLDESC, GLCUST;


  /*SELECT 
	ARCUST.CALPHA AS CustomerName,
	COUNT(DISTINCT GLT.GLTRN#) AS OrderCount,
	SUM(GLT.GLAMT) AS TotalCredits
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA 
	ON GLT.GLACCT = GLA.GACCT
LEFT JOIN ARCUST 
	ON GLT.GLCUST = ARCUST.CCUST
WHERE 
	GLT.GLAPPL IN ('CR') 
	AND GLA.GARP3 IN (500, 600) 
	AND GLT.GLPYY = 25 
	AND GLT.GLPMM = 2
GROUP BY 
	ARCUST.CALPHA
ORDER BY 
	TotalCredits DESC;*/

--I want to know what customer and what salesman does the most credits. 
--BAD QUERY
/*SELECT 
	SM.SMNAME AS SalesmanName,
	SUM(GLT.GLAMT) AS TotalCredits
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA 
	ON GLT.GLACCT = GLA.GACCT
LEFT JOIN ARCUST 
	ON GLT.GLCUST = ARCUST.CCUST
LEFT JOIN SALESMAN SM 
	ON ARCUST.CDIST = SM.SMDIST
WHERE 
	GLT.GLAPPL = 'CR' 
	AND GLA.GARP3 IN (500, 600)
	AND GLT.GLPYY = 25 
	AND GLT.GLPMM = 2
GROUP BY 
	SM.SMNAME
ORDER BY 
	TotalCredits DESC;*/


-------------------------------------------
-- Same query but with totals
/*
	SELECT 
		OEDETAIL.ODDIST * 1000000 + OEDETAIL.ODORDR AS OrderID,
		SALESMAN.SMNAME AS SalesmanName,
		OEOPNORD.OOTYPE AS OrderType,
		OEOPNORD.OOCDIS * 100000 + OEOPNORD.OOCUST AS DistributorCustomer,
		ARCUST.CALPHA AS CustomerName,
		OEOPNORD.OOICC * 1000000 + OEOPNORD.OOIYY * 10000 + OEOPNORD.OOIMM * 100 + OEOPNORD.OOIDD AS OrderDateKey,
		OEDETAIL.ODITEM,
		OEDETAIL.ODSIZ1,        
		OEDETAIL.ODSIZ2,        
		OEDETAIL.ODSIZ3,        
		OEDETAIL.ODCRTD AS [Size],
		SLSDSCOV.DXDSC2 AS [Specification],
		OEDETAIL.ODTFTS AS Feet,
		OEDETAIL.ODTLBS AS Pounds,
		OEDETAIL.ODTPCS AS Pieces,
		OEDETAIL.ODSLSX AS TotalSales,
		OEDETAIL.ODFRTS AS FreightCharges,
		OEDETAIL.ODCSTX AS MaterialCost,
		OEDETAIL.ODPRCC AS ProcessingCost,
		OEDETAIL.ODADCC AS AdditionalCharges,
		OEDETAIL.ODWCCS AS WeightCost,
		ARCUST.CSTAT AS CustomerState,
		ARCUST.CCTRY AS CustomerCountry
	FROM 
		ARCUST
	INNER JOIN OEOPNORD ON
		OEOPNORD.OOCDIS = ARCUST.CDIST AND
		OEOPNORD.OOCUST = ARCUST.CCUST
	INNER JOIN SALESMAN ON 
		OEOPNORD.OOISMD = SALESMAN.SMDIST AND 
		OEOPNORD.OOISMN = SALESMAN.SMSMAN
	INNER JOIN OEDETAIL ON 
		OEDETAIL.ODDIST = OEOPNORD.OODIST AND 
		OEDETAIL.ODORDR = OEOPNORD.OOORDR
	INNER JOIN SLSDSCOV ON 
		OEDETAIL.ODDIST = SLSDSCOV.DXDIST AND 
		OEDETAIL.ODORDR = SLSDSCOV.DXORDR AND 
		OEDETAIL.ODMLIN = SLSDSCOV.DXMLIN
	WHERE 
		OEOPNORD.OOIYY = 25 AND OEOPNORD.OOIMM = 2

	UNION ALL

	SELECT 
		NULL AS OrderID,
		'🧮 TOTAL' AS SalesmanName,
		NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
		NULL,
		SUM(OEDETAIL.ODTFTS),
		SUM(OEDETAIL.ODTLBS),
		SUM(OEDETAIL.ODTPCS),
		SUM(OEDETAIL.ODSLSX),
		SUM(OEDETAIL.ODFRTS),
		SUM(OEDETAIL.ODCSTX),
		SUM(OEDETAIL.ODPRCC),
		SUM(OEDETAIL.ODADCC),
		SUM(OEDETAIL.ODWCCS),
		NULL, NULL
	FROM 
		ARCUST
	INNER JOIN OEOPNORD ON
		OEOPNORD.OOCDIS = ARCUST.CDIST AND
		OEOPNORD.OOCUST = ARCUST.CCUST
	INNER JOIN SALESMAN ON 
		OEOPNORD.OOISMD = SALESMAN.SMDIST AND 
		OEOPNORD.OOISMN = SALESMAN.SMSMAN
	INNER JOIN OEDETAIL ON 
		OEDETAIL.ODDIST = OEOPNORD.OODIST AND 
		OEDETAIL.ODORDR = OEOPNORD.OOORDR
	INNER JOIN SLSDSCOV ON 
		OEDETAIL.ODDIST = SLSDSCOV.DXDIST AND 
		OEDETAIL.ODORDR = SLSDSCOV.DXORDR AND 
		OEDETAIL.ODMLIN = SLSDSCOV.DXMLIN
	WHERE 
		OEOPNORD.OOIYY = 25 AND OEOPNORD.OOIMM = 2

	ORDER BY SalesmanName, OrderID;  */



-----------------------------------------------

select TOP 100 * -- (GLT.[GLAMT])
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE [GLPYY] = 25 AND [GLPMM]=2 AND   GLA.GARP3 IN (600, 610) 


AND GLT.GLAPPL in ('CR', 'IN')

--Table structure
select top 1 *
from GLTRANS GLT
LEFT JOIN GLACCT GLA 
	ON GLT.GLACCT = GLA.GACCT
WHERE GLT.GLAPPL in ('CR') AND GLA.GARP3 IN (500, 600) and [GLPYY] = 25 AND [GLPMM]=2

--Group reason (Write off). 
select [GLCUST], gldesc, SUM(GLT.[GLAMT])
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE GLT.GLAPPL in ('CR') AND GLA.GARP3 IN (500, 600) and [GLPYY] = 25 AND [GLPMM]=2
GROUP BY [GLCUST], GLDESC;            --Group by customer


-- AUDIT COGS
SELECT
	GLREF,
	GLDESC,
	GLA.GACCT,
	GLA.GACDES,
	GLAMT,
	GLCRDB,
	GLPGM,
	GLAPPL,
	GLBTCH,
	GLUSER,
	*
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE 
	GLA.GARP3 IN (600, 610)
	AND GLTRN# <> '0'
	AND GLAMT <> 0
	AND GLPYY = 25
	AND GLPMM = 2
ORDER BY GLT.GLREF;






--AUDIT THE BUYOUT
SELECT 
	GLTRN#,
	GLDESC,
	GLREF,
	GLT.GLACCT,
	GLA.GARP3,
	GLA.GACDES,
	GLAMT
FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
WHERE GLA.GARP3 = 600
  AND GLA.GACDES LIKE '%BUYOUT%'
  AND GLT.GLPYY = 25
  AND GLT.GLPMM = 2
ORDER BY GLTRN#;


--Lets confirm if we have the index working
SELECT TOP 20 GLREF, GLREF_REV FROM GLTRANS
WHERE GLREF IS NOT NULL AND GLREF_REV IS NULL;

--Diagnose
SELECT TOP 20 GLREF, GLREF_REV 
FROM GLTRANS 
WHERE GLREF_REV LIKE '%34969%'  -- reverse of 965943

--Lets check the standardized version
SELECT *
FROM GLTRANS
WHERE GLREF_REV = REVERSE('0E01896943–0001')


--Lets try the performance
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT *
FROM GLTRANS
WHERE GLREF_REV = REVERSE('965943')

--QUERY USING THE FAST INDEXES
USE SigmaTB;

DECLARE @RefFilter VARCHAR(15);
SET @RefFilter = '965943';  -- without %!

SELECT
	-- Desc, ref
	GLDESC AS Title_GLDESC, 
	GLAMT,
	GLA.GARP3 as GARP3_FS,      
	GLAPPL AS GLAPPL_APP,       

	-- Account description from GLACCT
	GLA.GACDES AS GACDES_AccountDescription,
   
	FORMAT(GLCOMP, '00') + ' ' + FORMAT(GLDIST, '00') + ' ' + FORMAT(GLCSTC, '00') AS [CO DS CS],
	GLT.GLACCT AS GLAccount_GLACCT,

	GLREF AS GLREF_Reference,
	GLAPPL + RIGHT('00000000' + CAST(GLBTCH AS VARCHAR), 8) + '-0001' AS Reference,

	FORMAT(GLPPYY, '00') + ' ' + FORMAT(GLPERD, '00') AS Period,

	GLDESC AS Transaction_GLDESC,
	GLPGM AS GLPGM_Prgm,
	GLUSER AS GLUSER,
	GLAPTR AS GLAPTR_Related,
	GLTRN# AS [GLTRN#],
	GLTRNT AS [GLTRNT_Tran],
	GLTYPE AS GLTYPE,
	GLDIST AS GLDIST,
	GLREF AS GLREF_Document,
	GLCRDB,
	GLT.GLACCT AS GLACCT_FS,
	GLRECD AS Ext,

	TRY_CAST(
		CAST(GLRFYY AS VARCHAR(4)) + '-' + 
		RIGHT('00' + CAST(GLRFMM AS VARCHAR(2)), 2) + '-' + 
		RIGHT('00' + CAST(GLRFDD AS VARCHAR(2)), 2) 
	AS DATE) AS Posting,

	NULL AS System,
	FORMAT(GLCUST, '00 00000') AS Custmr

FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT




-- ✅ Optimized filtering using index on GLREF_REV
WHERE GLREF_REV LIKE REVERSE(@RefFilter) + '%' 
  AND GLA.GARP3 IN (500, 600)

GROUP BY
	GLRECD, GLCOMP, GLDIST, GLCSTC, GLT.GLACCT, GLDESC, GLPPYY, GLPERD, GLAPPL, GLBTCH, GLPGM,
	GLUSER, GLAPTR, GLTRN#, GLTRNT, GLTYPE, GLREF, GLRFYY, GLRFMM, GLRFDD, GLCUST, GLCRDB, GLAMT,
	GLA.GACDES, GLA.GARP3

ORDER BY GLTRN#;




--we check if the index has data
SELECT TOP 10 GLREF, GLREF_REV 
FROM GLTRANS 
WHERE GLREF IS NOT NULL;



select GLREF from GLTRANS;

ALTER TABLE GLTRANS
ADD GLREF_CLEAN AS RTRIM(GLREF) PERSISTED;

CREATE INDEX IX_GLREF_CLEAN ON GLTRANS(GLREF_CLEAN);
/**********************/

SELECT TOP 100
	GLREF, 
	LEN(GLREF) AS Length,
	'[' + GLREF + ']' AS VisibleWithBrackets
FROM GLTRANS
ORDER BY LEN(GLREF) DESC;

-- We check the index
select TOP 10000 
	GLREF_REV
FROM GLTRANS

/***************/

select count(*) from gltrans


USE SigmaTB;

--try with the buyout
USE SigmaTB;

SELECT
	-- Revenue and Returns
	SUM(CASE WHEN GLA.GARP3 = 500 THEN GLAMT ELSE 0 END) AS TotalSales,
	SUM(CASE WHEN GLA.GARP3 = 530 THEN GLAMT ELSE 0 END) AS ReturnAllow,

	-- Direct COGS
	SUM(CASE WHEN GLA.GACCT = '4101100000' THEN GLAMT ELSE 0 END) AS COGS_Material,
	SUM(CASE WHEN GLA.GACCT = '4203900000' THEN GLAMT ELSE 0 END) AS COGS_Freight,

	-- Buyout components
	SUM(CASE WHEN GLA.GACCT = '4101120000' THEN GLAMT ELSE 0 END) AS COGS_Buyout,
	SUM(CASE WHEN GLA.GACCT = '4101200000' THEN GLAMT ELSE 0 END) AS COGS_PPV,

	-- Net = Buyout minus PPV (if PPV is negative, subtracting will correct it)
	SUM(CASE WHEN GLA.GACCT = '4101120000' THEN GLAMT ELSE 0 END) -
	SUM(CASE WHEN GLA.GACCT = '4101200000' THEN GLAMT ELSE 0 END) AS NetBuyoutCOGS

FROM GLTRANS GLT
LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT

WHERE GLA.GARP3 IN (500, 530, 600, 610)
  AND GLT.GLTRN# <> '0'
  AND GLAMT <> 0
  AND GLT.GLPYY = 25
  AND GLT.GLPMM = 2;

---------------------------------------------------------
USE SigmaTB;
	--Query all
  SELECT GLA.GARP3, GLT.GLCSTC, GLT.GLAPPL, GLT.[GLTRN#], GLA.GACDES, GLT.GLACCT, GLT.GLAMT, GLT.GLAMTQ, GLT.GLCRDB, GLT.GLDESC 
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
  WHERE 
		GLT.[GLTRN#]   =965943

	-- Query what I want
	-- THIS QUERY IDENTIFIES TOTAL SALES, MATERIAL SALES, PROCESSING SALES, MATERIAL COST, PROCESSING COST
  SELECT GLA.GARP3, GLT.GLCSTC, GLT.GLAPPL, GLT.[GLTRN#], GLA.GACDES, GLT.GLACCT, GLT.GLAMT, GLT.GLAMTQ, GLT.GLCRDB, GLT.GLDESC 
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
  WHERE 
		GLT.[GLTRN#]   =965943
		AND GLA.GARP3 IN (30, 50, 500, 530, 600, 610, 175)
		AND GLT.GLAPPL NOT IN ('AP', 'IU')
		ORDER BY 
		CASE GARP3
			WHEN 30 THEN 1
			WHEN 500 THEN 2
			WHEN 175 THEN 3
			WHEN 50 THEN 3
			WHEN 600 THEN 3           
			ELSE 999
		END, 
		GACDES;

/**************************************************************************
--FUNCTION TO SELECT TOTAL SALES AND COSTS PER TRANSACTION
**************************************************************************/

	WITH SelectTotalSalesCostsperTransaction as(
		SELECT 
			Metric = 
				CASE 
					WHEN GLA.GARP3 = 500 THEN 'Total Sales'
					WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
					WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
					WHEN GLA.GARP3 = 50 THEN 'Material Cost'
					WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
					ELSE 'Other'
				END,
			SUM(CASE 
					WHEN GLCRDB = 'C' THEN -GLAMT
					WHEN GLCRDB = 'D' THEN  GLAMT
					ELSE 0
				END) AS TotalAmount
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE 
			GLT.[GLTRN#] = 965943
			AND GLA.GARP3 IN (30, 50, 500, 530, 600, 610, 175)
			AND GLT.GLAPPL NOT IN ('AP', 'IU')
			AND (
				GLA.GARP3 = 500 
				OR GLA.GARP3 = 50 
				OR GLA.GARP3 = 175
				OR GLA.GACCT IN (4001100000, 4103200000, 4103300000)
			)
		GROUP BY 
			CASE 
				WHEN GLA.GARP3 = 500 THEN 'Total Sales'
				WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
				WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
				WHEN GLA.GARP3 = 50 THEN 'Material Cost'
				WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
				ELSE 'Other'
			END
		ORDER BY 
			CASE 
				WHEN 
					CASE 
						WHEN GLA.GARP3 = 500 THEN 'Total Sales'
						WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
						WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
						WHEN GLA.GARP3 = 50 THEN 'Material Cost'
						WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
						ELSE 'Other'
					END = 'Total Sales' THEN 1
				WHEN 
					CASE 
						WHEN GLA.GARP3 = 500 THEN 'Total Sales'
						WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
						WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
						WHEN GLA.GARP3 = 50 THEN 'Material Cost'
						WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
						ELSE 'Other'
					END = 'Material Sales' THEN 2
				WHEN 
					CASE 
						WHEN GLA.GARP3 = 500 THEN 'Total Sales'
						WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
						WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
						WHEN GLA.GARP3 = 50 THEN 'Material Cost'
						WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
						ELSE 'Other'
					END = 'Processing Sales' THEN 3
				WHEN 
					CASE 
						WHEN GLA.GARP3 = 500 THEN 'Total Sales'
						WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
						WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
						WHEN GLA.GARP3 = 50 THEN 'Material Cost'
						WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
						ELSE 'Other'
					END = 'Material Cost' THEN 4
				WHEN 
					CASE 
						WHEN GLA.GARP3 = 500 THEN 'Total Sales'
						WHEN GLA.GACCT = 4001100000 THEN 'Material Sales'
						WHEN GLA.GACCT = 4103200000 OR GLA.GACCT = 4103300000 THEN 'Processing Sales'
						WHEN GLA.GARP3 = 50 THEN 'Material Cost'
						WHEN GLA.GARP3 = 175 THEN 'Processing Cost'
						ELSE 'Other'
					END = 'Processing Cost' THEN 5
				ELSE 999
			END;

	)

-------------------
	-- We get the totals per transaction
	select * from SelectTotalSalesCostsperTransaction
	ORDER BY GARP3;

------------------


SELECT DISTINCT GLAPPL FROM GLTRANS;

SELECT 
	GLAPPL,
	COUNT(*) AS MyRowCount
FROM GLTRANS
WHERE 
	GLPYY = 25 
	AND GLPMM = 2
GROUP BY GLAPPL
ORDER BY MyRowCount DESC;


SELECT 
	CASE 
		WHEN GLACCT IN (4101000000, 4101100000, 4101120000, 4101200000) THEN 'Material Cost'
		WHEN GLACCT IN (2201400000, 2201000000) THEN 'Processing Cost'
		ELSE 'Other'
	END AS CostType,
	SUM(CASE 
			WHEN GLCRDB = 'C' THEN -GLAMT
			WHEN GLCRDB = 'D' THEN  GLAMT
			ELSE 0
		END) AS TotalAmount
FROM GLTRANS
WHERE GLPYY = 25 AND GLPMM = 2
AND GLTRN# = 965943
AND GLACCT IN (4101000000, 4101100000, 4101120000, 4101200000, 2201400000, 2201000000)
GROUP BY 
	CASE 
		WHEN GLACCT IN (4101000000, 4101100000, 4101120000, 4101200000) THEN 'Material Cost'
		WHEN GLACCT IN (2201400000, 2201000000) THEN 'Processing Cost'
		ELSE 'Other'
	END;

USE SIGMATB;

DELETE FROM GLTRANS;

-- Only needed if your column type blocks conversion
ALTER TABLE GLTRANS
ALTER COLUMN GLAMTQ DECIMAL(18, 2);



SELECT 
	COLUMN_NAME, 
	DATA_TYPE, 
	NUMERIC_PRECISION, 
	NUMERIC_SCALE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'GLTRANS' AND COLUMN_NAME = 'GLAMTQ';


--PROVIDES ALL SALES AND COGS. REVIEW MATERIALS
BEGIN
	SELECT
		SUM(CASE WHEN Sub.GARP3 = 500 THEN AdjustedAmount ELSE 0 END) AS TotalSales,
		SUM(CASE WHEN Sub.GARP3 = 530 THEN AdjustedAmount ELSE 0 END) AS ReturnAllow,
		SUM(CASE WHEN Sub.GARP3 = 600 THEN AdjustedAmount ELSE 0 END) AS COGs_Material,
		SUM(CASE WHEN Sub.GARP3 = 610 THEN AdjustedAmount ELSE 0 END) AS COGs_Freight
	FROM (
		SELECT 
			GLAMT * CASE 
						WHEN GLCRDB = 'C' THEN -1 
						WHEN GLCRDB = 'D' THEN 1 
						ELSE 0 
					END AS AdjustedAmount,
			GLA.GARP3
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE 
			GLA.GARP3 IN (500, 530, 600, 610)
			AND GLTRN# <> '0'
			AND GLAMT <> 0
			AND GLT.GLPYY = 25
			AND GLT.GLPMM = 2
	) AS Sub;
END

		select * from GLACCT GLA where gla.gacdes like '%COGS - PROCESSING PUR PRICE VARIANC%'
			select * from GLACCT GLA where gla.gacct = 4103600000


SELECT *
FROM OEOPNORD
WHERE OOORDR IN (334622, 335295, 221719, 51257);

SELECT *
FROM ARCUST
WHERE CCUST IN (334622, 335295, 221719, 51257);

SELECT *
FROM ITEMTAG
WHERE ITEMTAG.ITAGN LIKE ('%334622%', '%335295%', '%221719%', '%51257%');

SELECT TOP 1 * FROM GLHIST WHERE GLHISTID = 334622;



 -- lets get the 380k - TOTAL
		SELECT         
			SUM(
				CASE 
					WHEN GLCRDB = 'C' THEN -GLAMT
					WHEN GLCRDB = 'D' THEN GLAMT
					ELSE 0
				END) AS AdjustedAmount 
		 
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE GLA.GARP3 IN (500, 530, 600, 610)
		AND GLT.[GLTRN#] = 0
		AND GLT.GLPYY = 25
		AND GLT.GLPMM = 2
		ORDER BY
			GARP3

-- Lets get the 380k by GACDES
		SELECT GLA.GACDES,
			SUM(
				CASE 
					WHEN GLCRDB = 'C' THEN +GLAMT
					WHEN GLCRDB = 'D' THEN -GLAMT
					ELSE 0
				END) AS AdjustedAmount 
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE GLA.GARP3 IN (500, 530, 600, 610)
		AND GLT.[GLTRN#] = 0
		AND GLT.GLPYY = 25
		AND GLT.GLPMM = 2
		GROUP BY GLA.GACDES;
   
-- Lets get the 380k by GLDESC -- all rows
		SELECT GLT.GLDESC,
			SUM(
				CASE 
					WHEN GLCRDB = 'C' THEN +GLAMT
					WHEN GLCRDB = 'D' THEN -GLAMT
					ELSE 0
				END) AS AdjustedAmount 
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE GLA.GARP3 IN (500, 530, 600, 610)
		AND GLT.[GLTRN#] = 0
		AND GLT.GLPYY = 25
		AND GLT.GLPMM = 2
		GROUP BY GLT.GLDESC; -- ORDER BY GARP3


-- Lets get the 380k by GLDESC -- only numeric rows
	SELECT 
		LTRIM(RTRIM(GLT.GLDESC)) AS GLDESC,
		GLA.GACDES,
		SUM(
			CASE 
				WHEN GLCRDB = 'C' THEN +GLAMT
				WHEN GLCRDB = 'D' THEN -GLAMT
				ELSE 0
			END
		) AS AdjustedAmount 
	FROM 
		GLTRANS GLT
	LEFT JOIN 
		GLACCT GLA ON GLT.GLACCT = GLA.GACCT
	WHERE 
		GLA.GARP3 IN (500, 530, 600, 610)
		AND GLT.[GLTRN#] = 0
		AND GLT.GLPYY = 25
		AND GLT.GLPMM = 2
		AND LEN(LTRIM(RTRIM(GLT.GLDESC))) <> 6  -- Exclude exactly 6-character trimmed values
	GROUP BY 
		LTRIM(RTRIM(GLT.GLDESC)), GLA.GACDES;





-- no
-- Lets get the 380k by GACDES
		SELECT GLA.GACDES, 
			SUM(glt.GLAMT)
		FROM GLTRANS GLT
		LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
		WHERE GLA.GARP3 IN (500, 530, 600, 610)
		AND GLT.[GLTRN#] = 0
		AND GLT.GLPYY = 25
		AND GLT.GLPMM = 2
		GROUP BY GLA.GACDES; -- ORDER BY GARP3


USE SigmaTB;
SELECT DISTINCT(ITTDES) FROM ITEMTAG;


use sigmatb;

SELECT CASE WHEN 
	ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
	THEN CAST(REPLACE(REPLACE(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) 
	ELSE 0.0 END AS [OnPO], ISNULL(e_TagData.remnants, 0.0) as remnants, e_ROPData.[Level], 
	CASE WHEN ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
	AND CAST(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) <> 0 
	THEN CAST(REPLACE(REPLACE(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) 
	/ CAST(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) 
	ELSE NULL END AS [PO Weeks], 
	CASE WHEN ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
	AND CAST(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) <> 0 
	THEN DATEADD( WEEK, CAST( ( CASE WHEN ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[OnHand] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
	THEN CAST(REPLACE(REPLACE(CAST(e_ROPData.[OnHand] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) ELSE 0.0 
	END - CASE 
		WHEN ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[Rsrv] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
		THEN CAST(REPLACE(REPLACE(CAST(e_ROPData.[Rsrv] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) 
		ELSE 0.0 END + CASE WHEN ISNUMERIC(REPLACE(REPLACE(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)), ',', ''), ' ', '')) = 1 
		THEN CAST(REPLACE(REPLACE(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) ELSE 0.0 
		END ) / CAST(REPLACE(REPLACE(CAST(e_ROPData.[con/wk] AS VARCHAR(MAX)), ',', ''), ' ', '') AS FLOAT) AS INT), 
		GETDATE() ) ELSE NULL END AS [New Depletion Date]
				FROM e_ROPData
				LEFT JOIN e_TagData ON e_ROPData.Item = TRY_CAST(e_TagData.item AS INT) -- <<< SQL JOIN FIX IS HERE
				WHERE e_ROPData.Item = 50002;


use SigmaTB;

SELECT
	-- Handle OnPO (TEXT type) safely using TRY_CAST, default 0.0
	ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) AS [OnPO],

	-- Handle remnants (Assuming it MIGHT be text - CHECK SCHEMA). Default 0.0
	ISNULL(TRY_CAST(CAST(e_TagData.remnants AS VARCHAR(MAX)) AS FLOAT), 0.0) AS remnants,

	-- Level (NUMERIC) - select directly
	e_ROPData.[Level],

	-- PO Weeks calculation (using direct NUMERIC con/wk and safe OnPO)
	CASE
		-- Check NUMERIC con/wk directly for NULL and non-zero
		WHEN e_ROPData.[con/wk] IS NOT NULL AND e_ROPData.[con/wk] <> 0
		THEN ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) -- Safe OnPO value
			 / e_ROPData.[con/wk] -- Direct division with NUMERIC con/wk
		ELSE NULL -- Return NULL if con/wk is NULL or zero
	END AS [PO Weeks],

	-- New Depletion Date (using direct NUMERIC columns and safe OnPO)
	CASE
		-- Check NUMERIC con/wk directly for NULL and non-zero
		WHEN e_ROPData.[con/wk] IS NOT NULL AND e_ROPData.[con/wk] <> 0
		THEN DATEADD(
			WEEK,
			-- Explicitly CAST the result of the division (weeks) to INT for DATEADD
			CAST(
				( -- Calculate Total Available Inventory
					ISNULL(e_ROPData.[OnHand], 0.0) -- OnHand (NUMERIC) - Use ISNULL for safety
				  - ISNULL(e_ROPData.[Rsrv], 0.0) -- Rsrv (NUMERIC) - Use ISNULL for safety
				  + ISNULL(TRY_CAST(CAST(e_ROPData.[OnPO] AS VARCHAR(MAX)) AS FLOAT), 0.0) -- Safe OnPO value
				)
				/ e_ROPData.[con/wk] -- Direct division by NUMERIC con/wk
			AS INT), -- Cast result to INT for DATEADD
			GETDATE()
			)
		ELSE NULL -- Return NULL if con/wk is NULL or zero
	END AS [New Depletion Date]
FROM
	e_ROPData -- Item is INT
LEFT JOIN
	e_TagData -- item is INT
	ON e_ROPData.Item = e_TagData.item -- Correct JOIN (INT = INT)
WHERE
	e_ROPData.Item = 50002; -- Correct WHERE (INT = INT), use variable in Python





/*********************************************************************
************************************************************************/
USE Sigmatb;

			SELECT GLDESC AS Title_GLDESC, GLAMT, GLA.GARP3 as GARP3_FS, GLAPPL AS GLAPPL_APP,
						   GLA.GACDES AS GACDES_AccountDescription, FORMAT(GLCOMP, '00') + ' ' + FORMAT(GLDIST, '00') + ' ' + FORMAT(GLCSTC, '00') AS [CO DS CS],
						   GLT.GLACCT AS GLAccount_GLACCT, GLREF AS GLREF_Reference, GLAPPL + RIGHT('00000000' + CAST(GLBTCH AS VARCHAR), 8) + '-0001' AS Reference,
						   FORMAT(GLPPYY, '00') + ' ' + FORMAT(GLPERD, '00') AS Period, GLDESC AS Transaction_GLDESC, GLPGM AS GLPGM_Prgm,
						   GLUSER AS GLUSER, GLAPTR AS GLAPTR_Related, GLTRN# AS [GLTRN#], GLTRNT AS [GLTRNT_Tran],
						   GLTYPE AS GLTYPE, GLDIST AS GLDIST, GLREF AS GLREF_Document, GLCRDB, GLT.GLACCT AS GLACCT_FS,
						   GLRECD AS Ext, TRY_CAST(CAST(GLRFYY AS VARCHAR(4)) + '-' + RIGHT('00' + CAST(GLRFMM AS VARCHAR(2)), 2) + '-' + RIGHT('00' + CAST(GLRFDD AS VARCHAR(2)), 2) AS DATE) AS Posting,
						   NULL AS System, FORMAT(GLCUST, '00 00000') AS Custmr
					FROM GLTRANS GLT
					LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
					WHERE GLREF LIKE 965943
					  AND GLA.GARP3 IN (500,600)
					GROUP BY GLRECD, GLCOMP, GLDIST, GLCSTC, GLT.GLACCT, GLDESC, GLPPYY, GLPERD, GLAPPL, GLBTCH, GLPGM,
							 GLUSER, GLAPTR, GLTRN#, GLTRNT, GLTYPE, GLREF, GLRFYY, GLRFMM, GLRFDD, GLCUST, GLCRDB, GLAMT,
							 GLA.GACDES, GLA.GARP3
					ORDER BY GLTRN#;


USE Sigmatb;
					SELECT GLDESC AS Title_GLDESC, GLAMT, GLA.GARP3 as GARP3_FS, GLAPPL AS GLAPPL_APP,
						   GLA.GACDES AS GACDES_AccountDescription, FORMAT(GLCOMP, '00') + ' ' + FORMAT(GLDIST, '00') + ' ' + FORMAT(GLCSTC, '00') AS [CO DS CS],
						   GLT.GLACCT AS GLAccount_GLACCT, GLREF AS GLREF_Reference, GLAPPL + RIGHT('00000000' + CAST(GLBTCH AS VARCHAR), 8) + '-0001' AS Reference,
						   FORMAT(GLPPYY, '00') + ' ' + FORMAT(GLPERD, '00') AS Period, GLDESC AS Transaction_GLDESC, GLPGM AS GLPGM_Prgm,
						   GLUSER AS GLUSER, GLAPTR AS GLAPTR_Related, GLTRN# AS [GLTRN#], GLTRNT AS [GLTRNT_Tran],
						   GLTYPE AS GLTYPE, GLDIST AS GLDIST, GLREF AS GLREF_Document, GLCRDB, GLT.GLACCT AS GLACCT_FS,
						   GLRECD AS Ext, TRY_CAST(CAST(GLRFYY AS VARCHAR(4)) + '-' + RIGHT('00' + CAST(GLRFMM AS VARCHAR(2)), 2) + '-' + RIGHT('00' + CAST(GLRFDD AS VARCHAR(2)), 2) AS DATE) AS Posting,
						   NULL AS System, FORMAT(GLCUST, '00 00000') AS Custmr
					FROM GLTRANS GLT
					LEFT JOIN GLACCT GLA ON GLT.GLACCT = GLA.GACCT
					WHERE GLREF LIKE '%965943%'
					  AND GLA.GARP3 IN (500,600)
					GROUP BY GLRECD, GLCOMP, GLDIST, GLCSTC, GLT.GLACCT, GLDESC, GLPPYY, GLPERD, GLAPPL, GLBTCH, GLPGM,
							 GLUSER, GLAPTR, GLTRN#, GLTRNT, GLTYPE, GLREF, GLRFYY, GLRFMM, GLRFDD, GLCUST, GLCRDB, GLAMT,
							 GLA.GACDES, GLA.GARP3
					ORDER BY GLTRN#



USE SigmaTB;
select  [Transaction_#_____shordn], 
		[Cust_P/O#_____SHORDN],
		[Cust_P/O#_____SHCORD]
		*  from 
		[dbo].[z_Shipments_File_____SHIPMAST]
WHERE Shipment_Year_____SHIPYY = 25
AND shipment_Month_____SHIPMM = 2;

/
USE SigmaTB;



/*********************************************************************
SHIPMAST
************************************************************************/


SELECT

	[Transaction_#_____SHORDN], 
	[Cust_P/O#_____SHCORD], 
	ITEM_NUMBER_____SHITEM, 
	Shipment_Year_____SHIPYY, Shipment_Month_____SHIPMM, 
	[3_POSITION_CLASS_____SHCLS3], Shipped_Qty_____SHSQTY,                                          -- SHIPPED_QTY_UOM_____SHUOM, 
	Billing_Qty_____SHBQTY,                         --BILLING_QTY_UOM_____SHBUOM,  
	Order_Qty_____SHOQTY,                           --ORDER_QTY_UOM_____SHOUOM, 
	Shipped_Total_LBS_____SHTLBS, Shipped_Total_PCS_____SHTPCS, Shipped_Total_FTS_____SHTFTS, [Shipped_Total_Sq.Ft_____SHTSFT], 
	[Theo._Meters_____SHTMTR], Theo_Kilos_____SHTKG, Actual_Scrap_LBS_____SHSCLB, Actual_Scrap_KGS_____SHSCKG, 
	Material_Cost_Stock_____SHMCSS,Material_Sales_Stock_____SHMSLS,Sales_Qty_Stock_____SHSLSS, Sales_Weight_Stock_____SHSWGS,
	[Adjusted_GP%_____SHADPC], UNIT_PRICE_____SHUNSP,    Actual_Scrap_Dollars_____SHSCDL, 


	CUSTOMER_NUMBER_____SHCUST,  Outside_Salesman_____SHOUTS,  Date_Ordered_Century_____SHORCC, 
	Date_Ordered_Year_____SHORYY, Date_Ordered_Month_____SHORMM, Date_Ordered_Day_____SHORDD, Prom_Date_Century_____SHPRCC, Prom_Date_Year_____SHPRYY, 
	Prom_Date_Month_____SHPRMM, Prom_Date_Day_____SHPRDD, Date_Inv_Century_____SHIVCC, Date_Inv_Year_____SHIVYY, Date_Inv_Month_____SHIVMM, 
	Date_Inv_Day_____SHIVDD,  Matl_Sales_Direct_____SHMSLD, 
	Proc_Sales_Stock_____SHPSLS, Process_Sales_Direct_____SHPSLD, Other_Sales_Stock_____SHOSLS, Other__Sales_Direct_____SHOSLD, 
	Discount_Sales_Stock_____SHDSLS, Discnt_Sales_Direct_____SHDSLD,  Material_Cost_Direct_____SHMCSD, 
	[Freight-In_Cost_Direct_____SHFISD], [Frght-Out_Cost_Stock_____SHFOSS], [Frght-Out_Cost_Direct_____SHFOSD],
	Fin_Scrap_Fctr_Stock_____SHFSFS, Fin_Scrap_Fctr_Direct_____SHFSFD, Processing_Cost_Stock_____SHPCSS, Processing_Cost_Direct_____SHPCSD, 
	Other_Cost_Stock_____SHOCSS, Other_Cost_Direct_____SHOCSD, Admin_Burden_Stock_____SHADBS, Admin_Burden_Direct_____SHADBD, 
	Oper_Burden_Stock_____SHOPBS, Oper_Burden_Direct_____SHOPBD, Inv_Adj_Stock_____SHIAJS, Inv_Adj_Direct_____SHIAJD, 
	Sales_Qty_Direct_____SHSLSD,  Sales_Weight_Direct_____SHSWGD,  
	Unit_Selling_Price_UOM_____SHUUOM, [S/A_addition_flag_____SHSAFL], [Century_added_to_S/A_____SHSACC], [Year_added_to_S/A_____SHSAYY], 
	[Month_added_to_S/A_____SHSAMM], [Day_added_to_S/A_____SHSADD], [Freight_local+road_____SHFRGH], 
	[Valid_Values_1_-_PRODUCT_NOT_STOCKED_____SHDBDC], [SHIP-TO_COUNTRY_____SHSCTY], Zip_Code_____SHZIP, 
	Truck_Route_____SHTRCK, 
	ADDRESS_ONE_____SHADR1, ADDRESS_TWO_____SHADR2, [Orig_cust#_____SHCSTO],

	Order_designation_Code_____SHODES, Shop_OLD_____SHSHOP, [CUSTOMER_SHIP-TO_____SHSHTO], [BILL-TO_COUNTRY_____SHBCTY], 
	[TEMP_SHIP-TO?_____SHTMPS], Sale_Territory_____SHSTER, Customer_Trade_____SHTRAD, [Bus._Potential_Class_____SHBPCC], EEC_Code_____SHEEC, 
	Sector_Code_____SHSEC, Invoice_Type_____SHITYP, In_Sales_Dept_____SHDPTI, Out_Sales_Dept_____SHDPTO, [Orig_cust_dist#_____SHDSTO], 
	[Orig_Slsmn_Dist_____SHSMDO], Orig_Slsmn_____SHSLMO, Inv_Comp_____SHICMP, 
	 ADDRESS_THREE_____SHADR3, CITY_25_POS_____SHCITY, State_Code_____SHSTAT, Job_Name_____SHJOB, 
	Shape_____SHSHAP,     Scrap_Flag_____SHSCRP, [Cutting/Process_Flag_____SHCUTC],
	Processing_Charge_____SHPRCG, Handling_Charge_____SHHAND,    Frght_Sales_Stock_____SHFSLS, Frght_Sales_Direct_____SHFSLD,
	[Freight-In_Cost_Stock_____SHFISS], [Freight-In_Cost_Direct_____SHFISD],[Frght-Out_Cost_Direct_____SHFOSD], [Frght-Out_Cost_Direct_____SHFOSD],
	Fin_Scrap_Fctr_Direct_____SHFSFD
FROM
	SigmaTB.dbo.z_Shipments_File_____SHIPMAST T
WHERE   
	Shipment_Year_____SHIPYY = 25 
	AND Shipment_Month_____SHIPMM = 2;

GO


SELECT DISTINCT([Customer_Dist_____SHCDIS]) FROM [dbo].[z_Shipments_File_____SHIPMAST] T;
SELECT count(DISTINCT([Zip_Code_____SHZIP])) FROM [dbo].[z_Shipments_File_____SHIPMAST] ;

 SELECT [Zip_Code_____SHZIP], 
	ADDRESS_ONE_____SHADR1, 
	ADDRESS_TWO_____SHADR2,
	Truck_Route_____SHTRCK,
	COUNT(*) as 'Registers' 
FROM [dbo].[z_Shipments_File_____SHIPMAST] 
GROUP BY [Zip_Code_____SHZIP], 
	ADDRESS_ONE_____SHADR1, 
	ADDRESS_TWO_____SHADR2,    -- Added this line to GROUP BY
	Truck_Route_____SHTRCK
ORDER BY [Zip_Code_____SHZIP],
		ADDRESS_ONE_____SHADR1,
		ADDRESS_TWO_____SHADR2,
		Truck_Route_____SHTRCK;





USE SigmaTB;
SELECT * FROM sys.extended_properties ep
WHERE ep.major_id = 706101556

AND ep.minor_id = 41
AND ep.name = 'ATPTXA'


--We check the consistency of the data
USE SigmaTB;
SELECT DISTINCT(Record_Code_____GLRECD) FROM [dbo].[z_General_Ledger_Transaction_File_____GLTRANS]




-- SP to find the count, and list, of unique values by column
EXEC mysp_find_unique_values_table_column_by_code 
	@InputTableCode = N'SHIPMAST',
	@InputColumnCode = N'SHORDH';


--ERRORS

-- Translate querys from code to names
EXEC sp_format_query_with_descriptions 
	@InputQuery = 'SELECT SHORDN, SHCORD FROM SHIPMAST WHERE SHORDN IS NULL'


USE SIGMATB;


'EXEC my_sp_getXPfromObjects @InputSearchTerm = 'GLTRN#';'
EXEC my_sp_getXPfromObjects 'GLTRANS'


Use SigmaTB;
SELECT [Transaction_Type_____GLTRNT], [Trans#_____GLTRN#] FROM myRenamedSchema.[z_General_Ledger_Transaction_File_____GLTRANS] WHERE [Trans#_____GLTRN#] IS NOT NULL AND myRenamedSchema.[z_General_Ledger_Transaction_File_____GLTRANS].[z_General_Ledger_Account_file_____GLACCT] = '12345';

select top(1) * from myRenamedSchema.[z_General_Ledger_Transaction_File_____GLTRANS]




 SELECT *
				FROM sys.extended_properties AS ep
				INNER JOIN sys.tables AS t ON ep.major_id = t.object_id
				WHERE ep.class = 1
				  AND ep.minor_id = 0
				  AND ep.name = 'GLTRANS'




-- Assume these variables are declared and populated beforehand:
-- DECLARE @my_var_int_table_object_id int = OBJECT_ID('SchemaName.TableName'); -- e.g., get object_id for the target table
-- DECLARE @my_var_nvarchar_column_name sql_variant = N'YourColumnXPValue'; -- e.g., the value like 'GLACCT' to find



/*********************************************************************/
USE SigmaTB;

SELECT TOP(100) z_Shipments_File_____SHIPMAST.Transaction_#_____SHORDN
from  myRenamedSchema.z_Shipments_File_____SHIPMAST






/*******************************************************************************/

SELECT ''Sales analysis, SPO'' AS QueryName, CAST(CAST([z_Order_Detail_File_____OEDETAIL].[O/E_District_#_____ODDIST] AS DECIMAL(18, 2)) AS INT) * 1000000 + CAST(CAST([z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) AS Order_districtPlusTransaction, [z_Salesman_Master_File_____SALESMAN].[Salesman_Name_____SMNAME], [z_Open_Order_File_____OEOPNORD].[Order_Type_____OOTYPE], CAST(CAST([z_Order_Detail_File_____OEDETAIL].[CUSTOMER_DISTRICT_____ODCDIS] AS DECIMAL(18, 2)) AS INT) * 100000 + CAST(CAST([z_Order_Detail_File_____OEDETAIL].[CUSTOMER_NUMBER_____ODCUST] AS DECIMAL(18, 2)) AS INT) AS Customer_DistrictPlusCustomer, [z_Customer_Master_File_____ARCUST].[Customer_Alpha_Name_____CALPHA], CAST(CAST([z_Open_Order_File_____OEOPNORD].[INVOICE_CENTURY_____OOICC] AS DECIMAL(18, 2)) AS INT) * 1000000 + CAST(CAST([z_Open_Order_File_____OEOPNORD].[INVOICE_YEAR_____OOIYY] AS DECIMAL(18, 2)) AS INT) * 10000 + CAST(CAST([z_Open_Order_File_____OEOPNORD].[INVOICE_MONTH_____OOIMM] AS DECIMAL(18, 2)) AS INT) * 100 + CAST(CAST([z_Open_Order_File_____OEOPNORD].[INVOICE_DAY_____OOIDD] AS DECIMAL(18, 2)) AS INT) AS InvoiceDate_OOI, [z_Order_Detail_File_____OEDETAIL].[ITEM_NUMBER_____ODITEM], [z_Service_Purchase_Order_Header_File_____SPHEADER].[Ship_To_Vendor_#_____BSSVEN], [z_Service_Purchase_Order_Header_File_____SPHEADER].[Multiple_SPO_____BSSPS#] FROM [mrs].[z_Customer_Master_File_____ARCUST] AS [z_Customer_Master_File_____ARCUST], [mrs].[z_Order_Detail_File_____OEDETAIL] AS [z_Order_Detail_File_____OEDETAIL], [mrs].[z_Open_Order_File_____OEOPNORD] AS [z_Open_Order_File_____OEOPNORD], [mrs].[z_Salesman_Master_File_____SALESMAN] AS [z_Salesman_Master_File_____SALESMAN], [mrs].[z_Service_Purchase_Order_Header_File_____SPHEADER] AS [z_Service_Purchase_Order_Header_File_____SPHEADER] WHERE CAST(CAST([z_Order_Detail_File_____OEDETAIL].[O/E_District_#_____ODDIST] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Open_Order_File_____OEOPNORD].[O/E_Dist#_____OODIST] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Open_Order_File_____OEOPNORD].[ORDER_NUMBER_____OOORDR] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Open_Order_File_____OEOPNORD].[CUSTOMER_DISTRICT_____OOCDIS] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Customer_Master_File_____ARCUST].[CUSTOMER_DISTRICT_NUMBER_____CDIST] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Open_Order_File_____OEOPNORD].[CUSTOMER_NUMBER_____OOCUST] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Customer_Master_File_____ARCUST].[CUSTOMER_NUMBER_____CCUST] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Open_Order_File_____OEOPNORD].[INSIDE_SALESMAN_DISTRICT_____OOISMD] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Salesman_Master_File_____SALESMAN].[Salesman_District_Number_____SMDIST] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Open_Order_File_____OEOPNORD].[INSIDE_SALESMAN_NUMBER_____OOISMN] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Salesman_Master_File_____SALESMAN].[Salesman_Number_____SMSMAN] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Order_Detail_File_____OEDETAIL].[O/E_District_#_____ODDIST] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Service_Purchase_Order_Header_File_____SPHEADER].[DISTRICT_NUMBER_____BSDIST] AS DECIMAL(18, 2)) AS INT) AND CAST(CAST([z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) = CAST(CAST([z_Service_Purchase_Order_Header_File_____SPHEADER].[Transaction_#_____BSORDR] AS DECIMAL(18, 2)) AS INT) AND (([z_Open_Order_File_____OEOPNORD].[Order_Type_____OOTYPE] IN (''A'',''B'')) AND ([z_Open_Order_File_____OEOPNORD].[Record_Code_____OORECD] = ''W'') AND CAST(CAST([z_Order_Detail_File_____OEDETAIL].[O/E_District_#_____ODDIST] AS DECIMAL(18, 2)) AS INT) = 1 AND CAST(CAST([z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) > @SPOTransactionNumber) ORDER BY [z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR];

--find columns for GL
SELECT [TableAS400Name], [ColumnAS400Name] FROM [mrs].[01_AS400_MSSQL_Equivalents_Columns] WHERE [ColumnAS400Name] IN ('GLRECD', 'GARP3', 'GLACCT', 'GACDES', 'YYMMDD', 'GLDESC', 'GLREF', 'GLAMTQ', 'GLAPPL', 'GLPGM', 'GLUSER', 'GLRPTY', 'GLRP#', 'GLTRNT', 'GLTYPE', 'GLTRDS', 'GLTRN#', 'DATE') ORDER BY [TableAS400Name], [ColumnAS400Name];


--GL Query
SELECT [g1].[Description_____GACDES] AS [GACDES], [g1].[Description_____GARP3] AS [GARP3], [g2].[Description_____GLACCT] AS [GLACCT_DEBC], [g2].[Description_____GLAPPL] AS [GLAPPL_DEBC], [g2].[Description_____GLDESC] AS [GLDESC_DEBC], [g2].[Description_____GLPGM] AS [GLPGM_DEBC], [g2].[Description_____GLRECD] AS [GLRECD_DEBC], [g2].[Description_____GLREF] AS [GLREF_DEBC], [g2].[Description_____GLRP#] AS [GLRP#_DEBC], [g2].[Description_____GLRPTY] AS [GLRPTY_DEBC], [g2].[Description_____GLUSER] AS [GLUSER_DEBC], [g3].[Description_____GLACCT] AS [GLACCT_TRAN], [g3].[Description_____GLAMTQ] AS [GLAMTQ], [g3].[Description_____GLAPPL] AS [GLAPPL_TRAN], [g3].[Description_____GLDESC] AS [GLDESC_TRAN], [g3].[Description_____GLPGM] AS [GLPGM_TRAN], [g3].[Description_____GLRECD] AS [GLRECD_TRAN], [g3].[Description_____GLREF] AS [GLREF_TRAN], [g3].[Description_____GLRP#] AS [GLRP#_TRAN], [g3].[Description_____GLRPTY] AS [GLRPTY_TRAN], [g3].[Description_____GLTRDS] AS [GLTRDS], [g3].[Description_____GLTRN#] AS [GLTRN#], [g3].[Description_____GLTRNT] AS [GLTRNT], [g3].[Description_____GLTYPE] AS [GLTYPE], [g3].[Description_____GLUSER] AS [GLUSER_TRAN]
FROM [mrs].[z_GL_Account_Master_____GLACCT] AS [g1]
JOIN [mrs].[z_GL_Debit_Credit_____GLDEBCRED] AS [g2] ON [g1].[Description_____SOME_KEY] = [g2].[Description_____SOME_KEY] JOIN [mrs].[z_GL_Transactions_____GLTRANS] AS [g3] ON [g1].[Description_____SOME_KEY] = [g3].[Description_____SOME_KEY]






SELECT   
		OE.[Transaction_#_____ODORDR],
		A.[Customer_Alpha_Name_____CALPHA],
		SP.[Ship_To_Vendor_#_____BSSVEN],
		* 
FROM     [mrs].[z_Order_Detail_File_____OEDETAIL] OE
LEFT JOIN [mrs].[z_Customer_Master_File_____ARCUST] A
		ON OE.[CUSTOMER_NUMBER_____ODCUST] = A.[CUSTOMER_NUMBER_____CCUST]
LEFT JOIN [mrs].[z_Service_Purchase_Order_Header_File_____SPHEADER] SP
		ON CAST(CAST(OE.[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) = 
		   CAST(CAST(SP.[Transaction_#_____BSORDR] AS DECIMAL(18, 2)) AS INT)
WHERE CAST(CAST(OE.[Transaction_#_____ODORDR] AS DECIMAL(18, 2)) AS INT) = 968207


select * from     [mrs].[z_Open_Order_File_____OEOPNORD]  WHERE   [z_Order_Detail_File_____OEDETAIL].[Transaction_#_____ODORDR] = '968207'

968207





USE SIGMATB;

EXEC [mrs].[sub_FindColumnPropertiesAndSearch] 
	@myVarVARCHARParamColumnCode = N'%ORD%',
	@myVarVARCHARParamSearchValue = N'968207',
	@myVarBITDebugMode = 0;




