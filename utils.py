import boto3
import random

aws_access_key_id='<ask bspar>'
aws_secret_access_key='<ask bspar>'
regions = {
    # 'us-east-1' : 'ami-89e449f6',
    'us-east-2' : 'ami-2ca79449',
    'us-west-1' : 'ami-dc4e53bc',
    'us-west-2' : 'ami-761e700e',
    'ap-northeast-1' : 'ami-1bf6ec67',
    'eu-central-1' : 'ami-224266c9'
}
vpc = {
    # 'us-east-1' : 'vpc-d384ffa8',
    'us-east-2' : 'vpc-1f87ea77',
    # 'us-west-1' : 'NONE',
    # 'us-west-2' : 'NONE',
    # 'ap-northeast-1' : 'NONE',
    # 'eu-central-1' : 'NONE'
}

def get_ec2(region=None):
    if not region:
        region = random.choice(list(regions.keys()))
    ec2 = boto3.resource('ec2',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region)
    return (region, ec2)

def instance_status(name):
    instid = name.split('.')[0]
    region = name.split('.')[1]
    _, ec2 = get_ec2(region)
    inst = ec2.Instance(instid)
    inst.load()
    return inst.state['Name']

def all_statuses():
    statuses = dict()
    for region in regions:
        _, ec2 = get_ec2(region)
        for status in ec2.meta.client.describe_instance_status(IncludeAllInstances=True)['InstanceStatuses']:
            statuses[status['InstanceId']+'.'+region] = status['InstanceState']['Name']
    return statuses

def create_instance(region=None):
    region, ec2 = get_ec2(region)
    instance = ec2.create_instances(ImageId=regions[region], InstanceType='t2.small',
        KeyName='bspartop-vm', MaxCount=1, MinCount=1)[0]
    name = instance.instance_id + '.' + region
    return ('pending', name)

def get_ip(name):
    instid = name.split('.')[0]
    region = name.split('.')[1]
    _, ec2 = get_ec2(region)
    inst = ec2.Instance(instid)
    ip = inst.public_ip_address
    if not ip:
        ip = 'pending'
    return ip

def terminate(name):
    instid = name.split('.')[0]
    region = name.split('.')[1]
    _, ec2 = get_ec2(region)
    inst = ec2.Instance(instid)
    inst.terminate()

def stop(name):
    instid = name.split('.')[0]
    region = name.split('.')[1]
    _, ec2 = get_ec2(region)
    inst = ec2.Instance(instid)
    inst.stop()

def start(name):
    instid = name.split('.')[0]
    region = name.split('.')[1]
    _, ec2 = get_ec2(region)
    inst = ec2.Instance(instid)
    inst.start()
