import json

from WrenchCL.ApiSuperClass import ApiSuperClass
from WrenchCL import wrench_logger
from WrenchCL import rdsInstance
from datetime import datetime

# https://patentsview.org/apis/api-endpoints/patentsbeta
# Alternative: https://patentsview.org/apis/api-endpoints/patents

"""
This is from the documentation
Usage Limits
Each application is allowed to make 45 requests/minute. If your application 
exceeds this limit, you will receive a “429 Too many Requests” response to 
your API query.

Query format
'q': {
    '_and': [
        {
            '_or' : [
                {"_text_any": {'patent_abstract': keywords_str1}},
                {"_text_any": {'patent_abstract': keywords_str2}},
                {"_text_any": {'patent_abstract': keywords_str3}},
            ]
        },
        {'_gte': {'patent_date': self.date_range['start_date']}},
        {'_lte': {'patent_date': self.date_range['end_date']}}
    ]
},

TODO: publication date - need to be using V1 of the APIs
      "pct_data": [
        {
          "application_kind": "keyword",
          "pct_102_date": "1976-01-06",
          "pct_371_date": "1976-01-06",
          "pct_doc_number": "keyword",
          "pct_doc_type": "keyword",
          "published_filed_date": "1976-01-06"
        }
      ],
      "us_related_documents": [
        {
          "published_country": "keyword",
          "related_doc_kind": "keyword",
          "related_doc_number": "keyword",
          "related_doc_published_date": "1976-01-06",
          "related_doc_sequence": 1,
          "related_doc_status": "keyword",
          "related_doc_type": "keyword",
          "wipo_kind": "keyword"
        }
      ],

"""


