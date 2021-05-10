import boto3
from boto3.dynamodb.conditions import Key, Attr
import ast
import datetime
from datetime import timedelta
from dateutil.tz import *
from dateutil.relativedelta import *
import re
import sys
import requests
import logging
import json
import os
import math
import random
import uuid

cpu2mem_weight = 0.5
pricing_dict = {}
region_table = {}
container_instance_ec2_mapping = {}


def get(table, region, cluster, service):
    """
    Scan the DynamoDB table to get all tasks in a service.
    Input - region, ECS ClusterARN and ECS ServiceName
    """
    resp = table.scan(
        FilterExpression=Attr('group').eq('service') &
        Attr('groupName').eq(service) &
        Attr('region').eq(region) &
        Attr('clusterArn').eq(cluster)
    )
    return(resp)


def ecs_getClusterArn(region, cluster):
    """ Given the ECS cluster name and the region, get the ECS ClusterARN. """
    client = boto3.client('ecs', region_name=region)
    response = client.describe_clusters(clusters=[cluster])

    logging.debug("ECS Cluster Details: %s", response)
    if len(response['clusters']) == 1:
        return (response['clusters'][0]['clusterArn'])
    else:
        return ''


def ec2_pricing(region, instance_type, tenancy, ostype):
    """
    Query AWS Pricing APIs to find cost of EC2 instance in the region.
    Given the paramters we use at input, we should get a UNIQUE result.
    TODO: In the current version, we only consider OnDemand price. If
    we start considering actual cost, we need to consider input from
    CUR on an hourly basis.
    """
    svc_code = 'AmazonEC2'
    client = boto3.client('pricing', region_name="us-east-1")
    response = client.get_products(ServiceCode=svc_code,
                                   Filters=[
                                       {'Type': 'TERM_MATCH', 'Field': 'location',
                                           'Value': "US EAST (Ohio)"},
                                       {'Type': 'TERM_MATCH', 'Field': 'servicecode',
                                           'Value': svc_code},
                                       {'Type': 'TERM_MATCH',
                                           'Field': 'preInstalledSw',   'Value': 'NA'},
                                       {'Type': 'TERM_MATCH', 'Field': 'tenancy',
                                           'Value': tenancy},
                                       {'Type': 'TERM_MATCH', 'Field': 'instanceType',
                                           'Value': instance_type},
                                       {'Type': 'TERM_MATCH',
                                           'Field': 'operatingSystem',  'Value': ostype}
                                   ],
                                   MaxResults=100
                                   )

    ret_list = []
    if 'PriceList' in response:
        for iter in response['PriceList']:
            ret_dict = {}
            mydict = ast.literal_eval(iter)
            ret_dict['memory'] = mydict['product']['attributes']['memory']
            ret_dict['vcpu'] = mydict['product']['attributes']['vcpu']
            ret_dict['instanceType'] = mydict['product']['attributes']['instanceType']
            ret_dict['operatingSystem'] = mydict['product']['attributes']['operatingSystem']
            ret_dict['normalizationSizeFactor'] = mydict['product']['attributes']['normalizationSizeFactor']

            mydict_terms = mydict['terms']['OnDemand'][list(
                mydict['terms']['OnDemand'].keys())[0]]
            ret_dict['unit'] = mydict_terms['priceDimensions'][list(
                mydict_terms['priceDimensions'].keys())[0]]['unit']
            ret_dict['pricePerUnit'] = mydict_terms['priceDimensions'][list(
                mydict_terms['priceDimensions'].keys())[0]]['pricePerUnit']
            ret_list.append(ret_dict)

    ec2_cpu = float(ret_list[0]['vcpu'])
    ec2_mem = float(re.findall("[+-]?\d+\.?\d*", ret_list[0]['memory'])[0])
    ec2_cost = float(ret_list[0]['pricePerUnit']['USD'])
    return(ec2_cpu, ec2_mem, ec2_cost)


