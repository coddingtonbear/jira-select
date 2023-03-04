import errno
import time
from typing import Any
from typing import Optional

from diskcache.core import EVICTION_POLICY
from diskcache.core import Cache


class MinimumRecencyCache(Cache):
    def get(
        self,
        key,
        default=None,
        read=False,
        expire_time=False,
        tag=False,
        retry=False,
        min_recency=2**32,
    ) -> Optional[Any]:
        """Retrieve value from cache. If `key` is missing, return `default`.

        .. note::

           This is lifted directly from the `diskcache.core.Cache.get` method
           in the superclass; just adding logic around a minimum recency
           restriction

        Raises :exc:`Timeout` error when database timeout occurs and `retry` is
        `False` (default).
        :param key: key for item
        :param default: value to return if key is missing (default None)
        :param bool read: if True, return file handle to value
            (default False)
        :param bool expire_time: if True, return expire_time in tuple
            (default False)
        :param bool tag: if True, return tag in tuple (default False)
        :param bool retry: retry if database timeout occurs (default False)
        :param int min_recency: return the value only if it is fewer than
            this number of seconds old.
        :return: value for item or default if key not found
        :raises Timeout: if database timeout occurs
        """
        db_key, raw = self._disk.put(key)
        update_column = EVICTION_POLICY[self.eviction_policy]["get"]
        select = (
            "SELECT rowid, expire_time, tag, mode, filename, value"
            " FROM Cache WHERE key = ? AND raw = ?"
            " AND (expire_time IS NULL OR expire_time > ?)"
            " AND (store_time >= ?) "
        )

        if expire_time and tag:
            default = (default, None, None)
        elif expire_time or tag:
            default = (default, None)

        if not self.statistics and update_column is None:
            # Fast path, no transaction necessary.

            rows = self._sql(
                select, (db_key, raw, time.time(), time.time() - min_recency)
            ).fetchall()

            if not rows:
                return default

            ((rowid, db_expire_time, db_tag, mode, filename, db_value),) = rows

            try:
                value = self._disk.fetch(mode, filename, db_value, read)
            except OSError:
                # Key was deleted before we could retrieve result.
                return default

        else:  # Slow path, transaction required.
            cache_hit = 'UPDATE Settings SET value = value + 1 WHERE key = "hits"'
            cache_miss = 'UPDATE Settings SET value = value + 1 WHERE key = "misses"'

            with self._transact(retry) as (sql, _):
                rows = sql(
                    select, (db_key, raw, time.time(), time.time() - min_recency)
                ).fetchall()

                if not rows:
                    if self.statistics:
                        sql(cache_miss)
                    return default

                ((rowid, db_expire_time, db_tag, mode, filename, db_value),) = rows

                try:
                    value = self._disk.fetch(mode, filename, db_value, read)
                except OSError as error:
                    if error.errno == errno.ENOENT:
                        # Key was deleted before we could retrieve result.
                        if self.statistics:
                            sql(cache_miss)
                        return default
                    else:
                        raise

                if self.statistics:
                    sql(cache_hit)

                now = time.time()
                update = "UPDATE Cache SET %s WHERE rowid = ?"

                if update_column is not None:
                    sql(update % update_column.format(now=now), (rowid,))

        if expire_time and tag:
            return (value, db_expire_time, db_tag)
        elif expire_time:
            return (value, db_expire_time)
        elif tag:
            return (value, db_tag)
        else:
            return value
