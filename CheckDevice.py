import plugins.ci as ci
import plugins.csrf as csrf
import plugins.fi as fi
import plugins.xss as xss

ALL_FUNCS = [ci.check, csrf.check, fi.check, xss.check]
