import os
import urllib
import uuid
import boto3
import json
import logging
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# mapping for all indexes to be created. Ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/dynamic-field-mapping.html
# date_detection to detect date from string
# numeric_detection to detect number from string
INDEX_MAPPING = """
    {
        "mappings": {
            "date_detection": true,
            "numeric_detection": false,    
            "dynamic": "strict",            
            "properties": {
                "object_key":{
                    "type": "keyword"
                },
                "test_suite": {
                    "type": "keyword"
                },                    
                "test_time": {
                    "type": "float"
                },
                "timestamp":{
                    "type": "date"
                },
                "custom_data": {
                    "type": "object",
                    "dynamic": "true"
                }                                        
            }            
        }
    }
    """


def get_es_client():
    """
    method that authenticates with ES and returns a handle
    :return: ES client handle
    """
    # get cres from rols
    credentials = boto3.Session().get_credentials()
    # generate auth
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, os.environ['REGION'],
                       'es', session_token=credentials.token)
    # authenticate and generate client
    es_client = Elasticsearch(hosts=[{'host': os.environ['ES_ENDPOINT_HOST'],
                                      'port': int(os.environ['ES_ENDPOINT_PORT'])}],
                              http_auth=awsauth,
                              use_ssl=True,
                              verify_certs=True,
                              connection_class=RequestsHttpConnection)
    logging.info('ES Init Done! ES={}'.format(es_client))
    return es_client


def read_object(event):
    """
    read S3 data object and return the containing JSON
    :param event: lambda event
    :return: data in the S3 data object
    """
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    logging.info('Bucket = [{}], Key = [{}]'.format(bucket, key))

    # get data stream, and read the stream
    response = s3.get_object(Bucket=bucket, Key=key)
    response_body = response['Body'].read()

    # read text from the stream
    logging.info('Response Body = [{}]'.format(response_body))

    # convert the json string to dict
    object_data = json.loads(response_body)
    logging.info('Object Data = [{}]'.format(object_data))
    return object_data


def create_index(es, index_name, index_mapping):
    """
    create index with specified mapping
    :param es: ES client handle
    :param index_name: index name
    :param index_mapping: mapping for the index
    :return: None
    """
    resp = es.indices.create(index=index_name, body=index_mapping)
    logging.info('Create Index Response = [{}]'.format(resp))


def bulk_import_json_data(object_data, doc_type):
    """
    creates generator object for importing to ES
    :param object_data: object data read from S3 object
    :param doc_type: string containing type
    :return: generator
    """
    for test_id, test_data in object_data.iteritems():
        yield {
            "_index": test_data['index'],
            "_type": doc_type,
            "_id": uuid.uuid4(),  # must be unique ID - random number
            "_source": test_data['test_data']
        }


############################################
#### DEBUG ONLY
############################################

def dump_env_vars(event, context):
    """
    dump all the env vars, and other debug stuff. Not needed for production
    :param event: event to lambda
    :param context: context of lambda
    :return: None
    """
    logging.info('Environment Vars:')
    for k, v in os.environ.iteritems():
        print '{}: [{}]'.format(k, v)
    logging.info('Event={}'.format(event))
    logging.info('Context={}'.format(context))


############################################
#### MAIN
############################################

def lambda_handler(event, context):
    logging.info('---> INDEX <---')
    dump_env_vars(event, context)

    # init ES client
    es = get_es_client()

    # create index with default mapping for any indices specified in the s3 object file

    # read from s3 object
    object_data = read_object(event)
    indices_list = list(set([item['index'] for item in object_data.values()]))
    logging.info('Indices read from the S3 object = [{}]'.format(indices_list))

    existing_indices = es.indices.get_alias().keys()
    logging.info('Existing Indices = [{}]'.format(existing_indices))

    # create all indices with default mapping, if does not exist
    for index_name in indices_list:
        if index_name not in existing_indices:
            logging.info('Creating Index = [{}] with Mapping = [{}]'.format(index_name, INDEX_MAPPING))
            create_index(es, index_name, INDEX_MAPPING)

    # bulk import all
    logging.info('Bulk Import Data to ES')
    resp = helpers.bulk(es, bulk_import_json_data(object_data, '_doc'))
    logging.info('Bulk Import Response = [{}]'.format(resp))


if __name__ == '__main__':
    lambda_handler(None, None)
