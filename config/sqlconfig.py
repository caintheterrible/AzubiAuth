import sqlite3
import threading
import queue
from functools import lru_cache
from contextlib import contextmanager
from pathlib import Path


# SQLite-specific configuration constants
DEFAULT_DB_PATH:str=':memory:'
DEFAULT_MIN_CONNECTIONS:int=3 # SQLite typically needs fewer connections
DEFAULT_MAX_CONNECTIONS:int=10
DEFAULT_TIMEOUT:float=30.0
DEFAULT_CHECK_SAME_THREAD:bool=False # Allows cross-thread usage
DEFAULT_ISOLATION_LEVEL=None # Autocommit mode off

# SQLite connection configuration
SQLite_CONFIG={
    'database':DEFAULT_DB_PATH,
    'min_connections':DEFAULT_MIN_CONNECTIONS,
    'max_connections':DEFAULT_MAX_CONNECTIONS,
    'timeout':DEFAULT_TIMEOUT,
    'check_same_thread':DEFAULT_CHECK_SAME_THREAD,
    'isolation_level':DEFAULT_ISOLATION_LEVEL,
    # SQlite-specific pragmas
    'pragmas':{
        'journal_mode':'WAL',
        'synchronous':'NORMAL',
        'cache_size':-64000, # 64MB cache
        'foreign_keys':'ON',
        'busy_timeout':30000,
    }
}

def create_sqlite_connection(db_path, **kwargs):
    """Create a raw SQLite connection with optimizations."""
    conn:sqlite3=sqlite3.connect(
        database=db_path,
        timeout=kwargs.get('timeout', DEFAULT_TIMEOUT),
        check_same_thread=kwargs.get('check_same_thread', DEFAULT_CHECK_SAME_THREAD),
        isolation_level=kwargs.get('isolation_level', DEFAULT_ISOLATION_LEVEL)
    )

    # Apply SQLite pragmas for performance
    pragmas=kwargs.get('pragmas', SQLite_CONFIG['pragmas'])
    cursor=conn.cursor()
    for pragma, value in pragmas.items():
        cursor.execute(f"PRAGMA {pragma} = {value}")
    cursor.close()

    return conn

def validate_sqlite_connection(conn):
    """Tests SQLite connection validity."""
    try:
        cursor=conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        return True
    except (sqlite3.Error, sqlite3.OperationalError):
        return False

def get_sqlite_pool(db_path, min_conn, max_conn):
    """Generate unique key for connection pool caching."""
    db_path_str= str(Path(db_path).resolve()) if db_path!=':memory:' else ':memory:'
    return f"sqlite_{db_path_str}_{min_conn}_{max_conn}"


@lru_cache(maxsize=32)
def create_sqlite_pool(db_path=DEFAULT_DB_PATH, min_connections=DEFAULT_MIN_CONNECTIONS, max_connections=DEFAULT_MAX_CONNECTIONS, **kwargs):
    """Create and cache SQLite connection pool instance."""
    pool_state={
        'available_connections':queue.Queue(maxsize=max_connections),
        'all_connections':set(),
        'connection_count':0,
        'lock':threading.RLock(),
        'db_path':db_path,
        'config':{**SQLite_CONFIG, **kwargs,
                  'min_connections':min_connections,
                  'max_connections':max_connections,
                  }
    }

    # Initialize minimum connections
    with pool_state['lock']:
        for _ in range(min_connections):
            if pool_state['connection_count']<max_connections:
                conn=create_sqlite_connection(db_path, **pool_state['config'])
                pool_state['available_connections'].put(conn)
                pool_state['all_connections'].add(conn)
                pool_state['connection_count']+=1

    return pool_state


def get_connection_from_sqlite_pool(pool_state):
    """Acquire connection from SQLite pool."""
    try:
        conn=pool_state['available_connections'].get(timeout=pool_state['config']['timeout'])

        if not validate_sqlite_connection(conn):
            remove_sqlite_connection(pool_state, conn)
            return get_connection_from_sqlite_pool(pool_state)

        return conn

    except queue.Empty:
        with pool_state['lock']:
            if pool_state['connection_count']<pool_state['config']['max_connections']:
                conn=create_sqlite_connection(pool_state['db_path'], **pool_state['config'])
                pool_state['all_connections'].add(conn)
                pool_state['connection_count']+=1
                return conn
            else:
                raise ConnectionError('SQLite pool exhausted')


