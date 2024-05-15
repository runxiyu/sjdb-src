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