def ecs_pricing(region):
    """
    Get Fargate Pricing in the region.
    """
    svc_code = 'AmazonECS'
    client = boto3.client('pricing', region_name="us-east-1")
    response = client.get_products(ServiceCode=svc_code,
                                   Filters=[
                                       {'Type': 'TERM_MATCH', 'Field': 'location',
                                           'Value': region},
                                       {'Type': 'TERM_MATCH', 'Field': 'servicecode',
                                           'Value': svc_code},
                                   ],
                                   MaxResults=100
                                   )

    cpu_cost = 0.0
    mem_cost = 0.0

    if 'PriceList' in response:
        for iter in response['PriceList']:
            mydict = ast.literal_eval(iter)
            mydict_terms = mydict['terms']['OnDemand'][list(
                mydict['terms']['OnDemand'].keys())[0]]
            mydict_price_dim = mydict_terms['priceDimensions'][list(
                mydict_terms['priceDimensions'].keys())[0]]
            if mydict_price_dim['description'].find('CPU') > -1:
                cpu_cost = mydict_price_dim['pricePerUnit']['USD']
            if mydict_price_dim['description'].find('Memory') > -1:
                mem_cost = mydict_price_dim['pricePerUnit']['USD']

    return(cpu_cost, mem_cost)


def get_datetime_start_end(now, month, days, hours):

    logging.debug(
        'In get_datetime_start_end(). month = %s, days = %s, hours = %s', month, days, hours)
    meter_end = now

    if month:
        # Will accept MM/YY and MM/YYYY format as input.
        regex = r"(?<![/\d])(?:0\d|[1][012])/(?:19|20)?\d{2}(?![/\d])"
        r = re.match(regex, month)
        if not r:
            print("Month provided doesn't look valid: %s" % (month))
            sys.exit(1)
        [m, y] = r.group().split('/')
        iy = 2000 + int(y) if int(y) <= 99 else int(y)
        im = int(m)

        meter_start = datetime.datetime(iy, im, 1, 0, 0, 0, 0, tzinfo=tzutc())
        meter_end = meter_start + relativedelta(months=1)

    if days:
        # Last N days = datetime(now) - timedelta (days = N)
        # Last N days could also be last N compelted days.
        # We use the former approach.
        if not days.isdigit():
            print("Duration provided is not a integer: %s" % (days))
            sys.exit(1)
        meter_start = meter_end - datetime.timedelta(days=int(days))
    if hours:
        if not hours.isdigit():
            print("Duration provided is not a integer" % (hours))
            sys.exit(1)
        meter_start = meter_end - datetime.timedelta(hours=int(hours))

    return (meter_start, meter_end)


def duration(startedAt, stoppedAt, startMeter, stopMeter, runTime, now):
    """
    Get the duration for which the task's cost needs to be calculated.
    This will vary depending on the CLI's input parameter (task lifetime,
    particular month, last N days etc.) and how long the task has run.
    """
    mRunTime = 0.0
    task_start = datetime.datetime.strptime(startedAt, '%Y-%m-%dT%H:%M:%S.%fZ')
    task_start = task_start.replace(tzinfo=datetime.timezone.utc)

    if (stoppedAt == 'STILL-RUNNING'):
        task_stop = now
    else:
        task_stop = datetime.datetime.strptime(
            stoppedAt, '%Y-%m-%dT%H:%M:%S.%fZ')
        task_stop = task_stop.replace(tzinfo=datetime.timezone.utc)

    # Return the complete task lifetime in seconds if metering duration is not provided at input.
    if not startMeter or not stopMeter:
        mRunTime = round((task_stop - task_start).total_seconds())
        logging.debug('In duration (task lifetime): mRunTime=%f',  mRunTime)
        return(mRunTime)

    if (task_start >= stopMeter) or (task_stop <= startMeter):
        mRunTime = 0.0
        logging.debug(
            'In duration (meter duration different OOB): mRunTime=%f',  mRunTime)
        return(mRunTime)

    calc_start = startMeter if (startMeter >= task_start) else task_start
    calc_stop = task_stop if (stopMeter >= task_stop) else stopMeter

    mRunTime = round((calc_stop - calc_start).total_seconds())
    logging.debug('In duration(), mRunTime = %f', mRunTime)
    return(mRunTime)


