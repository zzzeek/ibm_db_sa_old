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
"""Support for IBM DB2 database

"""
import re
import datetime
from decimal import Decimal as _python_Decimal
from sqlalchemy import types as sa_types
from sqlalchemy import schema as sa_schema
from sqlalchemy import __version__ as __sa_version__
from sqlalchemy import log, processors
from sqlalchemy.sql import compiler
from sqlalchemy.engine import default
from sqlalchemy.types import TypeDecorator, Unicode

from sqlalchemy import Table, MetaData, Column
from sqlalchemy.engine import reflection
from sqlalchemy import sql, util

from . import reflection

# as documented from:
# http://publib.boulder.ibm.com/infocenter/db2luw/v9/index.jsp?topic=/com.ibm.db2.udb.doc/admin/r0001095.htm
RESERVED_WORDS = set(
   ['activate', 'disallow', 'locale', 'result', 'add', 'disconnect', 'localtime',
    'result_set_locator', 'after', 'distinct', 'localtimestamp', 'return', 'alias',
    'do', 'locator', 'returns', 'all', 'double', 'locators', 'revoke', 'allocate', 'drop',
    'lock', 'right', 'allow', 'dssize', 'lockmax', 'rollback', 'alter', 'dynamic',
    'locksize', 'routine', 'and', 'each', 'long', 'row', 'any', 'editproc', 'loop',
    'row_number', 'as', 'else', 'maintained', 'rownumber', 'asensitive', 'elseif',
    'materialized', 'rows', 'associate', 'enable', 'maxvalue', 'rowset', 'asutime',
    'encoding', 'microsecond', 'rrn', 'at', 'encryption', 'microseconds', 'run',
    'attributes', 'end', 'minute', 'savepoint', 'audit', 'end-exec', 'minutes', 'schema',
    'authorization', 'ending', 'minvalue', 'scratchpad', 'aux', 'erase', 'mode', 'scroll',
    'auxiliary', 'escape', 'modifies', 'search', 'before', 'every', 'month', 'second',
    'begin', 'except', 'months', 'seconds', 'between', 'exception', 'new', 'secqty',
    'binary', 'excluding', 'new_table', 'security', 'bufferpool', 'exclusive',
    'nextval', 'select', 'by', 'execute', 'no', 'sensitive', 'cache', 'exists', 'nocache',
    'sequence', 'call', 'exit', 'nocycle', 'session', 'called', 'explain', 'nodename',
    'session_user', 'capture', 'external', 'nodenumber', 'set', 'cardinality',
    'extract', 'nomaxvalue', 'signal', 'cascaded', 'fenced', 'nominvalue', 'simple',
    'case', 'fetch', 'none', 'some', 'cast', 'fieldproc', 'noorder', 'source', 'ccsid',
    'file', 'normalized', 'specific', 'char', 'final', 'not', 'sql', 'character', 'for',
    'null', 'sqlid', 'check', 'foreign', 'nulls', 'stacked', 'close', 'free', 'numparts',
    'standard', 'cluster', 'from', 'obid', 'start', 'collection', 'full', 'of', 'starting',
    'collid', 'function', 'old', 'statement', 'column', 'general', 'old_table', 'static',
    'comment', 'generated', 'on', 'stay', 'commit', 'get', 'open', 'stogroup', 'concat',
    'global', 'optimization', 'stores', 'condition', 'go', 'optimize', 'style', 'connect',
    'goto', 'option', 'substring', 'connection', 'grant', 'or', 'summary', 'constraint',
    'graphic', 'order', 'synonym', 'contains', 'group', 'out', 'sysfun', 'continue',
    'handler', 'outer', 'sysibm', 'count', 'hash', 'over', 'sysproc', 'count_big',
    'hashed_value', 'overriding', 'system', 'create', 'having', 'package',
    'system_user', 'cross', 'hint', 'padded', 'table', 'current', 'hold', 'pagesize',
    'tablespace', 'current_date', 'hour', 'parameter', 'then', 'current_lc_ctype',
    'hours', 'part', 'time', 'current_path', 'identity', 'partition', 'timestamp',
    'current_schema', 'if', 'partitioned', 'to', 'current_server', 'immediate',
    'partitioning', 'transaction', 'current_time', 'in', 'partitions', 'trigger',
    'current_timestamp', 'including', 'password', 'trim', 'current_timezone',
    'inclusive', 'path', 'type', 'current_user', 'increment', 'piecesize', 'undo',
    'cursor', 'index', 'plan', 'union', 'cycle', 'indicator', 'position', 'unique', 'data',
    'inherit', 'precision', 'until', 'database', 'inner', 'prepare', 'update',
    'datapartitionname', 'inout', 'prevval', 'usage', 'datapartitionnum',
    'insensitive', 'primary', 'user', 'date', 'insert', 'priqty', 'using', 'day',
    'integrity', 'privileges', 'validproc', 'days', 'intersect', 'procedure', 'value',
    'db2general', 'into', 'program', 'values', 'db2genrl', 'is', 'psid', 'variable',
    'db2sql', 'isobid', 'query', 'variant', 'dbinfo', 'isolation', 'queryno', 'vcat',
    'dbpartitionname', 'iterate', 'range', 'version', 'dbpartitionnum', 'jar', 'rank',
    'view', 'deallocate', 'java', 'read', 'volatile', 'declare', 'join', 'reads', 'volumes',
    'default', 'key', 'recovery', 'when', 'defaults', 'label', 'references', 'whenever',
    'definition', 'language', 'referencing', 'where', 'delete', 'lateral', 'refresh',
    'while', 'dense_rank', 'lc_ctype', 'release', 'with', 'denserank', 'leave', 'rename',
    'without', 'describe', 'left', 'repeat', 'wlm', 'descriptor', 'like', 'reset', 'write',
    'deterministic', 'linktype', 'resignal', 'xmlelement', 'diagnostics', 'local',
    'restart', 'year', 'disable', 'localdate', 'restrict', 'years', '', 'abs', 'grouping',
    'regr_intercept', 'are', 'int', 'regr_r2', 'array', 'integer', 'regr_slope',
    'asymmetric', 'intersection', 'regr_sxx', 'atomic', 'interval', 'regr_sxy', 'avg',
    'large', 'regr_syy', 'bigint', 'leading', 'rollup', 'blob', 'ln', 'scope', 'boolean',
    'lower', 'similar', 'both', 'match', 'smallint', 'ceil', 'max', 'specifictype',
    'ceiling', 'member', 'sqlexception', 'char_length', 'merge', 'sqlstate',
    'character_length', 'method', 'sqlwarning', 'clob', 'min', 'sqrt', 'coalesce', 'mod',
    'stddev_pop', 'collate', 'module', 'stddev_samp', 'collect', 'multiset',
    'submultiset', 'convert', 'national', 'sum', 'corr', 'natural', 'symmetric',
    'corresponding', 'nchar', 'tablesample', 'covar_pop', 'nclob', 'timezone_hour',
    'covar_samp', 'normalize', 'timezone_minute', 'cube', 'nullif', 'trailing',
    'cume_dist', 'numeric', 'translate', 'current_default_transform_group',
    'octet_length', 'translation', 'current_role', 'only', 'treat',
    'current_transform_group_for_type', 'overlaps', 'true', 'dec', 'overlay',
    'uescape', 'decimal', 'percent_rank', 'unknown', 'deref', 'percentile_cont',
    'unnest', 'element', 'percentile_disc', 'upper', 'exec', 'power', 'var_pop', 'exp',
    'real', 'var_samp', 'false', 'recursive', 'varchar', 'filter', 'ref', 'varying',
    'float', 'regr_avgx', 'width_bucket', 'floor', 'regr_avgy', 'window', 'fusion',
    'regr_count', 'within'])


