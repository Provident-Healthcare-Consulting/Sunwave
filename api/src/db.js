const sql = require('mssql');
const { DefaultAzureCredential } = require('@azure/identity');

let _pool = null;
let _poolPromise = null;
const credential = new DefaultAzureCredential();

async function buildConfig() {
  const token = await credential.getToken('https://database.windows.net/.default');
  return {
    server: process.env.AZURE_SQL_SERVER,
    database: process.env.AZURE_SQL_DATABASE,
    port: parseInt(process.env.AZURE_SQL_PORT || '1433', 10),
    authentication: {
      type: 'azure-active-directory-access-token',
      options: { token: token.token },
    },
    options: { encrypt: true, trustServerCertificate: false },
    connectionTimeout: 60000,
    requestTimeout: 60000,
    pool: { max: 10, min: 0, idleTimeoutMillis: 30000 },
  };
}

async function getPool() {
  if (_pool && _pool.connected) return _pool;
  if (!_poolPromise) {
    _poolPromise = (async () => {
      const config = await buildConfig();
      _pool = await new sql.ConnectionPool(config).connect();
      _pool.on('error', () => { _pool = null; _poolPromise = null; });
      return _pool;
    })();
  }
  return _poolPromise;
}

async function query(sqlText) {
  const pool = await getPool();
  return pool.request().query(sqlText);
}

module.exports = { sql, query };