def ec2_cpu2mem_weights(mem, cpu):
    # Depending on the type of instance, we can make split cost beteen CPU and memory
    # disproportionately.
    global cpu2mem_weight
    return (cpu2mem_weight)


def cost_of_ec2task(region, cpu, memory, ostype, instanceType, runTime):
    """
    Get Cost in USD to run a ECS task where launchMode==EC2.
    The AWS Pricing API returns all costs in hours. runTime is in seconds.
    """
    global pricing_dict
    global region_table

    pricing_key = '_'.join(['ec2', region, instanceType, ostype])
    if pricing_key not in pricing_dict:
        # Workaround for DUBLIN, Shared Tenancy and Linux
        (ec2_cpu, ec2_mem, ec2_cost) = ec2_pricing(
            "US EAST (Ohio)", instanceType, 'Shared', 'Linux')
        pricing_dict[pricing_key] = {}
        # Number of CPUs on the EC2 instance
        pricing_dict[pricing_key]['cpu'] = ec2_cpu
        # GiB of memory on the EC2 instance
        pricing_dict[pricing_key]['memory'] = ec2_mem
        # Cost of EC2 instance (On-demand)
        pricing_dict[pricing_key]['cost'] = ec2_cost

    # Corner case: When no CPU is assigned to a ECS Task, cpushares = 0
    # Workaround: Assume a minimum cpushare, say 128 or 256 (0.25 vcpu is the minimum on Fargate).
    if cpu == '0':
        cpu = '128'

    # Split EC2 cost bewtween memory and weights
    ec2_cpu2mem = ec2_cpu2mem_weights(
        pricing_dict[pricing_key]['memory'], pricing_dict[pricing_key]['cpu'])
    cpu_charges = ((float(cpu)) / 1024.0 / pricing_dict[pricing_key]['cpu']) * (
        float(pricing_dict[pricing_key]['cost']) * ec2_cpu2mem) * (runTime/60.0/60.0)
    mem_charges = ((float(memory)) / 1024.0 / pricing_dict[pricing_key]['memory']) * (
        float(pricing_dict[pricing_key]['cost']) * (1.0 - ec2_cpu2mem)) * (runTime/60.0/60.0)

    logging.debug('In cost_of_ec2task: mem_charges=%f, cpu_charges=%f',
                  mem_charges, cpu_charges)
    return(mem_charges, cpu_charges)


def cost_of_fgtask(region, cpu, memory, ostype, runTime):
    global pricing_dict
    global region_table

    pricing_key = 'fargate_' + region
    if pricing_key not in pricing_dict:
        # First time. Updating Dictionary
        # Workarond - for DUBLIN (cpu_cost, mem_cost) = ecs_pricing(region)
        (cpu_cost, mem_cost) = ecs_pricing(region_table[region])
        pricing_dict[pricing_key] = {}
        pricing_dict[pricing_key]['cpu'] = cpu_cost
        pricing_dict[pricing_key]['memory'] = mem_cost

    mem_charges = ((float(memory)) / 1024.0) * \
        float(pricing_dict[pricing_key]['memory']) * (runTime/60.0/60.0)
    cpu_charges = ((float(cpu)) / 1024.0) * \
        float(pricing_dict[pricing_key]['cpu']) * (runTime/60.0/60.0)

    logging.debug('In cost_of_fgtask: mem_charges=%f, cpu_charges=%f',
                  mem_charges, cpu_charges)
    return(mem_charges, cpu_charges)


