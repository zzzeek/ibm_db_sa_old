from sqlalchemy.dialects import registry

registry.register("ibm_db", "ibm_db_sa.ibm_db", "DB2Dialect_ibm_db")
registry.register("ibm_db.ibm_db", "ibm_db_sa.ibm_db", "DB2Dialect_ibm_db")
registry.register("ibm_db.pyodbc", "ibm_db_sa.pyodbc", "DB2Dialect_pyodbc")
registry.register("ibm_db.zxjdbc", "ibm_db_sa.zxjdbc", "DB2Dialect_zxjdbc")
registry.register("ibm_db.pyodbc400", "ibm_db_sa.pyodbc", "AS400Dialect_pyodbc")
registry.register("ibm_db.zxjdbc400", "ibm_db_sa.zxjdbc", "AS400Dialect_zxjdbc")

from sqlalchemy.testing import runner

runner.main()

