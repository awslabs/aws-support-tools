USE [DB_NAME];
GO

/* SP "DuplicateLogin" Duplicates the Login and duplicates database user for those logins in each database that the login permissions that you're copying from is present*/
IF OBJECT_ID('dbo.DuplicateLogin') IS NULL
	EXEC ('CREATE PROCEDURE [dbo].[DuplicateLogin] AS SELECT 1')
GO
ALTER PROCEDURE [dbo].[DuplicateLogin] @NewLogin SYSNAME
	,@NewLoginPwd NVARCHAR(MAX)
	,@WindowsLogin CHAR(1)
	,@LoginToDuplicate SYSNAME
	,@DatabaseName SYSNAME = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @SQL AS NVARCHAR (MAX);
    CREATE TABLE #DuplicateLogins (
        SqlCommand NVARCHAR (MAX)
    );
    SET @SQL = '/' + '*' + 'BEGIN: DUPLICATE SERVER LOGIN' + '*' + '/';
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT @SQL;
    SET @SQL = '/' + '*' + 'CREATE SERVER LOGIN' + '*' + '/';
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT @SQL;
    IF (@WindowsLogin = 'T')
        BEGIN
            SET @SQL = 'CREATE LOGIN [' + @NewLogin + '] FROM WINDOWS;';
            INSERT INTO #DuplicateLogins (SqlCommand)
            SELECT @SQL;
        END
    ELSE
        BEGIN
            SET @SQL = 'CREATE LOGIN [' + @NewLogin + '] WITH PASSWORD = N''' + @NewLoginPwd + ''';';
            INSERT INTO #DuplicateLogins (SqlCommand)
            SELECT @SQL;
        END
    SET @SQL = '/' + '*' + 'DUPLICATE SERVER ROLES' + '*' + '/';
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT @SQL;
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT 'EXEC sp_addsrvrolemember @loginame = ''' + @NewLogin + ''', @rolename = ''' + R.NAME + ''';' AS 'SQL'
    FROM   sys.server_role_members AS RM
           INNER JOIN
           sys.server_principals AS L
           ON RM.member_principal_id = L.principal_id
           INNER JOIN
           sys.server_principals AS R
           ON RM.role_principal_id = R.principal_id
    WHERE  L.NAME = @LoginToDuplicate;
    IF @@ROWCOUNT = 0
        BEGIN
            SET @SQL = '/' + '*' + '---- No Server Roles To Clone' + '*' + '/';
            INSERT INTO #DuplicateLogins (SqlCommand)
            SELECT @SQL;
        END
    SET @SQL = '/' + '*' + 'DUPLICATE SERVER PERMISSIONS' + '*' + '/';
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT @SQL;
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT [SQL]
    FROM   (SELECT CASE P.[STATE] WHEN 'W' THEN 'USE master;GRANT ' + P.permission_name + ' TO [' + @NewLogin + '] WITH GRANT OPTION;' ELSE 'USE master;  ' + P.state_desc + ' ' + P.permission_name + ' TO [' + @NewLogin + '];' END AS [SQL]
            FROM   sys.server_permissions AS P
                   INNER JOIN
                   sys.server_principals AS L
                   ON P.grantee_principal_id = L.principal_id
            WHERE  L.NAME = @LoginToDuplicate
                   AND P.class = 100
                   AND P.type <> 'COSQ'
                   AND P.state_desc <> 'DENY'
                   AND P.permission_name <> 'ALTER ANY CREDENTIAL'
            UNION ALL
            SELECT CASE P.[STATE] WHEN 'W' THEN 'GRANT ' + P.permission_name + ' TO [' + @NewLogin + '] ;' ELSE 'USE master;  ' + P.state_desc + ' ' + P.permission_name + ' TO [' + @NewLogin + '];' END AS [SQL]
            FROM   sys.server_permissions AS P
                   INNER JOIN
                   sys.server_principals AS L
                   ON P.grantee_principal_id = L.principal_id
            WHERE  L.NAME = @LoginToDuplicate
                   AND P.class = 100
                   AND P.type <> 'COSQ'
                   AND P.state_desc <> 'DENY'
                   AND P.permission_name = 'ALTER ANY CREDENTIAL'
            UNION ALL
            SELECT CASE P.[STATE] WHEN 'W' THEN 'USE master; GRANT ' + P.permission_name + ' ON LOGIN::[' + L2.NAME + '] TO [' + @NewLogin + '] WITH GRANT OPTION;' COLLATE DATABASE_DEFAULT ELSE 'USE master; ' + P.state_desc + ' ' + P.permission_name + ' ON LOGIN::[' + L2.NAME + '] TO [' + @NewLogin + '];' COLLATE DATABASE_DEFAULT END AS [SQL]
            FROM   sys.server_permissions AS P
                   INNER JOIN
                   sys.server_principals AS L
                   ON P.grantee_principal_id = L.principal_id
                   INNER JOIN
                   sys.server_principals AS L2
                   ON P.major_id = L2.principal_id
            WHERE  L.NAME = @LoginToDuplicate
                   AND P.state_desc <> 'DENY'
                   AND P.class = 101
            UNION ALL
            SELECT CASE P.[STATE] WHEN 'W' THEN 'USE master; GRANT ' + P.permission_name + ' ON ENDPOINT::[' + E.NAME + '] TO [' + @NewLogin + '] WITH GRANT OPTION;' COLLATE DATABASE_DEFAULT ELSE 'USE master; ' + P.state_desc + ' ' + P.permission_name + ' ON ENDPOINT::[' + E.NAME + '] TO [' + @NewLogin + '];' COLLATE DATABASE_DEFAULT END AS [SQL]
            FROM   sys.server_permissions AS P
                   INNER JOIN
                   sys.server_principals AS L
                   ON P.grantee_principal_id = L.principal_id
                   INNER JOIN
                   sys.endpoints AS E
                   ON P.major_id = E.endpoint_id
            WHERE  L.NAME = @LoginToDuplicate
                   AND P.class = 105
                   AND P.state_desc <> 'DENY') AS ServerPermission;
    IF @@ROWCOUNT = 0
        BEGIN
            SET @SQL = '/' + '*' + '---- No Server Permissions To Clone' + '*' + '/';
            INSERT INTO #DuplicateLogins (SqlCommand)
            SELECT @SQL;
        END
    SET @SQL = '/' + '*' + 'END: DUPLICATE SERVER LOGIN' + '*' + '/';
    INSERT INTO #DuplicateLogins (SqlCommand)
    SELECT @SQL;
    SELECT *
    FROM   #DuplicateLogins;
END
BEGIN
    SET NOCOUNT ON;
    DECLARE @SQL2 AS NVARCHAR (MAX);
    DECLARE @DbName AS SYSNAME;
    DECLARE @Database TABLE (
        DbName SYSNAME);
    SET @DbName = '';
    CREATE TABLE #DuplicateDBUsers (
        SqlCommand NVARCHAR (MAX)
    );
    IF @DatabaseName IS NULL
        BEGIN
            INSERT INTO @Database (DbName)
            SELECT   NAME
            FROM     sys.databases
            WHERE    state_desc = 'ONLINE'
                     AND NAME NOT IN ('model','rdsadmin', 'rdsadmin_ReportServer', 'rdsadmin_ReportServerTempDB')
            ORDER BY NAME ASC;
        END
    ELSE
        BEGIN
            INSERT INTO @Database (DbName)
            SELECT @DatabaseName;
        END
    SET @SQL2 = '/' + '*' + 'BEGIN: CREATE DATABASE USER' + '*' + '/';
    INSERT INTO #DuplicateDBUsers (SqlCommand)
    SELECT @SQL2;
    WHILE @DbName IS NOT NULL
        BEGIN
            SET @DbName = (SELECT MIN(DbName)
                           FROM   @Database
                           WHERE  DbName > @DbName);
            SET @SQL2 = '
INSERT INTO #DuplicateDBUsers (SqlCommand)
SELECT ''USE [' + @DbName + ']; 
IF EXISTS(SELECT name FROM sys.database_principals 
WHERE name = ' + '''''' + @LoginToDuplicate + '''''' + ')
BEGIN
CREATE USER [' + @NewLogin + '] FROM LOGIN [' + @NewLogin + '];
END;''';
            EXECUTE (@SQL2);
        END
    IF EXISTS (SELECT COUNT(SqlCommand)
               FROM   #DuplicateDBUsers
               HAVING COUNT(SqlCommand) < 2)
        BEGIN
            SET @SQL2 = '/' + '*' + '---- No Database User To Create' + '*' + '/';
            INSERT INTO #DuplicateDBUsers (SqlCommand)
            SELECT @SQL2;
        END
    SET @SQL2 = '/' + '*' + 'END: CREATE DATABASE USER' + '*' + '/';
    INSERT INTO #DuplicateDBUsers (SqlCommand)
    SELECT @SQL2;
    SELECT SqlCommand
    FROM   #DuplicateDBUsers;
    DROP TABLE #DuplicateDBUsers;
