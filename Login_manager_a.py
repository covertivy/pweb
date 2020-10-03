#!/usr/bin/python3
import mechanize
import http.cookiejar

cj = http.cookiejar.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)
br.open("http://192.168.56.102/dvwa/")

url_before = br.geturl()

br.select_form(nr=0)
br.form['username'] = 'admin'
br.form['password'] = 'admin'

br.submit()
url_after = br.geturl()

if url_before != url_after:
    print("success")
else:
    print("failure")
