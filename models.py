
from database import cloudant_ext
import cloudant


class Document:
    """Metaclass to represent mapped Cloudant objects."""

    def __init__(self, _rev=None):
        """Construct a document.

        Sets the type attibute as the lowercase version of the
        most derived class name.
        """
        self.type = type(self).__name__.lower()
        self._rev = _rev

    def save(self):
        """Save the object to the Cloudant database, create if necessary."""
        if self.exists():
            doc = cloudant_ext.db[self._id]
            doc.update(vars(self))
            doc.save()
        else:
            doc = vars(self)
            del doc['_rev']
            cloudant_ext.db.create_document(doc)

    @classmethod
    def from_raw(cls, raw):
        """Construct an object from the raw dict-like Cloudant document."""
        del raw['type']
        return cls(**raw)

    @classmethod
    def get(cls, _id):
        """Get document corresponding to ID.

        Args:
            _id: primary key/ID of object to be retrieved
        """
        doc = cloudant_ext.db[_id]
        return cls.from_raw(doc)

    @classmethod
    def contains(cls, _id):
        """Return True if document with _id exists in DB.

        Args:
            _id: primary key/ID of object to be retrieved
        """
        return cloudant.document.Document(cloudant_ext.db, _id).exists()

    def exists(self):
        """Return True if this document exists in database."""
        return Document.contains(self._id)

    @classmethod
    def all(cls):
        """Get all documents of specific type defined by derived class."""
        selector = {'type': {'$eq': cls.__name__.lower()}}
        docs = cloudant_ext.db.get_query_result(selector)
        return [cls.from_raw(doc) for doc in docs]

    @classmethod
    def delete(cls, _id):
        """Delete document with _id if exists.

        Args:
            _id: primary key/ID of object to be deleted
        """
        if cls.contains(_id):
            cloudant_ext.db[_id].delete()


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
