import os
import urllib
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth


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
    print 'ES Init Done! ES={}'.format(es_client)
    return es_client


def get_index_key_from_object(event):
    """
    read the object name from lambda event and parse the name string to get index_name and object_key
    :param event: lambda function event
    :return: index name, object key strings
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    index_name, object_key, _, _ = key.split('_')
    print 'BUCKET={}, KEY={}, INDEX_NAME={}, OBJECT_KEY={}'.format(bucket, key, index_name, object_key)
    return index_name, object_key


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
    # dump_env_vars(event, context)

    # init ES client
    es = get_es_client()

    # get index name, object key from the S3 object file name
    index_name, object_key = get_index_key_from_object(event)

    # search for all docs with in the index having the specific object key
    search_results = es.search(index=index_name,
                               filter_path=["hits.hits._id"],  # get only the IDs of the objects
                               body={"query": {"match": {"object_key": object_key}}}
                               # get only the objects having the key
                               )
    print 'SEARCH RESULTS={}'.format(search_results)
    id_list = [item["_id"] for item in search_results["hits"]["hits"]]
    print 'ID LIST={}'.format(id_list)

    # delete all documents using IDs
    for id in id_list:
        print es.delete(index=index_name, id=id)


if __name__ == '__main__':
    lambda_handler(None, None)
