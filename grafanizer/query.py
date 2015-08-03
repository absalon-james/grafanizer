import json
import logging
import os
import re

from cerberus import Validator

from query_dsl import dsl as query_dsl

from schema import entity_types

logger = logging.getLogger('grafanizer.query')

# Dictionary to save queries. Should be updated with functions from
# this module.
_QUERIES = {}


class QueryResult(object):
    """
    Models a query result

    """
    def __init__(self, entity):
        self.entity = entity
        self.check_tuples = []

    def add(self, check, metrics):
        """
        Adds a check and metrics pair

        @param check
        @param metrics - List of metrics

        """
        self.check_tuples.append((check, metrics))

    def __iter__(self):
        for c, metrics in self.check_tuples:
            for m in metrics:
                yield (self.entity, c, m)

    def __nonzero__(self):
        l = sum([len(metrics) for check, metrics in self.check_tuples])
        return True if l > 0 else False


class Query(object):
    """
    Models a query.

    """
    def __init__(self, string):
        """
        Inits the query

        @param string - String

        """
        self.tokens = query_dsl.parseString(string, parseAll=True)

    def query(self, entity):
        """
        Returns a tuple with the entity, check, metric if the query is
        successfull. Returns None otherwise

        @param entity - Entity model instance
        @returns - tuple | None

        """
        # Dont even bother with entities without checks
        if not len(entity.checks):
            return None

        result = None
        metric_qs = self.tokens[2] if len(self.tokens) >= 3 else []
        check_qs = self.tokens[1] if len(self.tokens) >= 2 else []
        entity_qs = self.tokens[0] if len(self.tokens) >= 1 else []

        # Qualify the entity
        for e_q in entity_qs:

            # Empty entity expression, continue
            if not e_q:
                continue

            # Check on type expression
            if e_q[0] == 'type':
                type_query = get_query(e_q[1])
                if not type_query:
                    logger.warn("Couldnt find query for %s" % e_q[1])
                    return None
                result = type_query.query(entity)
                if not result:
                    return None
                continue

            # Should be an attribute expression if not empty
            # and not type expression
            attr, func, value = e_q
            func = getattr(self, func)
            if not func(value, getattr(entity, attr)):
                return None

        # Return if we only have entity type qualifying statements
        # without check and metric qualifying statements.
        if result and not check_qs and not metric_qs:
            return result
        else:
            result = QueryResult(entity)

        # Qualify the checks
        checks = entity.checks
        for c_q in check_qs:
            if not c_q:
                continue
            attr, func, value = c_q
            func = getattr(self, func)
            checks = [c for c in checks if func(value, getattr(c, attr))]
        if not checks:
            return None

        # Qualify the metrics
        for c in checks:
            metrics = c.metrics
            for m_q in metric_qs:
                if not m_q:
                    continue
                attr, func, value = m_q
                func = getattr(self, func)
                metrics = [m for m in metrics if func(value, getattr(m, attr))]
            if metrics:
                result.add(c, metrics)
        return result

    def full(self, needle, haystack):
        """
        Returns whether or not needle is equal to haystack

        @param needle - String
        @param haystack - String
        @return - Boolean

        """
        return needle.lower() == haystack.lower()

    def startswith(self, needle, haystack):
        """
        Returns whether or haystack starts with needle

        @param needle - String
        @param haystack - String
        @return - Boolean

        """
        return haystack.lower().startswith(needle.lower())

    def endswith(self, needle, haystack):
        """
        Returns whether or not haystack endswith needle

        @param needle - String
        @param haystack - String
        @return - Boolean

        """
        return haystack.lower().endswith(needle.lower())

    def contains(self, needle, haystack):
        """
        Returns whether or not haystack contains needle

        @param needle - String
        @param haystack - String
        @return - Boolean

        """
        return needle.lower() in haystack.lower()

    def regex(self, needle, haystack):
        """
        Returns whether or not the regex needle matches haystack

        @param needle - String
        @param haystack - String
        @return - Boolean

        """
        regex = re.compile(needle)
        if regex.match(haystack.lower()):
            return True
        return False


def save_query(name, query):
    """
    Saves a query with key of name

    @param name - String
    @param query - Query instance

    """
    _QUERIES[name] = query


def get_query(name):
    """
    Returns a saved query.

    @param name - String
    @return - Query | None

    """
    return _QUERIES.get(name)


def load_entity_types(path):
    """
    Entity types are basically queries.
    If a query on an entity returns non None results,
    that entity is considered that type.

    Types are saved as queryies named by the type in the module variable
    _QUERIES.

    @param path - String - Path to look for entity_types or entity_types.json

    """
    files = ['entity_types.json', 'entity_types']
    files = [os.path.join(path, f) for f in files]
    v = Validator(entity_types)
    for f in files:
        if os.path.isfile(f):
            logger.debug("Checking for entity types in %s" % f)
            try:
                with open(f, 'r') as infile:
                    data = json.loads(infile.read())
                    if not v.validate(data):
                        logger.info("Invalid entity types:")
                        logger.info(v.errors)
                        continue
                    types = data['types']
                    for name, querystring in types.iteritems():
                        save_query(name, Query(querystring))
                        logger.debug("Created type: %s" % name)
            except ValueError:
                logger.info(
                    "Error loading entity types: File %s has invalid json" % f
                )
            except Exception:
                logger.exception("Error loading entity types:")