def cost_of_service(tasks, meter_start, meter_end, now):
    fargate_service_cpu_cost = 0.0
    fargate_service_mem_cost = 0.0
    ec2_service_cpu_cost = 0.0
    ec2_service_mem_cost = 0.0

    if 'Items' in tasks:
        for task in tasks['Items']:
            runTime = duration(task['startedAt'], task['stoppedAt'],
                               meter_start, meter_end, float(task['runTime']), now)

            logging.debug("In cost_of_service: runTime = %f seconds", runTime)
            if task['launchType'] == 'FARGATE':
                fargate_mem_charges, fargate_cpu_charges = cost_of_fgtask(
                    task['region'], task['cpu'], task['memory'], task['osType'], runTime)
                fargate_service_mem_cost += fargate_mem_charges
                fargate_service_cpu_cost += fargate_cpu_charges
            else:
                # EC2 Task
                ec2_mem_charges, ec2_cpu_charges = cost_of_ec2task(
                    task['region'], task['cpu'], task['memory'], task['osType'], task['instanceType'], runTime)
                ec2_service_mem_cost += ec2_mem_charges
                ec2_service_cpu_cost += ec2_cpu_charges

    return(fargate_service_cpu_cost, fargate_service_mem_cost, ec2_service_mem_cost, ec2_service_cpu_cost)


def get_ecs_service_bcs(cluster: str, ci_tag: str):
    ecs = boto3.client("ecs")

    services = ecs.list_services(cluster=cluster, launchType="EC2")[
        'serviceArns']

    service_details = []
    for service in services:
        service_details.append(ecs.describe_services(cluster=cluster, services=[service], include=['TAGS'])[
            'services'][0])

    business_contexts = {}

    for serv in service_details:
        try:
            if serv['status'] == "ACTIVE":
                for x in serv['tags']:
                    if x['key'] == ci_tag:
                        business_context = x['value']

                business_contexts[serv['serviceName']] = (
                    serv['serviceArn'], business_context)

        except KeyError:
            srv_name = serv['serviceName']
            print(f'{srv_name} has no tags')

    return business_contexts


def call_iapi(ldif: dict, host: str, token: str):

    auth_url = 'https://'+host+'/services/mtm/v1/oauth2/token'
    request_url = 'https://'+host + \
        '/services/integration-api/v1/synchronizationRuns?start=false&test=false'

    # token = os.environ['leanix_api_key']
    token = token

    response = requests.post(auth_url, auth=('apitoken', token),
                             data={'grant_type': 'client_credentials'})
    response.raise_for_status()
    access_token = response.json()['access_token']
    auth_header = 'Bearer ' + access_token
    header = {'Authorization': auth_header, "Content-Type": "application/json"}

    r = json.dumps(ldif)
    loaded_r = json.loads(r)
    r = requests.post(request_url, json=loaded_r, headers=header)
    jsonBody = r.json()

    id = jsonBody["id"]
    request_url_update = 'https://demo-eu.leanix.net/services/integration-api/v1/synchronizationRuns/' + \
        id+'/start?test=false'
    print(request_url_update)
    r = requests.post(request_url_update, json=ldif, headers=header)


