import plugins.bf as bf
import plugins.ci as ci
import plugins.csrf as csrf
import plugins.fi as fi
import plugins.sqli as sqli
import plugins.xss as xss

ALL_FUNCS = [bf.check, ci.check, csrf.check, fi.check, sqli.check, xss.check]
