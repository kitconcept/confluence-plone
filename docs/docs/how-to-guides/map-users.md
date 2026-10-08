---
myst:
  html_meta:
    "description": "How to map Confluence users to the principals of a Plone site with confluence-plone."
    "property=og:description": "Map Confluence users to Plone principals"
    "property=og:title": "Map users | confluence-plone"
    "keywords": "confluence-plone, users, principals, mapping, LDAP"
---

(how-to-map-users)=

# Map users

Every author, commenter, and mention in the result is the id of a principal of the site.
`confluence-plone` does not create users, so these ids must match users that exist in the site, or will exist when the site connects to its user directory.

## Choose a strategy

When Confluence and the site share a user directory, a strategy is often enough.
Set it in the `[principals]` section of the settings.

`username`
: The Confluence user name. This is the default.

`email`
: The email address of the user.

`key`
: The internal Confluence user key. Useful only when the site uses the same ids.

## Add a mapping file

For the users the strategy gets wrong, write a CSV file with two columns.

```text
confluence,principal
jdoe,john.doe
anna@example.org,asmith
8a7f808a5e3c1b2d015e3c1b2f8e0001,jdoe
```

The `confluence` column matches a Confluence user key, user name, or email address, ignoring case.
The mapping file wins over the strategy.

```toml
[principals]
mapping_file = "users.csv"
```

## Check the result

Users that the strategy and the mapping file cannot resolve become the `default` principal.
After a conversion, `summary.json` lists them under `unmapped_users`, with the number of times each one appears, and the command prints how many there are.

`confluence-plone` cannot check that a principal exists in the site.
Before importing, compare the principals in the result with the users of the site.

## Related

- {ref}`concepts-mapping`
- {doc}`/reference/settings`
