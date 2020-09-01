import plugins.xss as xss
import plugins.sql as sql


def main(pages):
	xss.check(pages)
	sql.check(pages)