class _IBM_Boolean(sa_types.Boolean):

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if value == False:
                return 0
            elif value == True:
                return 1
        return process

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if value == False:
                return '0'
            elif value == True:
                return '1'
        return process


class _IBM_DateTime(sa_types.DateTime):

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, datetime.datetime):
                value = datetime.datetime(value.year, value.month, value.day,
                         value.hour, value.minute, value.second, value.microsecond)
            elif isinstance(value, datetime.time):
                value = datetime.datetime(value.year, value.month, value.day, 0, 0, 0, 0)
            return value
        return process

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, datetime.date):
                value = datetime.datetime(value.year, value.month,
                                value.day, 0, 0, 0, 0)
            return str(value)
        return process

class _IBM_Date(sa_types.Date):


    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            if isinstance(value, datetime.datetime):
                value = datetime.date(value.year, value.month, value.day)
            return value
        return process

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            if isinstance(value, datetime.datetime):
                value = datetime.date(value.year, value.month, value.day)
            return str(value)
        return process

class GRAPHIC(sa_types.CHAR):
    __visit_name__ = "GRAPHIC"

class VARGRAPHIC(sa_types.UnicodeText):
    __visit_name__ = "VARGRAPHIC"


class XML(sa_types.Text):
    __visit_name__ = "XML"

