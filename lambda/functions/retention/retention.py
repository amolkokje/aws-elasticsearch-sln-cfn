
import boto3
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    ## read env vars to get configuration values

    deployment_type = os.environ['DEPLOYMENT']  # Acceptable values: ENG,PROD
    data_bucket_name = os.environ['DATA_BUCKET_NAME']
    retention_bucket_name = os.environ['S3_RETENTION_BUCKET_NAME']
    whitelisted_indices = [x.strip() for x in os.environ['WHITELISTED_INDICES'].split(',')]

    s3_retention_days = int(os.environ['S3_RETENTION_DAYS'])
    s3_eng_retention_days = int(os.environ['S3_ENG_RETENTION_DAYS'])
    cloudwatch_retention_days = int(os.environ['CLOUDWATCH_LOGS_RETENTION_DAYS'])

    logging.info('Whitelisted Indices=[{}], Retention: S3=[{}], Cloudwatch Logs=[{}]'.format(whitelisted_indices,
                                                                                             s3_retention_days,
                                                                                             cloudwatch_retention_days))
    logging.info('Retention period to move data from PROD Server to Archive=[{}]'.format(s3_retention_days))
    logging.info('Retention period to delete non-whitelisted data on ENG Server=[{}]'.format(s3_eng_retention_days))

    ## retention for S3 documents

    # datetime object, files before which are old and need to be purged
    datetime_eng_retention = (datetime.now() - timedelta(days=s3_eng_retention_days))
    datetime_s3_retention = (datetime.now() - timedelta(days=s3_retention_days))

    s3_client = boto3.client('s3')
    delete_objects_dict = dict()
    delete_objects_dict['Objects'] = list()
    s3_file_objects = s3_client.list_objects(Bucket=data_bucket_name)

    if 'Contents' in s3_file_objects.keys():  # run only if the bucket is not empty
        for file_object in s3_file_objects['Contents']:
            file_name = file_object['Key']
            name_split_list = file_name.split('_')
            # a valid file name will have format INDEX_UUID_DATE_TIME.json
            if len(name_split_list) != 4:
                logging.info('Invalid file name: [{}], hence delete'.format(file_name))
                # mark for delete
                delete_objects_dict['Objects'].append({'Key': file_name})
            else:
                index = name_split_list[0]
                datetime_file = file_object['LastModified'].replace(tzinfo=None)

                if index in whitelisted_indices:
                    if deployment_type == 'PROD':
                        if (datetime_file - datetime_s3_retention).total_seconds() < 0:
                            # copy to retention bucket
                            logging.info('Copy from {0}:{1} to {2}:{1}'.format(data_bucket_name, file_name,
                                                                               retention_bucket_name))
                            s3_client.copy({'Bucket': data_bucket_name, 'Key': file_name},
                                           retention_bucket_name, file_name)
                            # mark for delete
                            delete_objects_dict['Objects'].append({'Key': file_name})
                    else:
                        if (datetime_file - datetime_s3_retention).total_seconds() < 0:
                            delete_objects_dict['Objects'].append({'Key': file_name})

                else:
                    if deployment_type == 'PROD':
                        delete_objects_dict['Objects'].append({'Key': file_name})
                    else:
                        if (datetime_file - datetime_eng_retention).total_seconds() < 0:
                            delete_objects_dict['Objects'].append({'Key': file_name})

    # if there are objects found for purge, remove all of them in a single request to S3
    if len(delete_objects_dict['Objects']) > 0:
        logging.info('Delete total [{}] objects from '
                     'S3 Bucket: [{}], Objects: [{}]'.format(len(delete_objects_dict['Objects']),
                                                             data_bucket_name, delete_objects_dict['Objects']))
        s3_client.delete_objects(Bucket=data_bucket_name, Delete=delete_objects_dict)

    ## retention for cloudwatch log streams

    # epoch for the time, files older than which need to be purged
    epoch_cw_retention = int(
        ((datetime.now() - timedelta(days=cloudwatch_retention_days)) - datetime(1970, 1, 1)).total_seconds() * 1000)

    cw_client = boto3.client('logs')
    # Get all the log groups for the current stack
    cw_log_groups = cw_client.describe_log_groups(logGroupNamePrefix='/aws/lambda/{}'.format(data_bucket_name))[
        'logGroups']
    logging.info('Log Groups = [{}]'.format(cw_log_groups))
    for log_group in cw_log_groups:
        for log_stream in cw_client.describe_log_streams(logGroupName=log_group['logGroupName'])['logStreams']:
            # if file older than timestamp, delete
            if 'lastEventTimestamp' in log_stream.keys() and int(log_stream['lastEventTimestamp']) < epoch_cw_retention:
                logging.info('Delete Log Stream: [{}]'.format(log_stream['logStreamName']))
                cw_client.delete_log_stream(logGroupName=log_group['logGroupName'],
                                            logStreamName=log_stream['logStreamName'])
