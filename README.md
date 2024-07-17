# fsi-sync
This app syncs students and staff from Edumate to Functional Solutions International (FSI). It is a one directional sync, and does not delete any users from FSI. It will only create or update them.

It requires API credentials for [Edumate](https://integrations.edumate.net/apidoc/#api-Authorization-getAuthorization) and [FSI](https://www.functionalsolutions.com.au/api_patron-sync), and the following environment variables set:
```
FSI_URL = 'https://school.functionalsolutions.com.au/Services/SSLIB_SER_PATRON_API.asmx/patron'
FSI_API_KEY = 'api-key'
FSI_API_SECRET = 'api-secret'
EDUMATE_URL = 'https://edumate.school.au/school/web/app.php/api'
EDUMATE_AUTH_URL = 'https://edumate.school.au/school/web/app.php/api/authorize'
EDUMATE_CLIENT_ID = 'client-id'
EDUMATE_CLIENT_SECRET = 'client-secret'
```
