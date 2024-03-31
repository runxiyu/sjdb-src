# Configuring the Azure app registration

1. Head over to the [Azure portal](https://portal.azure.com) and add an
   app registration.
2. Select "Accounts in this organizational directory only"
3. Do not add a redirect URI at this stage
4. Create the application registration
5. In the "Authentication" tab, set "Allow public client flows" to YES
6. Still in the "Authentication" tab, select "Add a platform", select
   "Mobile and desktop applications", and put "`http://localhost`" in
   the custom redirect URI, and press "Configure".
7. Add the correct scopes (see `config.ini`)

The following sections should be present in your `manifest.json` after
you complete these settings, if you really want to verify them.
```json
{
	"allowPublicClient": true,
	"replyUrlsWithType": [
		{
			"url": "http://localhost",
			"type": "InstalledClient"
		}
	],
	"requiredResourceAccess": [
		{
			"resourceAppId": "00000003-0000-0000-c000-000000000000",
			"resourceAccess": [
				{
					"id": "2b9c4092-424d-4249-948d-b43879977640",
					"type": "Scope"
				},
				{
					"id": "024d486e-b451-40bb-833d-3e66d98c5c73",
					"type": "Scope"
				},
				{
					"id": "e383f46e-2787-4529-855e-0e479a3ffac0",
					"type": "Scope"
				},
				{
					"id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",
					"type": "Scope"
				}
			]
		}
	],
}
```
