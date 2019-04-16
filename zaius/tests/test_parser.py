import unittest
import datetime

import parsy
from zaius.export.parser import QUERY_PARSER


class TestParser(unittest.TestCase):
    
    def test_queries_parse(self):
        # simplest valid query
        self.assertValid("""
            select ts
            from events
        """)
        
        # field names can be nested
        self.assertValid("""
            select customer.name
            from events
        """)
        
        # multiple fields are allowed
        self.assertValid("""
            select user_id, customer.name
            from events
        """)
        
        # results can be ordered
        self.assertValid("""
            select user_id
            from events
            order by ts
        """)
        
        # order can be controlled
        self.assertValid("""
            select user_id
            from events
            order by ts desc
        """)
        
        # results can be filtered
        self.assertValid("""
            select user_id
            from events
            where ts > {}
        """.format(datetime.date.today().strftime('%s')))
        
        # filters can be complex
        self.assertValid("""
            select user_id
            from events
            where 
                ts > {}
                and event_type = 'order'
                and action = 'purchase'
        """.format(datetime.date.today().strftime('%s')))
        
        # invalid queries
        
        # fields must be explicit
        self.assertInvalid("""
            select *
            from events
        """)
        
        # only one table in the from clause
        self.assertInvalid("""
            select user_id
            from events, customers
        """)
        
        # query keywords can only appear once
        self.assertInvalid("""
            select user_id
            select customer.name
            from events
        """)
        
        # something must be selected
        self.assertInvalid("""
            select
            from events
        """)

    def test_parse_output(self):
        # sorts and filters only appear when used in the query
        result = self.assertValid("""
            select user_id
            from events
        """)
        self.assertNotIn('sorts', result['select'])
        self.assertNotIn('filter', result['select'])
        
        result = self.assertValid("""
            select user_id
            from events
            order by ts
        """)
        self.assertIn('sorts', result['select'])
        self.assertNotIn('filter', result['select'])
        
        result = self.assertValid("""
            select user_id
            from events
            where ts > 0
        """)
        self.assertNotIn('sorts', result['select'])
        self.assertIn('filter', result['select'])
        
        # trivial filters work
        self.assertMatch('ts > 0', {'ts': 10})
        self.assertNoMatch('ts > 0', {'ts': -10})
        
        # compound filters work
        self.assertMatchLike(
            'ts > 0 and ts < 10',
            [{'ts': 0}, {'ts': 1}, {'ts': 9}, {'ts': 10}],
            [False, True, True, False]
        )
        
        self.assertMatchLike(
            "ts > 0 and ts < 10 and color = 'blue'",
            [
                {'ts': 1, 'color': 'red'},
                {'ts': 3, 'color': 'blue'},
                {'ts': 5, 'color': 'blue'},
                {'ts': 10, 'color': 'blue'}
            ],
            [False, True, True, False]
        )
        
    def assertValid(self, stmt):
        return QUERY_PARSER.parse(stmt)
    
    def assertInvalid(self, stmt):
        with self.assertRaises(parsy.ParseError):
            QUERY_PARSER.parse(stmt)
    
    def assertMatch(self, stmt, row):
        self.assertTrue(self.compileStatement(stmt)(row))
    
    def assertMatchLike(self, stmt, rows, target):
        fn = self.compileStatement(stmt)
        result = list(map(fn, rows))
        self.assertEqual(result, target)
    
    def assertMatchAll(self, stmt, rows):
        return self.assertMatchLike(stmt, rows, [True]*len(rows))
    
    def assertNoMatch(self, stmt, row):
        self.assertFalse(self.compileStatement(stmt)(row))
    
    def compileStatement(self, stmt):
        parsed = self.assertValid("select fake from fake where " + stmt)
        return self.compileFilter(parsed['select']['filter'])
    
    def compileFilter(self, filter_struct):
        if 'field' in filter_struct:
            return self.compileFilterTerm(filter_struct)
        elif 'and' in filter_struct:
            parts = list([self.compileFilter(part) for part in filter_struct['and']])
            return lambda row: all(map(lambda p: p(row), parts))
        elif 'or' in filter_struct:
            parts = list([self.compileFilter(part) for part in filter_struct['and']])
            return lambda row: any(map(lambda p: p(row), parts))
        else:
            raise ValueError('cannot compile {}'.format(filter_struct))
    
    def compileFilterTerm(self, filter_struct):
        field = filter_struct['field']
        value = filter_struct['value']
        
        return {
            '=': lambda row: row[field] == value,
            '>': lambda row: row[field] > value,
            '>=': lambda row: row[field] >= value,
            '<': lambda row: row[field] < value,
            '<=': lambda row: row[field] <= value,
            '!=': lambda row: row[field] != value,
        }[filter_struct['operator']]