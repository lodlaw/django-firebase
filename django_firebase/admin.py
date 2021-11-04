import firebase_admin
from django.contrib import admin


class FirebaseAdmin(admin.ModelAdmin):
    """ Overrides the default Django admin with Firebase """

    def get_object(self, request, object_id, from_field=None):
        document = firebase_admin.firestore.client().collection(self.model.collection_name).document(object_id).get()
        return self.model.document_to_model(document)