# Module level dictionary maps standard SQLAlchemy types to IBM_DB data types.
# The dictionary uses the SQLAlchemy data types as key, and maps an IBM_DB type as its value
colspecs = {
    sa_types.Boolean: _IBM_Boolean,
    sa_types.DateTime: _IBM_DateTime,
    sa_types.Date: _IBM_Date,
# really ?
#    sa_types.Unicode: IBM_DBVARGRAPHIC
}


class IBM_DBTypeCompiler(compiler.GenericTypeCompiler):

  def visit_now_func(self, fn, **kw):
    return "CURRENT_TIMESTAMP"

  def visit_TIMESTAMP(self, type_):
    return "TIMESTAMP"

  def visit_DATE(self, type_):
    return "DATE"

  def visit_TIME(self, type_):
    return "TIME"

  def visit_DATETIME(self, type_):
    return self.visit_TIMESTAMP(type_)

  def visit_SMALLINT(self, type_):
    return "SMALLINT"

  def visit_INT(self, type_):
    return "INT"

  def visit_BIGINT(self, type_):
    return "BIGINT"

  def visit_FLOAT(self, type_):
    return "REAL"

  def visit_XML(self, type_):
    return "XML"

  def visit_CLOB(self, type_):
    return "CLOB"

  def visit_BLOB(self, type_):
    return "BLOB(1M)" if type_.length in (None, 0) else \
        "BLOB(%(length)s)" % {'length' : type_.length}

  def visit_DBCLOB(self, type_):
    return "DBCLOB(1M)" if type_.length in (None, 0) else \
        "DBCLOB(%(length)s)" % {'length' : type_.length}

  def visit_VARCHAR(self, type_):
    if self.dialect.supports_char_length:
      return "LONG VARCHAR" if type_.length in (None, 0) else \
        "VARCHAR(%(length)s)" % {'length' : type_.length}
    else:
      return "LONG VARCHAR"

  def visit_VARGRAPHIC(self, type_):
    if self.dialect.supports_char_length:
      return "LONG VARGRAPHIC" if type_.length in (None, 0) else \
        "VARGRAPHIC(%(length)s)" % {'length' : type_.length}
    else:
      return "LONG VARGRAPHIC"

  def visit_CHAR(self, type_):
    return "CHAR" if type_.length in (None, 0) else \
        "CHAR(%(length)s)" % {'length' : type_.length}

  def visit_GRAPHIC(self, type_):
    return "GRAPHIC" if type_.length in (None, 0) else \
        "GRAPHIC(%(length)s)" % {'length' : type_.length}

  def visit_DECIMAL(self, type_):
    if not type_.precision:
      return "DECIMAL(31, 0)"
    elif not type_.scale:
      return "DECIMAL(%(precision)s, 0)" % {'precision': type_.precision}
    else:
      return "DECIMAL(%(precision)s, %(scale)s)" % {'precision': type_.precision, 'scale': type_.scale}


  def visit_numeric(self, type_):
    return self.visit_DECIMAL(type_)

  def visit_datetime(self, type_):
    return self.visit_TIMESTAMP(type_)

  def visit_date(self, type_):
    return self.visit_DATE(type_)

  def visit_time(self, type_):
    return self.visit_TIME(type_)

  def visit_integer(self, type_):
    return self.visit_INT(type_)

  def visit_boolean(self, type_):
    return self.visit_SMALLINT(type_)

  def visit_float(self, type_):
    return self.visit_FLOAT(type_)

  def visit_Float(self, type_):
    return self.visit_FLOAT(type_)

  def visit_unicode(self, type_):
    return self.visit_VARGRAPHIC(type_)

  def visit_unicode_text(self, type_):
    return self.visit_VARGRAPHIC(type_)

  def visit_string(self, type_):
    return self.visit_VARCHAR(type_)

  def visit_TEXT(self, type_):
    return self.visit_VARCHAR(type_)

  def visit_boolean(self, type_):
    return self.visit_SMALLINT(type_)

  def visit_large_binary(self, type_):
    return self.visit_BLOB(type_)


