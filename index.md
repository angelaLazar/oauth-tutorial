The GitHub API allows applications to interface with GitHub to access user data, create/delete users, view repos and more. To access data via the GitHub API, your app must be given authorization. This tutorial will walk you through the steps of creating a simple Google App Engine(GAE) app which will gain authorization to interface with the GitHub API. The goal here is to get an **access_token** from GitHub which can then be used to make authorized requests.
 
Though this tutorial, uses GAE for a quick Python application setup, other Python web application frameworks should be similar.  For this tutorial you must also have a GitHub account where your new application can be registered.

## Creating a Python Application using Google App Engine

1. Before you can get started, you will need to [download the Python SDK for App Engine.](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python)

1. In your terminal, create a new directory to hold the project called oauth-tutorial.    
`mkdir oauth-tutorial`

1. Inside your new directory, create a new Python file to contain your handlers. Let’s first start with a simple handler to see that the application was setup correctly. Call the file **oauth-tutorial.py** 
    
     ```python
import webapp2

	class MainPage(webapp2.RequestHandler):
	    def get(self):
	    	self.reponse.headers['Content-Type'] = 'text/plain'
	    	self.response.write('Success!')

	app = webapp2.WSGIApplication([
	    ('/', MainPage),
	], debug=True)
    ```    
This script will respond with a “Success!” message.

1. Next before we can run the application we need to create a configuration file called **app.yaml**. Make sure to create this inside the oauth-tutorial directory.

    ```
version: 1
runtime: python27
api_version: 1
threadsafe: true

libraries:
- name: webapp2
  version: latest

handlers:
- url: /.*
  script: oauth-tutorial.app
    ```
The syntax of this file is YAML. This file states the application version number, the python runtime environment with its API version and that the application is thread-safe so it can safely handle multiple requests at once. 

1. Now that there is a request handler and configuration file, the application can now be run on the web server provided by the App Engine Python SDK.  

  From your directory that contains your oauth-tutorial/ directory, run this command which gets your web server running:
`dev_appserver.py oauth-tutorial/`  

  Then, from your browser, navigate to:
[http://localhost:8080/](http://localhost:8080/)  

  You should see the “Success!” message from the python file. This means everything is running correctly. 

## Register the application with GitHub

To have an application interface with the GitHub API, it first needs to be registered with GitHub to identify where the requests for authorization are coming from. GitHub identifies applications with a **client_id** and **client_secret** it uniquely assigns to each application.  

To register your application:

1. Open the form to register a new application [here](https://github.com/settings/applications/new).  
 
![](http://i.imgur.com/aUkxWwt.png)

1. For your **Application name**, enter what you would like your application to called, this does not need to be unique, this is the name the user will see when granting you the authorization. I named mine “GitHub OAuth Tutorial”

1. For your **Homepage URL**, right now we are still running our web server locally so enter: `http://localhost:8080
`  

  This can be changed later if you choose to host your application.

1. The **Application description** is an optional field you can use to provide further details about your application. Since this field is optional, let's leave it blank.

1. The **Authorization callback URL** is the last field, this is a URL that GitHub will make requests back to our application during the authorization process. We will need to create a handler in our **oauth-tutorial.py** file to handle these responses, which we will do later on. Let’s call this /callback, so for this field enter: `http://localhost:8080/callback`

1. Click the **Register Application** button and now your app is registered to talk to GitHub! You should see a Client ID and Client Secret.

## Getting the GitHub Authorization

Now that the application is registered, we need to put our new **client_id** and **client_secret** into our application to use in requests to GitHub. But we do not want these values in code that could be pushed up to GitHub, else other applications can use them to access our user's data. So one way to hide these values is to put them in a json file that will not be committed to GitHub.

1. Create a new json file in your oauth-tutorial directory, called **client_secrets.json**. Inside of it, put in your **client_id** and **client_secret** you got from registering your application.

    ```
{
        "client_id":"<your client_id>",
        "client_secret":"<your client_secret"
}
    ```  

1. Now we need to have our **oauth-tutorial.py** access these fields. To parse the json, we need to add the json library to our application. Add this as an import next to webapps:  
`import webapp2, json`

1. Next we can add in the code to grab those two fields. Under your imports, add:

    ```python
with open('client_secrets.json') as data_file:    
    data = json.load(data_file)

client_id = data["client_id"]
client_secret = data["client_secret"]
    ```

1. The next step to getting authorization to a user’s data is to have the user give permission for our app to read their data.  

  We can choose to ask the user for a specific type of access, such as for their profile info or gists. This is specified using scopes. See all the scopes the API supports [here](https://developer.github.com/v3/oauth/#scopes).  

  For our example, let’s just get the user’s email addresses. So we will set our **scope** to `user:email`.  

  Let’s put a link on our main webpage to GitHub, where a user can choose to authorize our app to read their email addresses.  

  Change your get method in the MainPage class to:

    ```python
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_PAGE_HTML)
    ```

1. Next create the **MAIN_PAGE_HTML** variable under your json parsing code to hold the HTML.

    ```python

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
    ```

  This will create a link that brings the user to GitHub to authorize the app to access their GitHub email. 
 
  ![](http://i.imgur.com/W0NxPjO.png)  

  If the user clicks **Authorize application**, then Github will call our callback URL (that we stated when we registered the app). But we need setup a handler for `/callback`.

1. Add a request handler for `/callback` after the default handler at the bottom of the page that will call a class named `Callback`

    ```python
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/callback', Callback),
], debug=True)
    ```

1. Now create the `Callback` class, after the `MainPage` class.  In it, we will need `def get(self):` method to handle the the GET request we will receive from GitHub which includes a **code** field and the **scope** for the type of access.  

  Let’s create the get method and get the **scope** and **code** field from the request:

   ```python
class Callback(webapp2.RequestHandler):
	def get(self):
		# From the GET response from GitHub you grab the code and scope
		code = self.request.get('code')
		scope = self.request.get('scope')
    ```

1. Now with this code, we have all the fields we need to construct a request for an **access_token** from GitHub! The **access_token** will then allow you to make requests to the API on behalf of the user. Now we need to put all of our fields together and construct our request to get the **access_token**. Let’s create a dictionary of the fields, put this after the previous line:

    ```python
auth_params = dict(client_id=client_id, client_secret=client_secret, code=code, scope=scope)
    ```
1. Next we need to construct our request to the API. Add these lines right after the previous:

    ```python
opener = build_opener(HTTPSHandler)
request = Request('https://github.com/login/oauth/access_token',data=_encode_params(auth_params))
    ```  

  This is where we build our request. Note the `_encode_params` method here, we need to take our dictionary and encode it for the request. Copy this method above your two existing classes:

    ```python
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
    ```

1. This will require importing some libraries. Let’s add all the libraries we will need:

    ```python
import webapp2
import re, os, time, base64, hashlib, urllib, urlparse, json

from urllib2 import build_opener, HTTPSHandler, Request, HTTPError
from urllib import quote as urlquote
    ```  

  Some of these we aren’t using yet but we will in the next steps.

1. Now we can make a request for the access token. Add this code to make a request right after where we build the request:

    ```python
		try:
		    response = opener.open(request, timeout=TIMEOUT)
		    access_token_response = urlparse.parse_qs(response.read())

		    if 'error' in access_token_response:
		        raise GitHubApiAuthError(access_token_response['error_description'][0])

		    # Now you have your access_token in access_token_response!    
		    access_token = access_token_response['access_token'][0]
		    self.response.write("<p>Success! access_token=%s</p>"%access_token)
		except HTTPError as e:
		    raise GitHubApiAuthError('HTTPError when getting access token from GitHub')
    ```  
  Also remember to add a TIMEOUT variable in the file:  
  `TIMEOUT=60`

  Everything should run successfully, but we need to do some error handling to make sure. If our request failed, then we  will get an `HTTPError`. Else this code will get the response from the request and the next line will see if there is an error in the response, if there is it will show the error. Else, we succeeded in getting our access token and a success message will print out. A successful response should look similar to this:  
  `access_token=e72e16c7e42f292c6912e7710c838347ae178b4a&scope=user%2Cgist&token_type=bearer`  
  
  Note in this example, we are printing out the **access_token**, make sure in practice to hide this value from the user.

1. Before you run this to get your **access_token**, we need to put in the class for `GitHubApiAuthError` mentioned above. Enter this class after your `CallBack` class:

    ```python
class GitHubApiAuthError(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)
    ```

1. Now you should be able to run the code by refreshing your [http://localhost:8080](http://localhost:8080) page.  

  With this **access_token**, you can now make authorized requests to GitHub! There are multiple [libraries](https://developer.github.com/libraries/) in several languages available to make the requests.  

  I hope this helped you to better understand OAuth with GitHub. If you have any issues, you can compare to my code [here](https://github.com/angelaLazar/oauth-tutorial).

### Reference Links:  

[GitHub API Reference](https://developer.github.com/v3/)  
[OAuth Reference](https://developer.github.com/v3/oauth/)  
[Google App Engine](https://cloud.google.com/appengine/docs)









































    
