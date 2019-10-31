import time
import os
import urllib
import boto3
import logging
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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


def get_index_key_from_object(event):
    """
    read the object name from lambda event and parse the name string to get index_name and object_key
    :param event: lambda function event
    :return: index name, object key strings
    """
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    index_name, object_key, _, _ = key.split('_')
    logging.info('Bucket = [{}], Key = [{}], '
                 'Index Name = [{}], Object Key = [{}]'.format(bucket, key, index_name, object_key))
    return index_name, object_key


def delete_loop(es, index_name, object_key):
    """
    Loops until all documents are deleted and until search no longer gives an output.
    Loop is required since ES Search API does not give all documents. The reason for this is not known, even after
    referencing issues and docs. So the workaround is to keep invoking the API, until it gives an empty response
    :param es: ES handle
    :param index_name: index name to look for
    :param object_key: object key to look for
    :return: None
    """
    while True:
        search_results = es.search(index=index_name,
                                   filter_path=["hits.hits._id"],  # get only the IDs of the objects
                                   body={"query": {"match": {"object_key": object_key}}}
                                   # get only the objects having the key
                                   )
        logging.info('Search results = [{}]'.format(search_results))
        try:
            docs = search_results['hits']['hits']
            if len(docs) == 0:
                logging.info('Done deleting all the docs!')
                return

            id_list = [item["_id"] for item in docs]
            logging.info('Doc ID List = [{}]'.format(id_list))
            for id in id_list:
                resp = es.delete(index=index_name, id=id)
                logging.info('Delete Response = [{}]'.format(resp))
        except Exception as ex:
            logging.info('No Search Hits, Document with ID not found (probably deleted), or hit an Unkown Exception. '
                         'Return! Exception = [{}]'.format(ex.message))
            return
        time.sleep(3)


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
    logging.info('---> DELETE <---')
    # dump_env_vars(event, context)

    # init ES client
    es = get_es_client()

    # get index name, object key from the S3 object file name
    index_name, object_key = get_index_key_from_object(event)

    # invoke the delete loop to remove the docs on the index with the specified object key
    delete_loop(es, index_name, object_key)


if __name__ == '__main__':
    lambda_handler(None, None)
