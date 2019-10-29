import os
import requests, urllib, uuid, json
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers

from requests_aws4auth import AWS4Auth
import boto3

# mapping for all indexes to be created
INDEX_MAPPING = """
    {
        "mappings": {            
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
                "kpi": {
                    "type": "object",
                    "dynamic": "true",
                    "properties": {
                        "val0": {
                            "type": "float"
                        },
                        "val1": {
                            "type": "float"
                        }
                    }
                }                                        
            }            
        }
    }
    """

def get_es_client():
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, os.environ['REGION'],
                       'es', session_token=credentials.token)
    es_client = Elasticsearch( hosts=[{'host': os.environ['ES_ENDPOINT_HOST'],
                                       'port': int(os.environ['ES_ENDPOINT_PORT'])}],
                               http_auth=awsauth,
                               use_ssl=True,
                               verify_certs=True,
                               connection_class=RequestsHttpConnection)
    print 'ES Init Done! ES={}'.format(es_client)
    return es_client

def read_object(event):
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    print 'BUCKET={}, KEY={}'.format(bucket, key)
    response = s3.get_object(Bucket=bucket, Key=key)
    response_body = response['Body']
    object_data = response_body.read(amt=1024)
    #print 'BEFORE: OBJECT_DATA_TYPE={}, OBJECT_DATA={}'.format(type(object_data), object_data)
    object_data = eval(object_data)  ## convert the json string to dict
    print 'AFTER: OBJECT_DATA_TYPE={}, OBJECT_DATA={}'.format(type(object_data), object_data)
    return object_data

def create_index(es, index_name, index_mapping):
    es.indices.create(index=index_name, body=index_mapping)


def bulk_import_json_data(object_data, doc_type):
    # TODO: use generator implementation
    bulk_data = []
    for test_id, test_data in object_data.iteritems():
        bulk_data.append(
            {
                "_index": test_data['index'],
                "_type": doc_type,
                "_id": uuid.uuid4(),  # must be unique ID - random number
                "_source": test_data['test_data']
            }
        )
    return bulk_data

############################################
#### DEBUG ONLY
############################################

def dump_env_vars(event, context):
    print 'ENVIRONMENT VARS:'
    for k, v in os.environ.iteritems():
        print '{}: [{}]'.format(k, v)

    print 'EVENT={}'.format(event)
    print 'CONTEXT={}'.format(context)


def lambda_handler(event, context):

    print '---> INDEX <---'
    #dump_env_vars(event, context)

    # init ES client
    es = get_es_client()

    # create index with default mapping for any indices specified in the s3 object file

    # read from s3 object
    object_data = read_object(event)
    indices_list = list(set([ item['index'] for item in object_data.values() ]))
    print 'INDICES={}'.format(indices_list)

    existing_indices = es.indices.get_alias().keys()
    print 'EXISTING_INDICES={}'.format(existing_indices)

    # create all indices with default mapping, if does not exist
    for index_name in indices_list:
        if index_name not in existing_indices:
            create_index(es, index_name, INDEX_MAPPING)

    # bulk import all
    print 'BULK IMPORT'
    bulk_data = bulk_import_json_data(object_data, '_doc')
    print helpers.bulk(es, bulk_data)


if __name__ == '__main__':
    lambda_handler(None, None)