END
GO
/*---------------------------------------------------------------------------------------------------------------*/
/* "GrantUserRoleMembership" is a SP to duplicate DB user permissions and roles to the new user */
USE [DB_NAME];
GO
IF OBJECT_ID('dbo.GrantUserRoleMembership') IS NULL
	EXEC ('CREATE PROCEDURE [dbo].[GrantUserRoleMembership] AS SELECT 1')
GO
ALTER PROC dbo.GrantUserRoleMembership @NewLogin SYSNAME
	,@LoginToDuplicate SYSNAME
	,@DatabaseName SYSNAME = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @SQL AS NVARCHAR (MAX);
    DECLARE @DbName AS SYSNAME;
    DECLARE @Database TABLE (
        DbName SYSNAME);
    SET @DbName = '';
    CREATE TABLE #DuplicateRoleMembershipScript (
        SqlCommand NVARCHAR (MAX)
    );
    IF @DatabaseName IS NULL
        BEGIN
            INSERT INTO @Database (DbName)
            SELECT   [name]
            FROM     sys.databases
            WHERE    HAS_DBACCESS([name]) = 1
                     AND name NOT IN ('model', 'rdsadmin', 'rdsadmin_ReportServer', 'rdsadmin_ReportServerTempDB', 'SSISDB')
            ORDER BY NAME ASC;
        END
    ELSE
        BEGIN
            INSERT INTO @Database (DbName)
            SELECT @DatabaseName;
        END
    SET @SQL = '/' + '*' + 'BEGIN: DUPLICATE DATABASE ROLE MEMBERSHIP' + '*' + '/';
    INSERT INTO #DuplicateRoleMembershipScript (SqlCommand)
    SELECT @SQL;
    WHILE @DbName IS NOT NULL
        BEGIN
            SET @DbName = (SELECT MIN(DbName)
                           FROM   @Database
                           WHERE  DbName > @DbName
                                  AND DbName NOT IN ('model', 'rdsadmin', 'rdsadmin_ReportServer', 'rdsadmin_ReportServerTempDB', 'SSISDB'));
            SET @SQL = '