def return_connection_to_sqlite_pool(pool_state, conn):
    """Returns connection to SQLite pool."""
    if conn in pool_state['all_connections']:
        if validate_sqlite_connection(conn):
            try:
                conn.rollback() # Reset transaction state
                pool_state['available_connections'].put(conn, block=False)
            except queue.Full:
                remove_sqlite_connection(pool_state, conn)
        else:
            remove_sqlite_connection(pool_state, conn)


def remove_sqlite_connection(pool_state, conn):
    """Remove dead connection from SQLite pool"""
    with pool_state['lock']:
        if conn in pool_state['all_connections']:
            pool_state['all_connections'].remove(conn)
            pool_state['connection_count'] -= 1
            try:
                conn.close()
            except:
                pass


@contextmanager
def sqlite_connection(db_path=DEFAULT_DB_PATH, **kwargs):
    """Context manager for SQLite connections."""
    pool_key_params=(db_path, kwargs.get('min_connections', DEFAULT_MIN_CONNECTIONS),
                     kwargs.get('max_connections', DEFAULT_MAX_CONNECTIONS))

    pool_state=create_sqlite_pool(*pool_key_params, **kwargs)
    conn=get_connection_from_sqlite_pool(pool_state)

    try:
        yield conn
    finally:
        return_connection_to_sqlite_pool(pool_state, conn)


def execute_sqlite_query(sql, params=None, db_path=DEFAULT_DB_PATH, **kwargs):
    """Execute SELECT query on SQLite."""
    with sqlite_connection(db_path, **kwargs) as conn:
        cursor=conn.cursor()
        try:
            cursor.execute(sql, params or ())
            columns=[desc[0] for desc in cursor.description] if cursor.description else []
            rows=cursor.fetchall()
            return {'columns':columns, 'data':rows}
        finally:
            cursor.close()

def execute_sqlite_command(sql, params=None, db_path=DEFAULT_DB_PATH, **kwargs):
    """Execute INSERT/UPDATE/DELETE on SQLite."""
    with sqlite_connection(db_path, **kwargs) as conn:
        cursor=conn.cursor()
        try:
            cursor.execute(sql, params or ())
            affected_rows=cursor.rowcount
            conn.commit()
            return affected_rows
        except Exception as exc:
            conn.rollback()
            raise exc
        finally:
            cursor.close()


def get_sqlite_pool_stats(db_path=DEFAULT_DB_PATH, **kwargs):
    """Get SQLite pool statistics."""
    pool_key_params=(db_path, kwargs.get('min_connections', DEFAULT_MIN_CONNECTIONS),
                     kwargs.get('max_connections', DEFAULT_MAX_CONNECTIONS))

    try:
        pool_state=create_sqlite_pool(*pool_key_params, **kwargs)
        return {
            'database_path':pool_state['db_path'],
            'total_connections':pool_state['connection_count'],
            'available_connections':pool_state['available_connections'].qsize(),
            'active_connections':pool_state['connection_count']-pool_state['available_connections'].qsize(),
            'max_connections':pool_state['config']['max_connections'],
            'min_connections':pool_state['config']['min_connections']
        }
    except:
        return {'error': 'Pool not initialized'}


# Export cached pool access
def get_cached_pools():
    """Return `lru_cache` info for monitoring."""
    return create_sqlite_pool.cache_info()

def clear_sqlite_pools():
    """Clear all cached pools."""
    create_sqlite_pool.cache.clear()


# Django DATABASES configuration helper
def get_sqlite_database_config(db_path, **pool_kwargs):
    """Generate Django DATABASES configuration for SQLite with pooling."""
    return {
        'ENGINE':'django.db.backends.sqlite3',
        'NAME':db_path,
        'OPTIONS':{
            'init_command': ';'.join([f"PRAGMA {k} = {v}" for k, v in SQLite_CONFIG['pragmas'].items()]),
        },
        # Custom pool configuration
        'POOL_CONFIG':{
            'db_path':db_path,
            **SQLite_CONFIG,
            **pool_kwargs,
        }
    }