class PatentAPI(ApiSuperClass):
    # the API call requires a list of all fields to return - this is all of them
    format_fields = [
        'appcit_app_number',
        'appcit_category',
        'appcit_date',
        'appcit_kind',
        'appcit_sequence',
        'app_country',
        'app_date',
        'app_number',
        'app_type',
        'assignee_city',
        'assignee_country',
        'assignee_county',
        'assignee_county_fips',
        'assignee_first_name',
        'assignee_first_seen_date',
        'assignee_id',
        'assignee_last_name',
        'assignee_last_seen_date',
        'assignee_lastknown_city',
        'assignee_lastknown_country',
        'assignee_lastknown_latitude',
        'assignee_lastknown_location_id',
        'assignee_lastknown_longitude',
        'assignee_lastknown_state',
        'assignee_latitude',
        'assignee_location_id',
        'assignee_longitude',
        'assignee_organization',
        'assignee_sequence',
        'assignee_state',
        'assignee_state_fips',
        'assignee_total_num_inventors',
        'assignee_total_num_patents',
        'assignee_type',
        'cited_patent_category',
        'cited_patent_date',
        'cited_patent_kind',
        'cited_patent_number',
        'cited_patent_sequence',
        'cited_patent_title',
        'citedby_patent_category',
        'citedby_patent_date',
        'citedby_patent_kind',
        'citedby_patent_number',
        'citedby_patent_title',
        'cpc_category',
        'cpc_first_seen_date',
        'cpc_group_id',
        'cpc_group_title',
        'cpc_last_seen_date',
        'cpc_section_id',
        'cpc_sequence',
        'cpc_subgroup_id',
        'cpc_subgroup_title',
        'cpc_subsection_id',
        'cpc_subsection_title',
        'cpc_total_num_assignees',
        'cpc_total_num_inventors',
        'cpc_total_num_patents',
        'detail_desc_length',
        'examiner_first_name',
        'examiner_id',
        'examiner_last_name',
        'examiner_role',
        'examiner_group',
        'forprior_country',
        'forprior_date',
        'forprior_docnumber',
        'forprior_kind',
        'forprior_sequence',
        'govint_contract_award_number',
        'govint_org_id',
        'govint_org_level_one',
        'govint_org_level_two',
        'govint_org_level_three',
        'govint_org_name',
        'govint_raw_statement',
        'inventor_city',
        'inventor_country',
        'inventor_county',
        'inventor_county_fips',
        'inventor_first_name',
        'inventor_first_seen_date',
        'inventor_id',
        'inventor_last_name',
        'inventor_last_seen_date',
        'inventor_lastknown_city',
        'inventor_lastknown_country',
        'inventor_lastknown_latitude',
        'inventor_lastknown_location_id',
        'inventor_lastknown_longitude',
        'inventor_lastknown_state',
        'inventor_latitude',
        'inventor_location_id',
        'inventor_longitude',
        'inventor_sequence',
        'inventor_state',
        'inventor_state_fips',
        'inventor_total_num_patents',
        'ipc_action_date',
        'ipc_class',
        'ipc_classification_data_source',
        'ipc_classification_value',
        'ipc_first_seen_date',
        'ipc_last_seen_date',
        'ipc_main_group',
        'ipc_section',
        'ipc_sequence',
        'ipc_subclass',
        'ipc_subgroup',
        'ipc_symbol_position',
        'ipc_total_num_assignees',
        'ipc_total_num_inventors',
        'ipc_version_indicator',
        'lawyer_first_name',
        'lawyer_first_seen_date',
        'lawyer_id',
        'lawyer_last_name',
        'lawyer_last_seen_date',
        'lawyer_organization',
        'lawyer_sequence',
        'lawyer_total_num_assignees',
        'lawyer_total_num_inventors',
        'lawyer_total_num_patents',
        'nber_category_id',
        'nber_category_title',
        'nber_first_seen_date',
        'nber_last_seen_date',
        'nber_subcategory_id',
        'nber_subcategory_title',
        'nber_total_num_assignees',
        'nber_total_num_inventors',
        'nber_total_num_patents',
        'patent_abstract',
        'patent_average_processing_time',
        'patent_date',
        'patent_firstnamed_assignee_city',
        'patent_firstnamed_assignee_country',
        'patent_firstnamed_assignee_id',
        'patent_firstnamed_assignee_latitude',
        'patent_firstnamed_assignee_location_id',
        'patent_firstnamed_assignee_longitude',
        'patent_firstnamed_assignee_state',
        'patent_firstnamed_inventor_city',
        'patent_firstnamed_inventor_country',
        'patent_firstnamed_inventor_id',
        'patent_firstnamed_inventor_latitude',
        'patent_firstnamed_inventor_location_id',
        'patent_firstnamed_inventor_longitude',
        'patent_firstnamed_inventor_state',
        'patent_kind',
        'patent_num_cited_by_us_patents',
        'patent_num_claims',
        'patent_num_combined_citations',
        'patent_num_foreign_citations',
        'patent_num_us_application_citations',
        'patent_num_us_patent_citations',
        'patent_number',
        'patent_processing_time',
        'patent_title',
        'patent_type',
        'patent_year',
        'pct_102_date',
        'pct_371_date',
        'pct_date',
        'pct_docnumber',
        'pct_doctype',
        'pct_kind',
        'rawinventor_first_name',
        'rawinventor_last_name',
        'uspc_first_seen_date',
        'uspc_last_seen_date',
        'uspc_mainclass_id',
        'uspc_mainclass_title',
        'uspc_sequence',
        'uspc_subclass_id',
        'uspc_subclass_title',
        'uspc_total_num_assignees',
        'uspc_total_num_inventors',
        'uspc_total_num_patents',
        'wipo_field_id',
        'wipo_field_title',
        'wipo_sector_title',
        'wipo_sequence',
    ]

    def __init__(self, keywords, date_range):
        # super().__init__('https://search.patentsview.org/api/v1/patent', logger)  # this is newest API
        super().__init__('https://api.patentsview.org/patents/query')  # this is the legacy API

        self.keywords = keywords
        self.date_range = date_range
        self._api_key = ''

    def get_count(self):

        payload = {
            'q': {
                '_and': [
                    {
                        '_or': []
                    },
                    {'_gte': {'patent_date': self.date_range['start_date']}},
                    {'_lte': {'patent_date': self.date_range['end_date']}}
                ]
            },
            'f': [],  # Assuming empty will just return the count
            'o': {
                'per_page': 1
            }
        }

        # add keywords to the query
        for word in self.keywords:
            payload['q']['_and'][0]['_or'].append({"_text_phrase": {"patent_abstract": word}})

        # print(json.dumps(payload, indent=2))

        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': f'{self._api_key}'
        }

        # print(json.dumps(payload, indent=2))

        response = self._fetch_from_api(self.base_url, headers, payload)
        # print(json.dumps(response, indent=2))
        return response.get('total_patent_count') if response else 0

    def fetch_data(self, batch_size, last_record_unique_id=None):
        """
            last_record_unique_id: contains the page number to retrieve.  If None, then page 1
                                   is assumed.
        :return:
        """

        payload = {
            'q': {
                '_and': [
                    {
                        '_or': []
                    },
                    {'_gte': {'patent_date': self.date_range['start_date']}},
                    {'_lte': {'patent_date': self.date_range['end_date']}}
                ]
            },
            'f': self.format_fields,
            'o': {
                'per_page': batch_size
            }
        }

        # add keywords to the query
        for word in self.keywords:
            payload['q']['_and'][0]['_or'].append({"_text_phrase": {"patent_abstract": word}})

        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': f'{self._api_key}'
        }

        if last_record_unique_id:
            payload['o']['page'] = last_record_unique_id  # Assuming 'after' is used for pagination

        response = self._fetch_from_api(self.base_url, headers, payload)
        if response:
            # print(json.dumps(response, indent=2))
            return response, None, last_record_unique_id
        else:
            return None, None, None