def generateRandomNumber(digits):
    finalNumber = ""
    for i in range(digits // 16):
        finalNumber = finalNumber + \
            str(math.floor(random.random() * 10000000000000000))
    finalNumber = finalNumber + \
        str(math.floor(random.random() * (10 ** (digits % 16))))
    return int(finalNumber)


def get_cluster_names(region: str):
    ecs = boto3.client("ecs")
    clusters = ecs.list_clusters()['clusterArns']
    clusters_in_region = list()
    for cluster in clusters:
        if region in cluster.split(":"):
            cluster_name = cluster.split(":")[-1]
            cluster_name = cluster_name.split("/")[-1]
            clusters_in_region.append(cluster_name)
    return clusters_in_region


def get_secret():
    secret_name = os.environ.get('secret_name')
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=session.region_name,
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    if 'SecretString' in get_secret_value_response:
        text_secret_data = get_secret_value_response['SecretString']

    return text_secret_data


def putTasks(region, cluster, task):
    id_name = 'taskArn'
    task_id = task["taskArn"]
    new_record = {}

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table("ECSTaskStatus")
    saved_task = table.get_item(Key={id_name: task_id})

    # Look first to see if you have received this taskArn before.
    # If not,
    #   - you are getting a new task - i.e. the script is being run for the first time.
    #   - store its details in DDB
    # If yes,
    #   - the script is being run after the solution has been deployed.
    #   - dont do anything. quit.
    if "Item" in saved_task:
        print("Task: %s already in the DynamoDB table." % (task_id))
        return 1
    else:
        new_record["launchType"] = task["launchType"]
        new_record["region"] = region
        new_record["clusterArn"] = task["clusterArn"]
        new_record["cpu"] = task["cpu"]
        new_record["memory"] = task["memory"]
        if new_record["launchType"] == 'FARGATE':
            new_record["containerInstanceArn"] = 'INSTANCE_ID_UNKNOWN'
            (new_record['instanceType'], new_record['osType'], new_record['instanceId']) = (
                'INSTANCE_TYPE_UNKNOWN', 'linux', 'INSTANCE_ID_UNKNOWN')
        else:
            new_record["containerInstanceArn"] = task["containerInstanceArn"]
            (new_record['instanceType'], new_record['osType'], new_record['instanceId']) = getInstanceType(
                region, task['clusterArn'], task['containerInstanceArn'], task['launchType'])

        if ':' in task["group"]:
            new_record["group"], new_record["groupName"] = task["group"].split(
                ':')
        else:
            new_record["group"], new_record["groupName"] = 'taskgroup', task["group"]

        # Convert startedAt time to UTC from local timezone. The time returned from ecs_describe_tasks() will be in local TZ.
        startedAt = task["startedAt"].astimezone(tzutc())
        new_record["startedAt"] = datetime.datetime.strftime(
            startedAt, '%Y-%m-%dT%H:%M:%S.%fZ')
        new_record["taskArn"] = task_id
        new_record['stoppedAt'] = 'STILL-RUNNING'
        new_record['runTime'] = 0

        table.put_item(Item=new_record)
        return 0


def getInstanceType(region, cluster, instance, launchType):
    instanceType = 'INSTANCE_TYPE_UNKNOWN'
    osType = 'linux'
    instanceId = 'INSTANCE_ID_UNKNOWN'

    global container_instance_ec2_mapping

    # Shouldnt care about isntanceType if this is a FARGATE task
    if launchType == 'FARGATE':
        return (instanceType, osType, instanceId)

    if instance in container_instance_ec2_mapping:
        (instanceId, instanceType) = container_instance_ec2_mapping[instance]
        return (instanceType, osType, instanceId)

    ecs = boto3.client("ecs", region_name=region)
    try:
        result = ecs.describe_container_instances(
            cluster=cluster, containerInstances=[instance])
        if result and 'containerInstances' in result:
            attr_dict = result['containerInstances'][0]['attributes']

            instanceId = result['containerInstances'][0]["ec2InstanceId"]

            instance_type = [d['value']
                             for d in attr_dict if d['name'] == 'ecs.instance-type']
            if len(instance_type):
                # Return the instanceType. In addition, store this value in a DynamoDB table.
                instanceType = instance_type[0]

            os_type = [d['value']
                       for d in attr_dict if d['name'] == 'ecs.os-type']
            if len(os_type):
                # Return the osType. In addition, store this value in a DynamoDB table.
                osType = os_type[0]
        container_instance_ec2_mapping[instance] = (instanceId, instanceType)
        return (instanceType, osType, instanceId)
    except:
        # Try finding the instanceType in DynamoDB table
        return (instanceType, osType, instanceId)


def init_db(region: str):

    
    ecs = boto3.client("ecs", region_name=region)
    response = ecs.list_clusters()

    clusters = []
    if 'clusterArns' in response and response['clusterArns']:
        clusters = response['clusterArns']

    tasks = []
    for cluster in clusters:
        nextToken = ''
        while True:
            response = ecs.list_tasks(
                cluster=cluster, maxResults=100, nextToken=nextToken)
            tasks = tasks + [(cluster, taskArn)
                             for taskArn in response['taskArns']]
            if 'nextToken' in response and response['nextToken']:
                nextToken = response['nextToken']
            else:
                break

    for (cluster, task) in tasks:
        # Use range function to get maybe 10 tasks at a time.
        # taskDetails = ecs.describe_tasks(cluster=cluster, tasks=[task])

        taskDetails = ecs.describe_tasks(cluster=cluster, tasks=[task])

        # Get all tasks in the cluster and make an entry in DDB.
        tasks = putTasks(region, cluster, taskDetails['tasks'][0])

    db = boto3.resource('dynamodb')
    table = db.Table('initDB')

    table.put_item(
        Item={
            'id':uuid.uuid4().hex,
            'initialized':True,
            'date':datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }
    )

def lambda_handler(event, context):

    session = boto3.session.Session()
    region = session.region_name
    clusterList = get_cluster_names(region)

    
    

    for clustername in clusterList:

        # key = aws_name ; value = tag value from BC tag
        extracted_business_contexts = get_ecs_service_bcs(
            cluster=clustername, ci_tag="application")

        cpu2mem_weight = 0.5

        cluster = ecs_getClusterArn(region, clustername)
        if not cluster:
            logging.error("Cluster : %s Missing", clustername)
            sys.exit(1)

        now = datetime.datetime.now(tz=tzutc()) - timedelta(days=1)
        yesterday = datetime.datetime.now(
            tz=tzutc()) - datetime.timedelta(days=1)
        day_2 = datetime.datetime.now(tz=tzutc()) - datetime.timedelta(days=2)
        day_3 = datetime.datetime.now(tz=tzutc()) - datetime.timedelta(days=3)

        dates = [yesterday, day_2, day_3]

        dynamodb = boto3.resource("dynamodb", region_name=region)
        table = dynamodb.Table("ECSTaskStatus")

        payload = list()

        for aws_ecs_name, bc_name in extracted_business_contexts.items():

            tasks = get(table=table, region=region,
                        cluster=cluster, service=aws_ecs_name)

            for day in dates:

                (meter_start_t1, meter_end_t1) = get_datetime_start_end(
                    day, None, "01", None)
                (fg_cpu, fg_mem, ec2_mem, ec2_cpu) = cost_of_service(
                    tasks, meter_start_t1, meter_end_t1, day)

                if ec2_mem or ec2_cpu:
                    serviceCost = float(ec2_mem+ec2_cpu)

                entryId = uuid.uuid3(uuid.NAMESPACE_DNS,
                                     bc_name[0]+str(day.timestamp() * 1000))

                bc_cost = {
                    "type": "ECSMeteringCost",
                    "id": str(entryId),
                    "data": {
                        "totalCloudCostsYesterday": serviceCost,
                        "application": bc_name[1],
                        "datetime": day.strftime("%Y-%m-%dT00:00:00"),
                        "serviceId": bc_name[0],
                    }
                }
                payload.append(bc_cost)

        ldif = {
            "connectorType": "leanix-custom",
            "connectorId": "ecs-cost-distribution",
            "connectorVersion": "1.0.0",
            "lxVersion": "1.0.0",
            "description": "Approximated distribution of ECS Service cost by Business Context",
            "processingDirection": "inbound",
            "content": payload
        }

    s3 = boto3.client('s3')
    with open("/tmp/ldif.json", "w+") as f:
        json.dump(obj=ldif, fp=f, indent=4)
        os.chmod("/tmp/ldif.json", 0o777)

    date = datetime.datetime.now().strftime("%Y-%m-%d%H:%M")
    filename = "ldif_"+date+".json"
    with open('/tmp/ldif.json', 'rb') as fh:
        s3.upload_fileobj(fh, "ecsbucktforldif", filename)

    secret = json.loads(get_secret())
    host = secret["host"]
    token = secret["token"]
    call_iapi(ldif=ldif, host=host, token=token)
