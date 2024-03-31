Because the `Office365-REST-Python-Client` library's email-sending API doesn't
expose the `ItemBody`'s `content_type` attribute and therefore doesn't allow a
program to change the `content_type`, you must patch `site-packages/office365/outlook/mail/item_body.py`:

```python
from office365.runtime.client_value import ClientValue


class ItemBody(ClientValue):
    """Represents properties of the body of an item, such as a message, event or group post."""

    def __init__(self, content=None, content_type="HTML"): # CHANGE THIS LINE
        """

        :param str content: The content of the item.
        :param str content_type: The type of the content. Possible values are text and html.
        """
        super(ItemBody, self).__init__()
        self.content = content
        self.contentType = content_type

    def __repr__(self):
        return self.content

```

There are probably methods involving monkey-patching that would be cleaner than
directly patching library code, but this is way too complex for me to understand.

A middle-ground would to be properly use venvs, and write a function that
automatically patches the venv.
