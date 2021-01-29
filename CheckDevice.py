import plugins.sqli as sqli
import plugins.ci as ci
import plugins.domxss as domxss

ALL_FUNCS = [sqli.check, ci.check, domxss.check]
