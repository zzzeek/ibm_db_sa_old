from sqlalchemy.dialects import registry

registry.register("ibm_db", "ibm_db.base", "DB2Dialect")
registry.register("ibm_db.ibm_db", "ibm_db.base", "DB2Dialect")
registry.register("ibm_db.pyodbc", "ibm_db.pyodbc", "DB2Dialect_pyodbc")
registry.register("ibm_db.zxjdbc", "ibm_db.zxjdbc", "DB2Dialect_zxjdbc")
registry.register("ibm_db.pyodbc400", "ibm_db.pyodbc", "AS400Dialect_pyodbc")
registry.register("ibm_db.zxjdbc400", "ibm_db.zxjdbc", "AS400Dialect_zxjdbc")

from sqlalchemy.testing import runner

runner.main()

