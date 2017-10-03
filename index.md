The GitHub API allows applications to interface with GitHub to access user data, create/delete users, view repositories and more. To access data via the GitHub API, an app must be given authorization. This tutorial will go through the steps of creating a simple Google App Engine (GAE) app which will gain authorization to interface with the GitHub API. The goal here is to get an **access_token** from GitHub which can then be used to make authorized requests.
 
This tutorial uses GAE for a quick Python application setup but other Python web application frameworks should be similar.  For this tutorial you must have a GitHub account where your new application can be registered. 

## Create a Python Application using Google App Engine

1. Before getting started, you will need to [download the Python SDK for App Engine.](https://cloud.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python)

2. In terminal create a new directory to hold the project called **oauth-tutorial**:      
  `mkdir oauth-tutorial`

3. Here create a new Python file named **oauth-tutorial.py** to contain your handlers. Then add a simple handler to see that the application was setup correctly.
    
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

4. Before running the application create a configuration file called **app.yaml**. Make sure to create this inside the oauth-tutorial directory.

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

  This YAML file states the application version number, the python runtime environment with its API version and that the application is thread-safe. 

5. Now that there is a request handler and configuration file the application can be run on the web server provided by the App Engine Python SDK.  

  Inside the oauth-tutorial/ directory, run this command which gets your web server running:
  
  `dev_appserver.py oauth-tutorial/`  

  From your browser navigate to [http://localhost:8080/](http://localhost:8080/).  

  You should see the “Success!” message from the python file. This means everything is running correctly. 

## Register the application with GitHub

To have an application interface with the GitHub API it needs to be registered with GitHub to identify where the authorization requests are originating. GitHub identifies applications using a unique `client_id` and `client_secret` for each application.

Open the form to [register a new application](https://github.com/settings/applications/new).  
 
![](http://i.imgur.com/aUkxWwt.png)

**Application name**: this is what you would like your application to called, this field does not need to be unique. This is the name users see when granting authorization. It is named “GitHub OAuth Tutorial” in this tutorial.

**Homepage URL**: the web server is running locally so enter: `http://localhost:8080` (or the port number you are using)  

  This can be changed later if you choose to host your application.

**Application description**: an optional field you can use to provide further details about your application. It will currently will be left blank in this tutorial.

**Authorization callback URL**: the URL GitHub will use to make requests back to our application during the authorization request. We will need to create a handler in our **oauth-tutorial.py** file for this, completed in later steps. Let’s call this `/callback`, so for this field enter: `http://localhost:8080/callback`

Click the **Register application** button and now your app is registered to talk to GitHub! You should see a **Client ID** and **Client Secret**.

## Obtain GitHub Authorization

Now that the application is registered, we need to put the `client_id` and `client_secret` into the application to use in requests. These values need to be kept secret, one way to protect these values is to put them in a json file that will not be committed to GitHub.

1. Create a new json file in the `oauth-tutorial` directory, called **client_secrets.json**. Include the `client_id` and `client_secret` received from registering your application.

    ```
    {
            "client_id":"<your client_id>",
            "client_secret":"<your client_secret"
    }
    ```  

2. We need to have our **oauth-tutorial.py** access these fields. To parse the json we need to add the json library to our application. Add this as an import next to webapps:

    `import webapp2, json`

3. Add in the code to get these two fields. Under the imports, add:

    ```python
    with open('client_secrets.json') as data_file:    
        data = json.load(data_file)

    client_id = data["client_id"]
    client_secret = data["client_secret"]
    ```

4. Next the user must grant permission for the app to access their data.  

  We can choose to ask the user for a specific type of access, such as for their profile info or gists. This is specified using scopes. See all the scopes the GitHub API supports [here](https://developer.github.com/v3/oauth/#scopes).  

  For this tutorial let’s just get the user’s email addresses. So we will set our `scope` to `user:email`.
  
5. There needs to be a link for the user to grant or deny permissions. Let’s put a link on our main webpage to GitHub:

  Change your get method in the `MainPage` class to:

    ```python
    class MainPage(webapp2.RequestHandler):
        def get(self):
            self.response.write(MAIN_PAGE_HTML)
    ```

6. Create the `MAIN_PAGE_HTML` variable under your json parsing code to hold the HTML.

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

  If the user clicks **Authorize application** Github will make a request to the callback URL. But we need setup a handler for `/callback`.
  
## Handle the Response 

1. Add a request handler for `/callback` after the default handler at the bottom of the page that will call a class named `Callback`

```python
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/callback', Callback),
], debug=True)
```

2. Now create the `Callback` class, after the `MainPage` class.  In this we will need a `def get(self):` method to handle the the GET request we will receive from GitHub which includes a `code` field and `scope` for the type of access.  

   ```python
class Callback(webapp2.RequestHandler):
	def get(self):
		# From the GET response from GitHub you grab the code and scope
		code = self.request.get('code')
		scope = self.request.get('scope')
    ```

3. Now with this code we have all the fields we need to construct a request for a GitHub **access_token**! We need to put all of the fields together and construct the request to get the **access_token**. Create a dictionary after the previous line:

```python
auth_params = dict(client_id=client_id, client_secret=client_secret, code=code, scope=scope)
```

4. Next construct a request to the API. Add these lines right after the previous:

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

5. This will require importing some libraries. Let’s add all the libraries we will need:

    ```python
import webapp2
import re, os, time, base64, hashlib, urllib, urlparse, json

from urllib2 import build_opener, HTTPSHandler, Request, HTTPError
from urllib import quote as urlquote
    ```  

  Some of these we aren’t using yet but we will in the next steps.

6. Now we can make a request for the access token. Add this code to make a request right after where we build the request:

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
  Also remember to add a `TIMEOUT` variable in the file:  
  `TIMEOUT=60`

If we succeeded in getting our access token a success message will print out. A successful response should look similar to this:  
  `access_token=e72e16c7e42f292c6912e7710c838347ae178b4a&scope=user%2Cgist&token_type=bearer`  
  
  Note in this example we are printing out the **access_token**, make sure in practice to hide this value from the user!

7. Next is the error handling for unsuccessful requests. Before you run this to get your **access_token** we need to put in the class for `GitHubApiAuthError` . Enter this class after your `CallBack` class:

    ```python
class GitHubApiAuthError(Exception):
    def __init__(self, msg):
        super(Exception, self).__init__(msg)
    ```

8. Now you should be able to run the code by refreshing your [http://localhost:8080](http://localhost:8080) page.  

  With the **access_token** you can now make authorized requests to GitHub! There are multiple [libraries](https://developer.github.com/libraries/) in several languages available to make the requests.  

  I hope this helped you to better understand OAuth with GitHub. If you have any issues, you can compare to my code [here](https://github.com/angelaLazar/oauth-tutorial).

### Reference Links:  

[GitHub API Reference](https://developer.github.com/v3/)  
[OAuth Reference](https://developer.github.com/v3/oauth/)  
[Google App Engine](https://cloud.google.com/appengine/docs)









































    
