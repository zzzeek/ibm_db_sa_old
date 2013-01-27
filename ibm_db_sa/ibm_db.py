# +--------------------------------------------------------------------------+
# |  Licensed Materials - Property of IBM                                    |
# |                                                                          |
# | (C) Copyright IBM Corporation 2008.                                      |
# +--------------------------------------------------------------------------+
# | This module complies with SQLAlchemy 0.8 and is                          |
# | Licensed under the Apache License, Version 2.0 (the "License");          |
# | you may not use this file except in compliance with the License.         |
# | You may obtain a copy of the License at                                  |
# | http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable |
# | law or agreed to in writing, software distributed under the License is   |
# | distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY |
# | KIND, either express or implied. See the License for the specific        |
# | language governing permissions and limitations under the License.        |
# +--------------------------------------------------------------------------+
# | Authors: Alex Pitigoi, Abhigyan Agrawal                                  |
# | Contributors: Jaimy Azle, Mike Bayer                                     |
# | Version: 0.3.x                                                           |
# +--------------------------------------------------------------------------+

from .base import DB2ExecutionContext, DB2Dialect

class DB2ExecutionContext_ibm_db(DB2ExecutionContext):

    def get_lastrowid(self):
        return self.cursor.last_identity_val

class DB2Dialect_ibm_db(DB2Dialect):

    driver = 'ibm_db_sa'
    supports_unicode_statements = False
    supports_sane_rowcount = True
    supports_sane_multi_rowcount = False
    supports_native_decimal = False
    supports_char_length = True
    execution_ctx_cls = DB2ExecutionContext_ibm_db

    @classmethod
    def dbapi(cls):
        """ Returns: the underlying DBAPI driver module
        """
        import ibm_db_dbi as module
        return module

    def _get_server_version_info(self, connection):
        return connection.connection.server_info()

    def create_connect_args(self, url):
        conn_args = url.translate_connect_args()

        # DSN support through CLI configuration (../cfg/db2cli.ini),
        # while 2 connection attributes are mandatory: database alias
        # and UID (in support to current schema), all the other
        # connection attributes (protocol, hostname, servicename) are
        # provided through db2cli.ini database catalog entry. Example
        # 1: ibm_db_sa:///<database_alias>?UID=db2inst1 or Example 2:
        # ibm_db_sa:///?DSN=<database_alias>;UID=db2inst1
        if str(url).find('///') != -1:
            dsn, uid, pwd = '', '', ''
            if 'database' in conn_args and conn_args['database'] is not None:
                dsn = conn_args['database']
            else:
                if 'DSN' in url.query and url.query['DSN'] is not None:
                    dsn = url.query['DSN']
            if 'UID' in url.query and url.query['UID'] is not None:
                uid = url.query['UID']
            if 'PWD' in url.query and url.query['PWD'] is not None:
                pwd = url.query['PWD']
            return ((dsn, uid, pwd, '', ''), {})
        else:
            # Full URL string support for connection to remote data servers
            dsn_param = ['DRIVER={IBM DB2 ODBC DRIVER}']
            dsn_param.append('DATABASE=%s' % conn_args['database'])
            dsn_param.append('HOSTNAME=%s' % conn_args['host'])
            dsn_param.append('PORT=%s' % conn_args['port'])
            dsn_param.append('PROTOCOL=TCPIP')
            dsn_param.append('UID=%s' % conn_args['username'])
            dsn_param.append('PWD=%s' % conn_args['password'])
            dsn = ';'.join(dsn_param)
            dsn += ';'
            return ((dsn, conn_args['username'], '', '', ''), {})

    # Retrieves current schema for the specified connection object
    def _get_default_schema_name(self, connection):
        return self.normalize_name(connection.connection.get_current_schema())


    # Checks if the DB_API driver error indicates an invalid connection
    def is_disconnect(self, ex, connection, cursor):
        if isinstance(ex, (self.dbapi.ProgrammingError,
                                             self.dbapi.OperationalError)):
            return 'Connection is not active' in str(ex) or \
                        'connection is no longer active' in str(ex) or \
                        'Connection Resource cannot be found' in str(ex)
        else:
            return False

dialect = DB2Dialect_ibmdb
