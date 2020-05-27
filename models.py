
from database import cloudant_ext


class Document:
    """Metaclass to represent mapped Cloudant objects."""

    # TODO (rocco): figure out if this should be an abstract base class
    def __init__(self, _rev=None):
        """Construct a document.

        Sets the type attibute as the lowercase version of the
        most derived class name.
        """
        self.type = type(self).__name__.lower()
        self._rev = _rev

    def save(self):
        """Save the object to the Cloudant database."""
        doc = cloudant_ext.db[self._id]
        for k, v in vars(self):
            doc[k] = v
        doc.save()

    @classmethod
    def from_raw(cls, raw):
        """Construct an object from the raw dict-like Cloudant document."""
        del raw['type']
        return cls(**raw)

    @classmethod
    def get(cls, _id):
        """Get instance corresponding to ID.

        Args:
            _id: primary key/ID of object to be retrieved
        """
        doc = cloudant_ext.db[_id]
        return cls.from_raw(doc)

    @classmethod
    def all(cls):
        """Get all instances of specific type defined by derived class."""
        selector = {'type': {'$eq': cls.__name__.lower()}}
        users = cloudant_ext.db.get_query_result(selector)
        return [cls.from_raw(user) for user in users]


class User(Document):
    """Representation of a Segmund/Strava user."""

    def __init__(self,
                 _id,
                 name,
                 firstname,
                 lastname,
                 access_token,
                 expires_at,
                 refresh_token,
                 **kwargs):
        super().__init__(**kwargs)
        self._id = _id
        self.name = name
        self.firstname = firstname
        self.lastname = lastname
        self.access_token = access_token
        self.expires_at = expires_at
        self.refresh_token = refresh_token
