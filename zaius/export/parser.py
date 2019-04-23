# -*- coding: utf-8 -*-
"""
Parser for SQL subset that maps to operations supported by the
zaius export API.
"""

import parsy

# pylint: disable=R0914
def _query_parser():
    """
    Construct a parser for the subset of SQL that is applicable to the export API
    """

    whitespace = parsy.regex(r"\s*")
    lower = lambda x: x.lower()
    string = lambda x: parsy.string(x, lower)

    def lexeme(value):
        """A string or parser surrounded by whitespace"""

        if isinstance(value, str):
            value = string(value)
        return whitespace >> value << whitespace

    lparen = lexeme("(")
    rparen = lexeme(")")
    comma = lexeme(",")

    logop = lexeme(string("and") | string("or") | string("not"))
    eqop = lexeme(
        string("<=")
        | string(">=")
        | string("!=")
        | string("<>").result('!=')
        | string("<")
        | string(">")
        | string("=")
    )
    alphanum = parsy.regex(r"[a-zA-Z_][a-zA-Z0-9_]+")
    identifier = lexeme(alphanum)
    fieldpart = alphanum
    dot = parsy.string(".")
    field = lexeme(fieldpart.sep_by(dot)).map(".".join).desc("field")
    string_part = parsy.regex(r"[^\'\\]+")
    string_esc = string("\\") >> (string("\\") | string("'"))
    quoted = lexeme(
        string("'") >> (string_part | string_esc).many().concat() << parsy.string("'")
    ).desc("string")
    floatnum = lexeme(parsy.regex(r"-?(0|[1-9][0-9]*)([.][0-9]+)")).map(float)
    intnum = lexeme(parsy.regex(r"-?(0|[1-9][0-9]*)")).map(int)
    value = (quoted | floatnum | intnum).desc("value")
    filter_exp = (
        parsy.seq(field, eqop, value)
        .map(lambda x: dict(zip(["field", "operator", "value"], x)))
        .desc("filter")
    )

    @parsy.generate
    def where_expression_part():
        parser = quoted_where_expression | filter_exp
        result = yield parser
        return result

    def compound_result(args):
        first, rest = args[0], args[1]
        rest0 = rest[0]
        if len(rest) == 1:
            return {rest0[0]: [first, rest0[1]]}

        return {rest0[0]: [first, compound_result([rest0[1], rest[1:]])]}

    @parsy.generate
    def where_expression():
        first = yield where_expression_part
        rest = yield parsy.seq(logop, where_expression).many()
        if rest:
            return compound_result([first, rest])
        return first

    quoted_where_expression = lparen >> where_expression << rparen

    select_kw = lexeme("select")
    from_kw = lexeme("from")
    where_kw = lexeme("where")
    fields = field.sep_by(comma)

    sort_order = lexeme(string("asc") | string("desc"))
    field_sort = parsy.seq(field, sort_order.optional())
    order_by_kw = lexeme(parsy.seq(string("order"), whitespace, string("by")))

    def query_result(args):
        select = {"fields": args[1], "object": args[3]}
        if args[4] is not None:
            select["filter"] = args[4][1]
        if args[5] is not None:
            select["sorts"] = []
            for sort in args[5][1]:
                sort_chunk = {"field": sort[0], "order": sort[1] or "asc"}
                select["sorts"].append(sort_chunk)

        return {"select": select}

    query = parsy.seq(
        select_kw,
        fields,
        from_kw,
        identifier,
        parsy.seq(where_kw, where_expression).optional(),
        parsy.seq(order_by_kw, field_sort.sep_by(comma)).optional(),
    ).map(query_result)
    return query


QUERY_PARSER = _query_parser()