class IBM_DBCompiler(compiler.SQLCompiler):


    def visit_now_func(self, fn, **kw):
        return "CURRENT_TIMESTAMP"

    def limit_clause(self, select):
        if select._limit is not None:
            return " FETCH FIRST %s ROWS ONLY" % select._limit
        else:
            return ""

    def default_from(self):
        return  " FROM SYSIBM.SYSDUMMY1"   # DB2 uses SYSIBM.SYSDUMMY1 table for row count

    #def visit_function(self, func, result_map=None, **kwargs):
    # TODO: this is wrong but need to know what DB2 is expecting here
    #    if func.name.upper() == "LENGTH":
    #        return "LENGTH('%s')" % func.compile().params[func.name + '_1']
    #   else:
    #        return compiler.SQLCompiler.visit_function(self, func, **kwargs)

    def visit_typeclause(self, typeclause):
        type_ = typeclause.type.dialect_impl(self.dialect)
        if isinstance(type_, (sa_types.TIMESTAMP, sa_types.DECIMAL, \
            sa_types.DateTime, sa_types.Date, sa_types.Time)):
            return self.dialect.type_compiler.process(type_)
        else:
            return None

    #def visit_cast(self, cast, **kwargs):
    # TODO: don't know what this is about either
    #    type_ = self.process(cast.typeclause)
    #    if type_ is None:
    #       return self.process(cast.clause)
    #   return 'CAST(%s AS %s)' % (self.process(cast.clause), type_)

    def get_select_precolumns(self, select):
        if isinstance(select._distinct, basestring):
            return select._distinct.upper() + " "
        elif select._distinct:
            return "DISTINCT "
        else:
            return ""

    def visit_join(self, join, asfrom=False, **kwargs):
        # NOTE: this is the same method as that used in mysql/base.py
        # to render INNER JOIN
        return ''.join(
            (self.process(join.left, asfrom=True, **kwargs),
             (join.isouter and " LEFT OUTER JOIN " or " INNER JOIN "),
             self.process(join.right, asfrom=True, **kwargs),
             " ON ",
             self.process(join.onclause, **kwargs)))


class IBM_DBDDLCompiler(compiler.DDLCompiler):

  def get_column_specification(self, column, **kw):
    """Inputs:  Column object to be specified as a string
                Boolean indicating whether this is the first column of the primary key
       Returns: String, representing the column type and attributes,
                including primary key, default values, and whether or not it is nullable.
    """
    # column-definition: column-name:
    col_spec = [self.preparer.format_column(column)]
    # data-type:
    col_spec.append(column.type.dialect_impl(self.dialect).get_col_spec())

    # column-options: "NOT NULL"
    if not column.nullable or column.primary_key:
      col_spec.append('NOT NULL')

    # default-clause:
    default = self.get_column_default_string(column)
    if default is not None:
      col_spec.append('WITH DEFAULT')
      #default = default.lstrip("'").rstrip("'")
      col_spec.append(default)

    # generated-column-spec:

    # identity-options:
    # example:  id INT GENERATED BY DEFAULT AS IDENTITY (START WITH 1),
    if column.primary_key    and \
       column.autoincrement  and \
       isinstance(column.type, sa_types.Integer) and \
       not getattr(self, 'has_IDENTITY', False): # allowed only for a single PK
      col_spec.append('GENERATED BY DEFAULT')
      col_spec.append('AS IDENTITY')
      col_spec.append('(START WITH 1)')
      self.has_IDENTITY = True                   # flag the existence of identity PK

    column_spec = ' '.join(col_spec)
    return column_spec

  # Defines SQL statement to be executed after table creation
  def post_create_table(self, table):
    if hasattr( self , 'has_IDENTITY' ):    # remove identity PK flag once table is created
      del self.has_IDENTITY
    return ""

  def visit_drop_index(self, drop):
    index = drop.element
    return "\nDROP INDEX %s" % (
            self.preparer.quote(
                        self._index_identifier(drop.element.name),
                        drop.element.quote)
            )

  def visit_drop_constraint(self, drop):
    constraint = drop.element
    if isinstance(constraint, sa_schema.ForeignKeyConstraint):
        qual = "FOREIGN KEY "
        const = self.preparer.format_constraint(constraint)
    elif isinstance(constraint, sa_schema.PrimaryKeyConstraint):
        qual = "PRIMARY KEY "
        const = ""
    elif isinstance(constraint, sa_schema.UniqueConstraint):
        qual = "INDEX "
        const = self.preparer.format_constraint(constraint)
    else:
        qual = ""
        const = self.preparer.format_constraint(constraint)
    return "ALTER TABLE %s DROP %s%s" % \
                (self.preparer.format_table(constraint.table),
                qual, const)

