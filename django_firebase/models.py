from django.conf import settings
from django.db import models
from django.db.models import sql, ForeignKey
from django.db.models.lookups import Exact
from django.forms.models import model_to_dict
from django.utils import timezone
from firebase_admin import firestore


class FirebaseQuery(sql.Query):
    """
    Overrides the default SQL query behaviour with Firebase
    """

    def get_count(self, using):
        """
        Gets the number of documents in a collection
        """
        return len(self.firebase_query.get())

    def has_results(self, using):
        return bool(self.get_count(using))

    @property
    def firebase_query(self):
        collection_ref = self.collection_reference

        for key, val in self.firebase_filters.items():
            collection_ref = collection_ref.where(key, '==', val)

        return collection_ref

    @property
    def firebase_filters(self):
        """
        Converts sql filters to firebase filters
        :return: A dictionary contains key and values of the filter
        """
        # only get the exact filters
        exact_filters = list(filter(lambda e: isinstance(e, Exact), self.where.children))

        # transform the sql filters to firebase filter
        filters = {}
        for exact_filter in exact_filters:
            filters[exact_filter.lhs.target.name] = exact_filter.rhs

        return filters

    @property
    def collection_reference(self):
        """
        Gets the firebase collection reference
        """
        return firestore.client().collection(self.model.get_collection_name())


class FirebaseQuerySet(models.QuerySet):
    """
    Overrides the default SQL queryset behaviour with Firebase
    """

    def __init__(self, model=None, using=None, hints=None, query=None):
        super().__init__(query=FirebaseQuery(model), model=model, using=using, hints=hints)

    def _clone(self):
        """
        Clones the queryset
        :return: A new queryset
        :rtype FirebaseQuerySet
        """
        c = super()._clone()
        c.query = self.query

        return c

    def exists(self):
        return super().exists()

    def get(self, id=None, *args, **kwargs):
        """
        Gets a Firebase instance
        :param id: the id of that firebase instance
        :return: the instance itself
        :rtype FirebaseModel
        """
        self._fetch_all()

        if id:
            kwargs['id'] = id

        for i in self._result_cache:
            i_dict = i.__dict__
            found = True

            for key, value in kwargs.items():
                try:
                    if not i_dict[key] == value:
                        found = False
                except KeyError:
                    if not i_dict[key + "_id"] == value:
                        found = False

            if found:
                return i

        raise self.model.DoesNotExist("Object does not exist")

    def _fetch_all(self):
        """
        Fetches all documents of a collection and then appends to the result cache
        :return:
        """
        documents = self.query.firebase_query

        # get the order of the query
        for order in self.query.order_by:
            # get the order direction
            direction = firestore.Query.DESCENDING
            if order[0] == '-':
                direction = firestore.Query.ASCENDING
                order = order[1:]

            # ignore primary key ordering
            if order == "pk":
                continue

            # start sorting
            documents = documents.order_by(order, direction=direction)

        self._result_cache = []
        for document in documents.get():
            self._result_cache.append(self.model.document_to_model(document))

    def iterator(self, chunk_size=2000):
        """
        Override the iterator behavior of a queryset
        Instead of returning a generator of the documents like how a queryset does, we return the documents right away
        """
        self._fetch_all()

        return self._result_cache

    def __getitem__(self, k):
        """
        Gets the first k documents from the collection
        :param k: number of documents to get
        :return: k documents of the collection
        :rtype google.cloud.firestore_v1.base_document.DocumentSnapshot[]
        """
        self._fetch_all()
        return self._result_cache[k]


class FirebaseModel(models.Model):
    # overrides the default queryset with a firebase queryset
    objects = FirebaseQuerySet.as_manager()

    # an id is compulsory here for Firebase
    id = models.CharField(max_length=50, primary_key=True, editable=False)

    # timestamp fields for firebase
    created = models.DateTimeField(blank=False, default=timezone.now)
    modified = models.DateTimeField(blank=False, default=timezone.now)

    def __init__(self, *args, **kwargs):
        super(FirebaseModel, self).__init__(*args, **kwargs)

        # validate if a collection name is provided
        if not getattr(self, 'prod_collection_name', None):
            raise AttributeError("prod_collection_name must be provided")
        if not getattr(self, 'test_collection_name', None):
            raise AttributeError("test_collection_name must be provided")

    def clean_fields(self, exclude=None):
        """
        Cleans Firebase fields
        The steps are:
        - Remove all foreign key fields (the developer is responsible for cleaning them)
        - Calling super to get the default clean_fields without the foreign key fields
        """
        exclude = []
        for f in self._meta.fields:
            if type(f) == ForeignKey:
                exclude.append(f.name)

        super().clean_fields(exclude=exclude)

    def _perform_unique_checks(self, unique_checks):
        """
        Overrides unique check behaviour with Firebase
        """
        errors = {}
        for model_class, check in unique_checks:

            # mapping between the field name to check for and the value of that field
            field_values = {}
            for field in check:
                # get the actual field value
                # if the field value is a model then get the id of that model
                field_value = getattr(self, field)
                if isinstance(field_value, FirebaseModel):
                    field_value = field_value.id

                field_values[field] = field_value

            try:
                self.__class__.objects.get(**field_values)
                errors.setdefault('__all__', []).append(self.unique_error_message(model_class, check))
            except self.DoesNotExist:
                pass

        return errors

    def save(self):
        """
        Overrides the default behaviour of models.Model
        :return: a Firebase model
        :rtype FirebaseModel
        """
        collection = firestore.client().collection(self.get_collection_name())

        document = collection.document(document_id=self.generate_document_id())

        json = model_to_dict(self)

        document.create(json)

        self.id = document.id

        return self

    def generate_document_id(self):
        """
        Generates a firebase document id
        :return: a document id
        :rtype str
        """
        return None

    @classmethod
    def document_to_model(cls, document):
        """
        Converts a firestore document snapshot to a Django firebase model
        :param document: a firebase document
        :type document: google.cloud.firestore_v1.base_document.DocumentSnapshot
        :return: a Django firebase model
        :rtype FirebaseModel
        """
        # get the field mappings from the firestore document to the django model
        # ex: notificationId -> notification_id
        field_mappings = {}
        for field in cls._meta.fields:
            map_to = getattr(field, 'attname')
            map_from = getattr(field, 'db_column')

            if map_from:
                field_mappings[map_from] = map_to

        document_data = document.to_dict()

        # transform the document with the field mapping
        for map_from, map_to in field_mappings.items():
            if map_from in document_data:
                value = document_data.get(map_from)
                del document_data[map_from]
                document_data[map_to] = value

        return cls(id=document.id, **document_data)

    @classmethod
    def get_collection_name(cls):
        """ Gets the actual collection name based on if the app is running on debug or not """
        if settings.DEBUG:
            return cls.test_collection_name

        return cls.prod_collection_name

    class Meta:
        abstract = True
        managed = False
