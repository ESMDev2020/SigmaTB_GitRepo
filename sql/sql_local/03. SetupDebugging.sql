
USE SigmaTBLocal;
GO

-- Enable detailed error messages
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

-- This is your debugging wrapper
-- Create a stored procedure to help with debugging
CREATE OR ALTER PROCEDURE [dbo].[Debug_usp_TranslateSQLQuery]
AS
BEGIN
    -- Variables that match your original procedure parameters
    -- Replace these with the actual parameters your procedure expects
    DECLARE @SourceSQL NVARCHAR(MAX) = 'SELECT * FROM [AWS_SigmaTB].[SigmaTB].[mrs].[z_Customer_Master_File_____ARCUST] WHERE 1=1';
    -- Add any other parameters your procedure needs
    
    BEGIN TRY
        -- Execute your procedure
        PRINT 'Executing procedure with test parameters...';
        EXEC [mrs].[usp_TranslateSQLQuery] 
            @SourceSQL = @SourceSQL
            -- Add other parameters as needed
        
        PRINT 'Procedure executed successfully';
    END TRY
    BEGIN CATCH
        PRINT 'Error occurred: ' + ERROR_MESSAGE();
        PRINT 'Line number: ' + CAST(ERROR_LINE() AS NVARCHAR(10));
        -- Additional error details if needed
        THROW;
    END CATCH
END;
GO