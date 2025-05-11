/*******************************************************************************************
OBTAIN INFO ABOUT THE LOCAL SERVER
*******************************************************************************************/
SELECT 
    @@SERVERNAME AS ServerName,
    SERVERPROPERTY('ServerName') AS FullServerName,
    SERVERPROPERTY('InstanceName') AS InstanceName,
    CURRENT_USER AS CurrentUser,
    DB_NAME() AS CurrentDatabase,
    SYSTEM_USER AS SystemUser,
    SESSION_USER AS SessionUser,
    ORIGINAL_LOGIN() AS OriginalLogin,
    CONNECTIONPROPERTY('local_net_address') AS ServerIPAddress,
    CONNECTIONPROPERTY('protocol_type') AS Protocol,
    CONNECTIONPROPERTY('auth_scheme') AS AuthScheme,
    @@VERSION AS SQLVersion

	/***********
		```
		ServerName:         STB-LT-ES
		FullServerName:     STB-LT-ES
		InstanceName:       NULL
		CurrentUser:        dbo
		CurrentDatabase:    master
		SystemUser:         sa
		SessionUser:        dbo
		OriginalLogin:      sa
		ServerIPAddress:    NULL
		Protocol:           TSQL
		AuthScheme:         SQL
		SQLVersion:         Microsoft SQL Server 2019 (RTM) - 15.0.2000.5 (X64)  Sep 24 2019 13:48:23  Copyright (C) 2019 Microsoft Corporation  Developer Edition (64-bit) on Windows 10 Pro 10.0 <X64> (Build 22631: ) (Hypervisor)
		```
**************************************************************/


/**********************************************************************
SET UP LINKED SERVER
**********************************************************************/
-- Create a linked server to the AWS RDS SQL Server
USE SigmaTBLocal;
GO

-- Create a linked server to the AWS RDS SQL Server
EXEC sp_addlinkedserver 
    @server = 'AWS_SigmaTB',             -- Name for the linked server
    @srvproduct = '',                    -- Leave empty when using provider
    @provider = 'SQLNCLI11',             -- SQL Server Native Client 11.0
    @datasrc = 'database-3.c67ymu6q22o1.us-east-1.rds.amazonaws.com',  -- AWS RDS endpoint
    @catalog = 'SigmaTB';                -- Target database name

-- Add credentials for the linked server
EXEC sp_addlinkedsrvlogin 
    @rmtsrvname = 'AWS_SigmaTB',         -- Must match the name used above
    @useself = 'False',                  -- Don't use current login
    @locallogin = NULL,                  -- Apply to all local logins
    @rmtuser = 'admin',                  -- Remote username
    @rmtpassword = 'Er1c41234$';         -- Password

/***************************************************************************************************
TEST CONNECTION
****************************************************************************************************/
-- Test query
SELECT TOP 1 * FROM [AWS_SigmaTB].[SigmaTB].[INFORMATION_SCHEMA].[TABLES];
