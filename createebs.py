import boto3
import time

def list_instances(ec2):
    instances = []
    for reservation in ec2.describe_instances()['Reservations']:
        for inst in reservation['Instances']:
            instances.append(inst)
    return instances

def main():
    # List available profiles
    session = boto3.Session()
    profiles = session.available_profiles
    if not profiles:
        print("No AWS profiles found. Please configure your AWS credentials.")
        return

    print("\nAvailable AWS Profiles:")
    for idx, prof in enumerate(profiles):
        print(f"[{idx+1}] {prof}")

    while True:
        try:
            prof_idx = int(input(f"Select profile (1-{len(profiles)}): "))
            if 1 <= prof_idx <= len(profiles):
                profile = profiles[prof_idx-1]
                break
        except ValueError:
            pass
        print("Invalid selection.")

    # Use the selected profile
    session = boto3.Session(profile_name=profile)
    ec2 = session.client('ec2')

    instances = list_instances(ec2)
    if not instances:
        print("No EC2 instances found.")
        return

    print("\nAvailable EC2 Instances:")
    for idx, inst in enumerate(instances):
        name = next((tag['Value'] for tag in inst.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
        print(f"[{idx+1}] InstanceId: {inst['InstanceId']} | Name: {name}")

    while True:
        try:
            selection = int(input(f"\nSelect instance (1-{len(instances)}): "))
            if 1 <= selection <= len(instances):
                selected = instances[selection-1]
                break
        except ValueError:
            pass
        print("Invalid selection.")

    instance_id = selected['InstanceId']
    az = selected['Placement']['AvailabilityZone']
    print(f"\nSelected Instance: {instance_id} in AZ: {az}")

    ebs_types = ["gp2", "gp3", "io1", "io2", "st1", "sc1", "standard"]
    print("\nEBS Volume Types:")
    for idx, t in enumerate(ebs_types):
        print(f"[{idx+1}] {t}")

    while True:
        try:
            ebs_type_idx = int(input(f"Select EBS type (1-{len(ebs_types)}): "))
            if 1 <= ebs_type_idx <= len(ebs_types):
                ebs_type = ebs_types[ebs_type_idx-1]
                break
        except ValueError:
            pass
        print("Invalid selection.")

    while True:
        try:
            volume_count = int(input("How many volumes to create? (1-10): "))
            if 1 <= volume_count <= 10:
                break
        except ValueError:
            pass
        print("Invalid number.")

    while True:
        try:
            size = int(input("Enter size (GiB) for each volume (1-16384): "))
            if 1 <= size <= 16384:
                break
        except ValueError:
            pass
        print("Invalid size.")

    iops = None
    throughput = None
    if ebs_type in ("io1", "io2", "gp3"):
        iops = input("Enter IOPS (or press Enter for default): ")
        iops = int(iops) if iops.strip() else None
    if ebs_type == "gp3":
        throughput = input("Enter throughput (MB/s, or press Enter for default): ")
        throughput = int(throughput) if throughput.strip() else None

    # Create and attach volumes
    for i in range(volume_count):
        params = {
            'AvailabilityZone': az,
            'Size': size,
            'VolumeType': ebs_type
        }
        if iops:
            params['Iops'] = iops
        if throughput:
            params['Throughput'] = throughput

        vol = ec2.create_volume(**params)
        volume_id = vol['VolumeId']
        print(f"Created volume {volume_id}")

        # Wait for available
        print("Waiting for volume to become available...")
        while True:
            desc = ec2.describe_volumes(VolumeIds=[volume_id])
            state = desc['Volumes'][0]['State']
            if state == 'available':
                break
            time.sleep(2)

        # Find next available device name (Linux style, e.g., /dev/xvdf, /dev/xvdg, etc.)
        device_letter = chr(102 + i)  # 102 = 'f'
        device_name = f"/dev/xvd{device_letter}"

        print(f"Attaching {volume_id} to {instance_id} as {device_name}")
        ec2.attach_volume(InstanceId=instance_id, VolumeId=volume_id, Device=device_name)

    print("\nAll volumes created and attached!")

if __name__ == "__main__":
    main() 