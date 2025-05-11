

/***************************************************************************
SAVE THIS
RETURNS THE TYPE OF DATA FOR THE SPECIFIED COLUMN
-----------------------------------------------------------------------------
		SELECT 
			COLUMN_NAME,
			DATA_TYPE,
			CHARACTER_MAXIMUM_LENGTH,
			NUMERIC_PRECISION,
			NUMERIC_SCALE,
			IS_NULLABLE
		FROM 
			INFORMATION_SCHEMA.COLUMNS
		WHERE 
			TABLE_NAME =		'mysql_____ap'	--'z_Shipments_File_____SHIPMAST'
			AND COLUMN_NAME =	'PO_______PO__'			--'Transaction_#_____SHORDN';

********************************************************************************/


