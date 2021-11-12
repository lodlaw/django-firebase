# django-firebase

A proxy for Firebase and Django model. With this package, you can:

- Use Django models to connect to Firebase Cloud Storage.
- You can also use these models on the admin page do Firebase operation: creating a new record, viewing a record.

## Gotchas

- The Firebase schema must be strictly relational.
- Nested data structure is currently not supported.

## What can be used

### Admin page

- Listing all documents.
- Creating a new document.

### Supported Model Operations:

- Model.objects.get()
- Model.objects.filter()
- Model.objects.exists()
- Model.objects.count()
- Model.objects.all()

The filters can be applied to model are `==`.

### Supported Fields:

- All fields that are not relational.
- For relational fields: ForeignKey.

### Constraints

- Unique Constraints are supported.
- unique_together constraints are also supported.

## How to use?

- Make your model to be a subclass of `FirebaseModel`.
- A `prod_collection_name` and a `test_collection_name` are required. `prod_collection_name` will be used when
  Django `settings.DEBUG` is False and vice versa.

```py
from django.db import models

from django_firebase.models import FirebaseModel


class Teacher(FirebaseModel):
  prod_collection_name = 'teacher'
  test_collection_name = 'test_teacher'

  name = models.CharField(max_length=50)


class Student(FirebaseModel):
  prod_collection_name = 'student'
  test_collection_name = 'test_student'

  teacher = models.ForeignKey(Teacher, db_column='teacher', blank=False, on_delete=models.CASCADE)
```