INSERT INTO #DuplicateRoleMembershipScript (SqlCommand)
SELECT ''USE [' + @DbName + ']; EXEC sp_addrolemember @rolename = '''''' + R.name
+ '''''', @membername = ''''' + @NewLogin + ''''';''
FROM [' + @DbName + '].sys.database_principals AS U
JOIN [' + @DbName + '].sys.database_role_members AS RM
ON U.principal_id = RM.member_principal_id
JOIN [' + @DbName + '].sys.database_principals AS R
ON RM.role_principal_id = R.principal_id
WHERE U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL);
        END
    IF EXISTS (SELECT COUNT(SqlCommand)
               FROM   #DuplicateRoleMembershipScript
               HAVING COUNT(SqlCommand) < 2)
        BEGIN
            SET @SQL = '/' + '*' + '---- No Database Roles To Duplicate' + '*' + '/';
            INSERT INTO #DuplicateRoleMembershipScript (SqlCommand)
            SELECT @SQL;
        END
    SET @SQL = '/' + '*' + 'END: DUPLICATE DATABASE ROLE MEMBERSHIP' + '*' + '/';
    INSERT INTO #DuplicateRoleMembershipScript (SqlCommand)
    SELECT @SQL;
    SELECT SqlCommand
    FROM   #DuplicateRoleMembershipScript;
    DROP TABLE #DuplicateRoleMembershipScript;
