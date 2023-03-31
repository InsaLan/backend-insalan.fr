# Langate Endpoint(s)

## Current State of Things

As it turns out, the [langate2000](https://github.com/Insalan/langate2000/) only
uses one API endpoint on [insalan.fr](https://www.insalan.fr/) to authenticate
users, and check that they've paid, and are registered for this year's
tournaments.

The exact endpoint is `/api/user/2me`.

HTTP authentication is used to provide the credentials entered by the player,
and the results are given as a JSON-encoded string in the likes of:

```json
{
	"user": {
		"username": "Lymkwi",
		"name": "Am\u00e9lie Gonzalez",
		"email": "lymkwi@vulpinecitrus.info"
	},
	"err": "registration_not_found",
	"tournament": null
}
```

Per the langate2000 documentation found in the `insalan_auth` module, this is
the template for a response provided by insalan.fr :
```json
{
	"user": {
		"username": username,
		"name": name,
		"email": email
	},
	"err":  "registration_not_found", (player not found)
			"no_paid_place", (player found but he has not paid)
			null, (player found and he has paid)
	"tournament": [
		{
			"shortname": (...),
			"game_name": (...),
			"team": (...),
			"manager": true / false,
			"has_paid": true / false
		}
	]
}
```
