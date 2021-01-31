import plugins.csrf as csrf
import plugins.ci as ci
import plugins.sqli as sqli

ALL_FUNCS = [csrf.check, ci.check, sqli.check]
