import webapp2
import re, os, time, base64, hashlib, urllib, json

from urllib2 import build_opener, HTTPSHandler, Request, HTTPError
from urllib import quote as urlquote

with open('client_secrets.json') as data_file:    
    data = json.load(data_file)

client_id= data["client_id"]
client_secret= data["client_secret"]

#Timeout for GitHub API Request
TIMEOUT=60

MAIN_PAGE_HTML = """\
<html>
  <head>
  </head>
  <body>
    <p>
      You can include a link or access point in your site that brings the user to GitHub to authorize
      your app to access their protected GitHub profile data. <br></br>

      Here is an example:<br>

      To authorize this site to access your GitHub email addresses 
      <a href="https://github.com/login/oauth/authorize?scope=user:email&client_id=%s">Click here</a></a>
    </p>
  </body>
</html>
""" %(client_id)

def _encode_params(kw):
    '''
    Encode parameters using utf-8 and join them together
    '''
    args = []
    for k, v in kw.items():
        try:
            qv = v.encode('utf-8') if isinstance(v, unicode) else str(v)
        except:
            qv = v
        args.append('%s=%s' % (k, urlquote(qv)))
    return '&'.join(args)


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_PAGE_HTML)

class Callback(webapp2.RequestHandler):
	def get(self):
		# From the GET response from GitHub you grab the code and scope
		code = self.request.get('code')
		scope = self.request.get('scope')

		auth_params = dict(client_id=client_id, client_secret=client_secret, code=code, scope=scope)

		opener = build_opener(HTTPSHandler)
		request = Request('https://github.com/login/oauth/access_token', data=_encode_params(auth_params))

		try:
		    response = opener.open(request, timeout=TIMEOUT)
		    access_token_response = response.read()
		    if 'error' in access_token_response:
		        raise ApiAuthError(str(access_token_response.error))
		    # Now you have your access_token in access_token_response!    
		    self.response.write("<p>Success! access_token received</p>")
		except HTTPError as e:
		    raise GitHubApiAuthError('HTTPError when getting access token from GitHub')


class ApiError(Exception):
    def __init__(self, url, request, response):
        super(ApiError, self).__init__(url)
        self.request = request
        self.response = response

class GitHubApiAuthError(ApiError):
    def __init__(self, msg):
        super(ApiAuthError, self).__init__(msg, None, None)
     
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/callback', Callback),
], debug=True)