class IBM_DBIdentifierPreparer(compiler.IdentifierPreparer):

  reserved_words = RESERVED_WORDS
  illegal_initial_characters = set(xrange(0, 10)).union(["_", "$"])

  def __init__(self, dialect, **kw):
    super(IBM_DBIdentifierPreparer, self).__init__(dialect, initial_quote='"', \
      final_quote='"')

  def _bindparam_requires_quotes(self, value):
    return (value.lower() in self.reserved_words
            or value[0] in self.illegal_initial_characters
            or not self.legal_characters.match(unicode(value))
            )


class IBM_DBExecutionContext(default.DefaultExecutionContext):
    def fire_sequence(self, seq, type_):
        return self._execute_scalar("SELECT NEXTVAL FOR " +
                    self.dialect.identifier_preparer.format_sequence(seq) +
                    " FROM SYSIBM.SYSDUMMY1", type_)

    def get_lastrowid(self):
      cursor = self.create_cursor()
      cursor.execute("SELECT IDENTITY_VAL_LOCAL() "+
          "FROM SYSIBM.SYSDUMMY1")
      lastrowid = cursor.fetchone()[0]
      cursor.close()
      if lastrowid is not None:
        lastrowid = int(lastrowid)
      return lastrowid

class IBM_DBDialect(default.DefaultDialect):

  name = 'ibm_db_sa'
  max_identifier_length = 128
  encoding = 'utf-8'
  default_paramstyle = 'named'
  colspecs = colspecs
  ischema_names = reflection.ischema_names
  supports_char_length = False
  supports_unicode_statements = False
  supports_unicode_binds = False
  returns_unicode_strings = False
  postfetch_lastrowid = True
  supports_sane_rowcount = False
  supports_sane_multi_rowcount = False
  supports_native_decimal = True
  preexecute_sequences = False
  supports_alter = True
  supports_sequences = True
  sequences_optional = True

  statement_compiler = IBM_DBCompiler
  ddl_compiler = IBM_DBDDLCompiler
  type_compiler = IBM_DBTypeCompiler
  preparer = IBM_DBIdentifierPreparer
  execution_ctx_cls = IBM_DBExecutionContext

  def __init__(self, use_ansiquotes=None, **kwargs):
    super(IBM_DBDialect, self).__init__(**kwargs)



  # Returns the converted SA adapter type for a given generic vendor type provided
  @classmethod
  def type_descriptor(self, typeobj):
    """ Inputs: generic type to be converted
        Returns: converted adapter type
    """
    return sa_types.adapt_type(typeobj, colspecs)

  def _compat_fetchall(self, rp, charset=None):
    return [_DecodingRowProxy(row, charset) for row in rp.fetchall()]

  def _compat_fetchone(self, rp, charset=None):
    return _DecodingRowProxy(rp.fetchone(), charset)

  def _compat_first(self, rp, charset=None):
    return _DecodingRowProxy(rp.first(), charset)

log.class_logger(IBM_DBDialect)

class _DecodingRowProxy(object):
  """Return unicode-decoded values based on type inspection.

  Smooth over data type issues (esp. with alpha driver versions) and
  normalize strings as Unicode regardless of user-configured driver
  encoding settings.

  """
  def __init__(self, rowproxy, charset):
    self.rowproxy = rowproxy
    self.charset = charset

  def __getitem__(self, index):
    item = self.rowproxy[index]
    if isinstance(item, _array):
        item = item.tostring()
    # Py2K
    if self.charset and isinstance(item, str):
    # end Py2K
    # Py3K
    #if self.charset and isinstance(item, bytes):
      return item.decode(self.charset)
    else:
      return item

  def __getattr__(self, attr):
    item = getattr(self.rowproxy, attr)
    if isinstance(item, _array):
      item = item.tostring()
    # Py2K
    if self.charset and isinstance(item, str):
    # end Py2K
    # Py3K
    #if self.charset and isinstance(item, bytes):
      return item.decode(self.charset)
    else:
      return item