END
BEGIN
    SET NOCOUNT ON;
    DECLARE @SQL2 AS NVARCHAR (MAX);
    DECLARE @DBName2 AS SYSNAME;
    DECLARE @Database2 TABLE (
        DbName SYSNAME);
    SET @DBName2 = '';
    CREATE TABLE #DuplicateDbPermissionScript (
        SqlCommand NVARCHAR (MAX)
    );
    IF @DatabaseName IS NULL
        BEGIN
            INSERT INTO @Database2 (DbName)
            SELECT   [name]
            FROM     sys.databases
            WHERE    HAS_DBACCESS([name]) = 1
                     AND [name] NOT IN ('model', 'rdsadmin', 'rdsadmin_ReportServer', 'rdsadmin_ReportServerTempDB', 'SSISDB')
            ORDER BY NAME;
        END
    ELSE
        BEGIN
            INSERT INTO @Database2 (DbName)
            SELECT @DatabaseName;
        END
    SET @SQL2 = '/' + '*' + 'BEGIN: DUPLICATE DATABASE PERMISSIONS' + '*' + '/';
    INSERT INTO #DuplicateDbPermissionScript (SqlCommand)
    SELECT @SQL2;
    WHILE @DBName2 IS NOT NULL
        BEGIN
            SET @DBName2 = (SELECT MIN(DbName)
                            FROM   @Database2
                            WHERE  DbName > @DBName2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON DATABASE::[' + @DBName2 + '] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON DATABASE::[' + @DBName2 + '] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	WHERE class = 0
	  AND P.[type] <> ''CO''
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON SCHEMA::[''
		 + S.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON SCHEMA::[''
		 + S.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.schemas AS S
		ON S.schema_id = P.major_id
	WHERE class = 3
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON OBJECT::[''
		 + S.name + ''].['' + O.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON OBJECT::[''
		 + S.name + ''].['' + O.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.objects AS O
		ON O.object_id = P.major_id
	  JOIN [' + @DBName2 + '].sys.schemas AS S
		ON S.schema_id = O.schema_id
	WHERE class = 1
	  AND U.name = ''' + @LoginToDuplicate + '''
	  AND P.major_id > 0
	  AND P.minor_id = 0';
            EXECUTE (@SQL2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON OBJECT::[''
		 + S.name + ''].['' + O.name + ''] ('' + C.name + '') TO [' + @NewLogin + '] WITH GRANT OPTION;''
		 COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON OBJECT::[''
		 + S.name + ''].['' + O.name + ''] ('' + C.name + '') TO [' + @NewLogin + '];''
		 COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.objects AS O
		ON O.object_id = P.major_id
	  JOIN [' + @DBName2 + '].sys.schemas AS S
		ON S.schema_id = O.schema_id
	  JOIN [' + @DBName2 + '].sys.columns AS C
		ON C.column_id = P.minor_id AND O.object_id = C.object_id
	WHERE class = 1
	  AND U.name = ''' + @LoginToDuplicate + '''
	  AND P.major_id > 0
	  AND P.minor_id > 0;';
            EXECUTE (@SQL2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON ROLE::[''
		 + U2.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON ROLE::[''
		 + U2.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.database_principals AS U2
		ON U2.principal_id = P.major_id
	WHERE class = 4
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL2);
            SET @SQL2 = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON SYMMETRIC KEY::[''
		 + K.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON SYMMETRIC KEY::[''
		 + K.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.symmetric_keys AS K
		ON P.major_id = K.symmetric_key_id
	WHERE class = 24
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL2);
            SET @SQL = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON ASYMMETRIC KEY::[''
		 + K.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON ASYMMETRIC KEY::[''
		 + K.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.asymmetric_keys AS K
		ON P.major_id = K.asymmetric_key_id
	WHERE class = 26
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL);
            SET @SQL = 'INSERT INTO #DuplicateDbPermissionScript(SqlCommand)
	SELECT CASE [state]
	   WHEN ''W'' THEN ''USE [' + @DBName2 + ']; GRANT '' + permission_name + '' ON CERTIFICATE::[''
		 + C.name + ''] TO [' + @NewLogin + '] WITH GRANT OPTION;'' COLLATE DATABASE_DEFAULT
	   ELSE ''USE [' + @DBName2 + ']; '' + state_desc + '' '' + permission_name + '' ON CERTIFICATE::[''
		 + C.name + ''] TO [' + @NewLogin + '];'' COLLATE DATABASE_DEFAULT
	   END AS ''Permission''
	FROM [' + @DBName2 + '].sys.database_permissions AS P
	  JOIN [' + @DBName2 + '].sys.database_principals AS U
		ON P.grantee_principal_id = U.principal_id
	  JOIN [' + @DBName2 + '].sys.certificates AS C
		ON P.major_id = C.certificate_id
	WHERE class = 25
	  AND U.name = ''' + @LoginToDuplicate + ''';';
            EXECUTE (@SQL);
        END
    IF EXISTS (SELECT COUNT(SqlCommand)
               FROM   #DuplicateDbPermissionScript
               HAVING COUNT(SqlCommand) < 2)
        BEGIN
            SET @SQL = '/' + '*' + '---- No Database Permissions To Duplicate' + '*' + '/';
            INSERT INTO #DuplicateDbPermissionScript (SqlCommand)
            SELECT @SQL;
        END
    SET @SQL = '/' + '*' + 'END: DUPLICATE DATABASE PERMISSIONS' + '*' + '/';
    INSERT INTO #DuplicateDbPermissionScript (SqlCommand)
    SELECT @SQL;
    SELECT SqlCommand
    FROM   #DuplicateDbPermissionScript;
    DROP TABLE #DuplicateDbPermissionScript;
END;
GO
/*---------------------------------------------------------------------------------------------------------------*/
/* "DuplicateRDS"  consolidates the results of both the SP "DuplicateLogin" and "GrantUserRoleMembership" */
USE [DB_NAME];
GO
IF OBJECT_ID('dbo.DuplicateRDS') IS NULL
	EXEC ('CREATE PROCEDURE [dbo].[DuplicateRDS] AS SELECT 1')
GO
ALTER PROC dbo.DuplicateRDS @NewLogin SYSNAME
	,@NewLoginPwd NVARCHAR(MAX)
	,@WindowsLogin CHAR(1)
	,@LoginToDuplicate SYSNAME
	,@DatabaseName SYSNAME = NULL
AS
BEGIN
    SET NOCOUNT ON;
	/* checking if login existed on server or not*/
	IF NOT EXISTS(select name from sys.syslogins where name=@LoginToDuplicate)
		BEGIN
			PRINT 'Login ' + @LoginToDuplicate + ' not existed in current RDS instance'
			RETURN
		END
    IF EXISTS (SELECT [name]
               FROM   tempdb.sys.tables
               WHERE  [name] LIKE '#DuplicateRDSScript%')
        BEGIN
            DROP TABLE #DuplicateRDSScript;
        END
    CREATE TABLE #DuplicateRDSScript (
        SqlCommand NVARCHAR (MAX)
    );
    INSERT INTO #DuplicateRDSScript
    EXECUTE [DB_NAME].dbo.[DuplicateLogin] @NewLogin = @NewLogin, @NewLoginPwd = @NewLoginPwd, @WindowsLogin = @WindowsLogin, @LoginToDuplicate = @LoginToDuplicate, @DatabaseName = @DatabaseName;
    INSERT INTO #DuplicateRDSScript
    EXECUTE [DB_NAME].dbo.GrantUserRoleMembership @NewLogin = @NewLogin, @LoginToDuplicate = @LoginToDuplicate, @DatabaseName = @DatabaseName;
    SELECT SqlCommand
    FROM   #DuplicateRDSScript;
    DROP TABLE #DuplicateRDSScript;
END

GO