# Gogs clients


## Getting client via accesstoken

### Create access token in gogs

Under user profile click your settings.
Click Applications, from there use generate new token to create your token.

#### User Access token
rest = j.clients.gogs.getRestClient('https://docs.greenitglobe.com', 443,
                                    accesstoken='myaccesstoken')

## Getting client via username, password
rest = j.clients.gogs.getRestClient('https://docs.greenitglobe.com', 443,
                                    'myusername', 'mypassword')
