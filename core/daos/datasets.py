# -*- coding: utf-8 -*-

import time
from core.models import DatasetI18n, Dataset, DatasetRevision, Category
from core.exceptions import SearchIndexNotFoundException
from core.lib.searchify import SearchifyIndex
from core import settings
from core.daos.resource import AbstractDatasetDBDAO
from core.builders.datasets import DatasetImplBuilderWrapper


class DatasetDBDAO(AbstractDatasetDBDAO):
    """ class for manage access to datasets' database tables """

    def get(self, language, dataset_id=None, dataset_revision_id=None):
        pass
        
    def query(self, account_id=None, language=None, page=0, itemsxpage=settings.PAGINATION_RESULTS_PER_PAGE,
          sort_by='-id', filters_dict=None, filter_name=None, exclude=None):
              
        pass

    def query_childs(self, dataset_id, language):
        """ Devuelve la jerarquia completa para medir el impacto """
        pass

    def create(self, dataset=None, user=None, collect_type='', impl_details=None, **fields):
        """create a new dataset if needed and a dataset_revision"""

        if dataset is None:
            # Create a new dataset (TITLE is for automatic GUID creation)
            dataset = Dataset.objects.create(user=user, type=collect_type, title=fields['title'])

        # meta_text = '{"field_values": [{"cust-dataid": "dataid-%s"}]}' % dataset.id
        if not fields.get('language', None):
            fields['language'] = user.language

        dataset_revision = DatasetRevision.objects.create(dataset=dataset,
                user_id=user.id, status=fields['status'],
                category=Category.objects.get(id=fields['category']), filename=fields['file_name'],
                end_point=fields['end_point'], impl_type=fields['impl_type'],
                impl_details=impl_details, size=fields['file_size'],
                license_url=fields['license_url'], spatial=fields['spatial'],
                frequency=fields['frequency'], mbox=fields['mbox'])

        DatasetI18n.objects.create(dataset_revision=dataset_revision,
            language=fields['language'], title=fields['title'],
            description=fields['description'], notes=fields['notes'])

        dataset_revision.add_tags(fields['tags'])
        dataset_revision.add_sources(fields['sources'])

        return dataset, dataset_revision

    def update(self, dataset_revision, changed_fields, **fields):
        builder = DatasetImplBuilderWrapper(changed_fields=changed_fields, **fields).builder

        # TODO: Fix that
        #if builder.has_changed(changed_fields):
        #    # Build impl_details if necessary
        fields['impl_details'] = builder.build()

        changed_fields.append('impl_details')

        dataset_revision.update(changed_fields, **fields)

        DatasetI18n.objects.get(dataset_revision=dataset_revision, language=fields['language']).update(changed_fields, **fields)

        dataset_revision.add_tags(fields['tags'])
        dataset_revision.add_sources(fields['sources'])

        return dataset_revision
        
class DatasetSearchDAOFactory():
    """ select Search engine"""
    
    def create(self):
        if settings.USE_SEARCHINDEX == 'searchify':
            self.search_dao = DatasetSearchifyDAO()
        else:
            raise SearchIndexNotFoundException()

        return self.search_dao
        
        
class DatasetSearchifyDAO():
    """ class for manage access to datasets' searchify documents """
    def __init__(self):

        self.search_index = SearchifyIndex()
        
    def add(self, dataset_revision, language):
        category = dataset_revision.category.categoryi18n_set.get(language=language)
        dataseti18n = DatasetI18n.objects.get(dataset_revision=dataset_revision, language=language)

        # DS uses GUID, but here doesn't exists. We use ID
        text = [dataseti18n.title, dataseti18n.description, dataset_revision.user.nick, str(dataset_revision.dataset.guid)]

        # datastream has a table for tags but seems unused. I define get_tags funcion for dataset.
        tags = dataset_revision.tagdataset_set.all().values_list('tag__name')        
        text.extend(tags)
        text = ' '.join(text)

        document = {
                'docid' : "DT::DATASET-ID-" + str(dataset_revision.dataset.id),
                'fields' :
                    {'type' : 'dt',
                     'dataset_id': dataset_revision.dataset.id,
                     'datasetrevision_id': dataset_revision.id,
                     'title': dataseti18n.title,
                     'text': text,
                     'description': dataseti18n.description,
                     'owner_nick' : dataset_revision.user.nick,
                     'tags' : ','.join(tags),
                     'account_id' : dataset_revision.dataset.user.account.id,
                     'parameters': "",
                     'timestamp': int(time.mktime(dataset_revision.created_at.timetuple())),
                     'end_point': dataset_revision.end_point,
                     'is_private': 0,
                    },
                'categories': {'id': unicode(category.id), 'name': category.name}
                }

        # Update dict with facets
        # try:
        #     document = add_facets_to_doc(self, dataset.user.account, document)
        # except Exception, e:
        #     logger.error("indexable_dict ERROR: [%s]" % str(e))

        # document['fields'].update(get_meta_data_dict(dataset.meta_text))

        self.search_index.indexit(document)
        
    def remove(self, dataset_revision):
        self.search_index.delete_documents(["DT::DATASET-ID-" + str(dataset_revision.dataset.id)])
