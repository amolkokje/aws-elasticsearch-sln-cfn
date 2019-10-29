import os
import requests, urllib, uuid
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers

from requests_aws4auth import AWS4Auth
import boto3



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

def get_index_key_from_object(event):
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    print 'BUCKET={}, KEY={}'.format(bucket, key)
    index_name, object_key, _, _ = key.split('_')
    return index_name, object_key
    """
    response = s3.get_object(Bucket=bucket, Key=key)
    response_body = response['Body']
    object_data = response_body.read(amt=1024)
    print 'OBJECT_DATA={}'.format(object_data)
    return object_data
    """


############################################
#### DEBUG ONLY
############################################

def dump_env_vars(event, context):
    print 'ENVIRONMENT VARS:'
    for k, v in os.environ.iteritems():
        print '{}: [{}]'.format(k, v)

    print 'EVENT={}'.format(event)
    print 'CONTEXT={}'.format(context)


############################################
#### MAIN
############################################

def lambda_handler(event, context):

    print '---> DELETE <---'
    #dump_env_vars(event, context)

    # init ES client
    es = get_es_client()

    # get index name, object key from the S3 object file name
    index_name, object_key = get_index_key_from_object(event)
    print 'INDEX_NAME={}, OBJECT_KEY={}'.format(index_name, object_key)

    # search for all docs with in the index having the specific object key
    search_results = es.search(index=index_name,
                               filter_path=["hits.hits._id"],  # get only the IDs of the objects
                               body={"query": {"match": {"object_key": object_key}}}  # get only the objects having the key
                               )
    print 'SEARCH RESULTS={}'.format(search_results)
    id_list = [ item["_id"] for item in search_results["hits"]["hits"]]
    print 'ID LIST={}'.format(id_list)

    # delete all documents using IDs
    for id in id_list:
        print es.delete(index=index_name, id=id)


if __name__ == '__main__':
    lambda_handler(None, None)