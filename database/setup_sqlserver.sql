CREATE LOGIN app_user WITH PASSWORD = 'TuPassword123!', CHECK_POLICY = OFF;

CREATE DATABASE observabilidad_documental_shard1;
CREATE DATABASE observabilidad_documental_shard2;
CREATE DATABASE observabilidad_documental_shard1_replica;
CREATE DATABASE observabilidad_documental_shard2_replica;

USE observabilidad_documental_shard1;
CREATE USER app_user FOR LOGIN app_user;
ALTER ROLE db_owner ADD MEMBER app_user;

USE observabilidad_documental_shard2;
CREATE USER app_user FOR LOGIN app_user;
ALTER ROLE db_owner ADD MEMBER app_user;

USE observabilidad_documental_shard1_replica;
CREATE USER app_user FOR LOGIN app_user;
ALTER ROLE db_owner ADD MEMBER app_user;

USE observabilidad_documental_shard2_replica;
CREATE USER app_user FOR LOGIN app_user;
ALTER ROLE db_owner ADD MEMBER app_user;