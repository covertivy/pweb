import plugins.sqli as sqli
import plugins.domxss as domxss
import plugins.ci as ci

ALL_FUNCS = [sqli.check, domxss.check, ci.check]
