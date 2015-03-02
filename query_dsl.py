import logging

from pyparsing import alphanums, delimitedList, Group, Literal, oneOf, \
    OneOrMore, Optional, Suppress, Word, ZeroOrMore

logger = logging.getLogger('grafanizer.query_dsl')

lp = Suppress('(')
rp = Suppress(')')
dot = Suppress('.')
colon = Suppress(':')

e_lit = Literal('entity')
c_lit = Literal('check')
m_lit = Literal('metric')
type_lit = Literal('type')

match_word = Word(alphanums + '!_-/\// ')

entity_attrs = oneOf('id label')
check_attrs = oneOf('id label')
metric_attrs = oneOf('name')

func = oneOf('startswith endswith contains full regex')

m_clause = Group(metric_attrs + colon + func + lp + match_word + rp)
m_exp = Suppress(m_lit) + lp + delimitedList(m_clause) + rp
m_section = OneOrMore(dot + m_exp)

c_clause = Group(check_attrs + colon + func + lp + match_word + rp)
c_exp = Suppress(c_lit) + lp + delimitedList(c_clause) + rp
c_section = OneOrMore(dot + c_exp)

e_attr_clause = Group(entity_attrs + colon + func + lp + match_word + rp)
e_type_clause = Group(type_lit + colon + match_word)
e_clause = (e_attr_clause | e_type_clause)
e_exp_empty = Suppress(e_lit) + lp + rp
e_exp = (Suppress(e_lit) + lp + delimitedList(e_clause) + rp) | e_exp_empty
e_section = e_exp + ZeroOrMore(dot + e_exp)

dsl = \
    Group(e_section) + \
    Optional(Group(c_section) + Group(m_section))


def validate_query(field, value, error):
    """
    Custom validator function that can be used by cerberus
    when validating data structures.

    Validates that a query string is parseable by dsl.

    @param field - String name of field being validated
    @param value - Value of field being validated
    @param error - Error object of the validator.

    """
    try:
        dsl.parseString(value, parseAll=True)
    except Exception as e:
        msg = "Clould not parse query: %s -- %s" % (value, str(e))
        error(field, msg)