class PatentProcessor(PatentAPI):
    def __init__(self, keywords, date_range):
        super().__init__(keywords, date_range)
        self.batch_size = 30
        self.process_patents()

    def process_patents(self):
        count = self.get_count()
        if count is not None:
            wrench_logger.info(
                f'Found {count} patents for keywords {self.keywords} between {self.date_range["start_date"]} and {self.date_range["end_date"]}.')
        else:
            wrench_logger.error('Failed to get the patent count.')

        rdsInstance.connect()

        for page in range(1, 10):
            data, last_record_sort_value, last_record_unique_id = self.fetch_data(self.batch_size, page)
            if data:
                wrench_logger.info(f'Fetched {data["count"]} patents in batch {page}.')
                wrench_logger.debug(
                    f'Last record sort value: {last_record_sort_value}, Last record unique ID: {last_record_unique_id}')

                for patent in data['patents']:
                    patent_data = self.process_patent(patent)
                    self.insert_patent_data(patent_data)
            else:
                wrench_logger.error('Failed to fetch the patent data.')

    def process_patent(self, patent):
        patent_id = patent['patent_number']
        patent_title = patent['patent_title']
        patent_description = patent['patent_abstract']
        filing_date = patent['applications'][0]['app_date'] or ''
        publication_date = patent['pct_data'][0]['pct_date'] or ''
        cpc_codes = ','.join(
            set(cpc['cpc_subgroup_id'] for cpc in patent.get('cpcs', []) if cpc['cpc_subgroup_id'])) or ''
        retrieval_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        inventors = [{'id': self.escape_special_characters(invent['inventor_id']),
                      'key_id': int(invent['inventor_key_id']),
                      'first': self.escape_special_characters(invent["inventor_first_name"]),
                      'last': self.escape_special_characters(invent["inventor_last_name"])} for invent in
                     patent['inventors']]


        json_dump = json.dumps(patent).replace("'", "''").replace("-", "\\-")

        return {
            'patent_id': patent_id,
            'patent_title': self.escape_special_characters(patent_title),
            'patent_description': self.escape_special_characters(patent_description),
            'filing_date': filing_date,
            'publication_date': publication_date,
            'cpc_codes': cpc_codes,
            'retrieval_date': retrieval_date,
            'inventors': inventors,
            'json_dump': self.escape_special_characters(json_dump)
        }

    def insert_patent_data(self, patent_data):
        sql = f'''
            INSERT into svs_patents (patent_id, patent_title, patent_description, filing_date, publication_date, cpc_code, retrieval_date, json_dump)
            SELECT '{patent_data["patent_id"]}', '{patent_data["patent_title"]}', '{patent_data["patent_description"]}', to_date('{patent_data["filing_date"]}','yyyy-mm-dd'), to_date('{patent_data["publication_date"]}','yyyy-mm-dd'), '{patent_data["cpc_codes"]}', to_timestamp('{patent_data["retrieval_date"]}','yyyy-mm-dd hh24:mi:ss'), '{json.dumps(patent_data["json_dump"])}'
            WHERE NOT EXISTS
            (
                SELECT patent_id FROM svs_patents
                WHERE patent_id = '{patent_data["patent_id"]}'
            );
        '''

        sql_results = rdsInstance.execute_query(sql)

        if sql_results == 'ERROR':
            wrench_logger.error(f'An Exception Occurred: Failed to execute SQL query for inserting Patent data. {sql_results}')
            wrench_logger.debug(f'Failed Query: {sql}')
            rdsInstance.close()
            rdsInstance.connect()

        for inventor in patent_data['inventors']:
            self.insert_inventor(inventor, patent_data["patent_id"])

    def insert_inventor(self, inventor, patent_id):
        sql = f'''
            INSERT INTO svs_inventors (inventor_id, first_name, last_name, external_id)
            SELECT {inventor['key_id']}, '{inventor['first']}', '{inventor['last']}', '{inventor['id']}'
            WHERE NOT EXISTS
            (
                SELECT inventor_id FROM svs_inventors
                WHERE inventor_id = {inventor['key_id']}
            );
        '''

        sql_results = rdsInstance.execute_query(sql)

        if sql_results == 'ERROR':
            wrench_logger.error(f'An Exception Occurred: Failed to execute SQL query for inserting Patent data. {sql_results}')
            wrench_logger.debug(f'Failed Query: {sql}')
            rdsInstance.close()
            rdsInstance.connect()

        self.link_inventor_to_patent(inventor['key_id'], patent_id)

    def link_inventor_to_patent(self, inventor_id, patent_id):
        sql = f'''
            INSERT INTO svs_relational_inventors_patents (patent_id, inventor_id)
            SELECT '{patent_id}', {inventor_id}
            WHERE NOT EXISTS
            (
                SELECT patent_id FROM svs_relational_inventors_patents
                WHERE patent_id = '{patent_id}' AND inventor_id = {inventor_id}
            );
        '''

        sql_results = rdsInstance.execute_query(sql)

        if sql_results == 'ERROR':
            wrench_logger.error(f'An Exception Occurred: Failed to execute SQL query for inserting Patent data. {sql_results}')
            wrench_logger.debug(f'Failed Query: {sql}')
            rdsInstance.close()
            rdsInstance.connect()

    @staticmethod
    def escape_special_characters(value):
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            # Escape single quotes, hyphens, and periods
            return value.replace("'", "''").replace("-", "\\-")
        else:
            return value


if __name__ == '__main__':
    keywords = ['machine learning', 'python']
    date_range = {'start_date': '2000-01-01', 'end_date': '2023-08-30'}  # Replace with your RDS instance setup
    processor = PatentProcessor(keywords, date_range)
