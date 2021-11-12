from django.db import models

from django_firebase.models import FirebaseModel


class Teacher(FirebaseModel):
    prod_collection_name = 'teacher'

    # on debug mode, this collection will be used
    test_collection_name = 'test_teacher'

    name = models.CharField(max_length=50)

    def generate_document_id(self):
        """ Generate a custom document id on firebase """
        return self.name


class Student(FirebaseModel):
    prod_collection_name = 'student'
    test_collection_name = 'test_student'

    teacher = models.ForeignKey(Teacher, db_column='teacher', blank=False, on_delete=models.CASCADE)


def queries():
    print(Student.objects.all())
    print(Teacher.objects.all())
