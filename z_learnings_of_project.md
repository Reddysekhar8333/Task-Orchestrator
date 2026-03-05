### reset DB schema + migration history cleanly
1) Backup first
In Azure SQL: export bacpac or snapshot before destructive changes.

2) Connect to Azure SQL and clear migration history
Run in SSMS / Azure Data Studio on your target DB:
```bash
SELECT app, name, applied FROM django_migrations ORDER BY app, applied; # to see migrations
Then remove rows (project apps first, or all if full reset):

DELETE FROM django_migrations WHERE app IN ('tasks', 'users');
-- or full reset:
-- DELETE FROM django_migrations; # to delete migrations
```
3) Drop app tables (if you truly want fresh start)
If you only delete django_migrations but keep tables, Django may fail with “table already exists” later.

For full clean reset, easiest is to recreate DB.
If not recreating DB, drop project tables manually (and related FK tables).

4) Re-run migrations from app container/host
`python task_manager/manage.py migrate`

### here’s the exact Azure SQL reset script you can run to delete existing Django migration state and app tables safely.
```bash
/* ====== DANGER: destructive reset for Django project tables ====== */
/* Backup first. */

BEGIN TRY
    BEGIN TRANSACTION;

    /* 1) Drop all FOREIGN KEY constraints on project tables first */
    DECLARE @sql NVARCHAR(MAX) = N'';

    ;WITH target_tables AS (
        SELECT t.object_id, s.name AS schema_name, t.name AS table_name
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        WHERE t.name LIKE 'users_%'
           OR t.name LIKE 'tasks_%'
           OR t.name IN (
                'users_user',
                'tasks_task',
                'django_migrations',
                'django_admin_log',
                'django_session',
                'authtoken_token',
                'auth_group',
                'auth_group_permissions',
                'auth_permission',
                'users_user_groups',
                'users_user_user_permissions'
           )
    )
    SELECT @sql = @sql +
        N'ALTER TABLE ' + QUOTENAME(SCHEMA_NAME(pt.schema_id)) + N'.' + QUOTENAME(pt.name) +
        N' DROP CONSTRAINT ' + QUOTENAME(fk.name) + N';' + CHAR(10)
    FROM sys.foreign_keys fk
    JOIN sys.tables pt ON pt.object_id = fk.parent_object_id
    JOIN sys.tables rt ON rt.object_id = fk.referenced_object_id
    WHERE pt.name LIKE 'users_%'
       OR pt.name LIKE 'tasks_%'
       OR rt.name LIKE 'users_%'
       OR rt.name LIKE 'tasks_%'
       OR pt.name IN ('django_migrations','django_admin_log','django_session','authtoken_token',
                      'auth_group','auth_group_permissions','auth_permission',
                      'users_user_groups','users_user_user_permissions')
       OR rt.name IN ('django_migrations','django_admin_log','django_session','authtoken_token',
                      'auth_group','auth_group_permissions','auth_permission',
                      'users_user_groups','users_user_user_permissions');

    IF LEN(@sql) > 0 EXEC sp_executesql @sql;

    /* 2) Drop project tables if they exist */
    DROP TABLE IF EXISTS dbo.tasks_task;
    DROP TABLE IF EXISTS dbo.users_user_groups;
    DROP TABLE IF EXISTS dbo.users_user_user_permissions;
    DROP TABLE IF EXISTS dbo.users_user;
    DROP TABLE IF EXISTS dbo.django_admin_log;
    DROP TABLE IF EXISTS dbo.django_session;
    DROP TABLE IF EXISTS dbo.authtoken_token;
    DROP TABLE IF EXISTS dbo.auth_group_permissions;
    DROP TABLE IF EXISTS dbo.auth_group;
    DROP TABLE IF EXISTS dbo.auth_permission;
    DROP TABLE IF EXISTS dbo.django_migrations;

    COMMIT TRANSACTION;
    PRINT 'Reset complete.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
```

### port collisions
What’s happening?
Earlier, your Jenkins pipeline mentioned that it was deploying your application. Usually, when a Jenkins job "takes over" a port or starts a Docker container that binds to 8080, and then the Jenkins service itself tries to restart, they fight over the same "socket."