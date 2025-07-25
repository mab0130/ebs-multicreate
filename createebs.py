import boto3
import time

def list_instances(ec2):
    instances = []
    for reservation in ec2.describe_instances()['Reservations']:
        for inst in reservation['Instances']:
            instances.append(inst)
    return instances

def get_used_device_names(ec2, instance_id):
    """Get list of device names already in use on the instance"""
    used_devices = set()
    
    # Get instance details including block device mappings
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    
    # Check root device
    if 'RootDeviceName' in instance:
        used_devices.add(instance['RootDeviceName'])
    
    # Check attached volumes
    if 'BlockDeviceMappings' in instance:
        for mapping in instance['BlockDeviceMappings']:
            used_devices.add(mapping['DeviceName'])
    
    return used_devices

def find_next_available_device(ec2, instance_id):
    """Find the next available device name for volume attachment"""
    used_devices = get_used_device_names(ec2, instance_id)
    
    # Start from /dev/xvdf and find first available
    for i in range(26):  # a-z
        device_letter = chr(102 + i)  # Start from 'f' (102)
        device_name = f"/dev/xvd{device_letter}"
        
        if device_name not in used_devices:
            return device_name
    
    # If all xvd* are taken, try sd* devices
    for i in range(26):
        device_letter = chr(97 + i)  # Start from 'a' (97)
        device_name = f"/dev/sd{device_letter}"
        
        if device_name not in used_devices:
            return device_name
    
    raise Exception("No available device names found")

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
            prof_input = input(f"Select profile (1-{len(profiles)}) or * to quit: ").strip()
            if prof_input == '*':
                print("Goodbye!")
                return
            prof_idx = int(prof_input)
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
            selection_input = input(f"\nSelect instance (1-{len(instances)}) or * to quit: ").strip()
            if selection_input == '*':
                print("Goodbye!")
                return
            selection = int(selection_input)
            if 1 <= selection <= len(instances):
                selected = instances[selection-1]
                break
        except ValueError:
            pass
        print("Invalid selection.")

    instance_id = selected['InstanceId']
    az = selected['Placement']['AvailabilityZone']
    
    # Count initial volumes attached to the instance
    initial_volume_count = len(get_used_device_names(ec2, instance_id))
    
    print(f"\nSelected Instance: {instance_id} in AZ: {az}")
    print(f"Currently attached volumes: {initial_volume_count}")
    
    total_volumes_created = 0

    while True:  # Main loop for creating volumes
        ebs_types = ["gp2", "gp3", "io1", "io2", "st1", "sc1", "standard"]
        print("\nEBS Volume Types:")
        for idx, t in enumerate(ebs_types):
            print(f"[{idx+1}] {t}")

        while True:
            try:
                ebs_input = input(f"Select EBS type (1-{len(ebs_types)}) or * to quit: ").strip()
                if ebs_input == '*':
                    print("Goodbye!")
                    return
                ebs_type_idx = int(ebs_input)
                if 1 <= ebs_type_idx <= len(ebs_types):
                    ebs_type = ebs_types[ebs_type_idx-1]
                    break
            except ValueError:
                pass
            print("Invalid selection.")

        while True:
            try:
                volume_input = input("How many volumes to create? (1-28) or * to quit: ").strip()
                if volume_input == '*':
                    print("Goodbye!")
                    return
                volume_count = int(volume_input)
                if 1 <= volume_count <= 28:
                    break
            except ValueError:
                pass
            print("Invalid number.")

        while True:
            try:
                size_input = input("Enter size (GiB) for each volume (1-16384) or * to quit: ").strip()
                if size_input == '*':
                    print("Goodbye!")
                    return
                size = int(size_input)
                if 1 <= size <= 16384:
                    break
            except ValueError:
                pass
            print("Invalid size.")

        iops = None
        throughput = None
        if ebs_type in ("io1", "io2", "gp3"):
            iops_input = input("Enter IOPS (or press Enter for default, * to quit): ").strip()
            if iops_input == '*':
                print("Goodbye!")
                return
            iops = int(iops_input) if iops_input.strip() else None
        else:
            iops = None
        if ebs_type == "gp3":
            throughput_input = input("Enter throughput (MB/s, or press Enter for default, * to quit): ").strip()
            if throughput_input == '*':
                print("Goodbye!")
                return
            throughput = int(throughput_input) if throughput_input.strip() else None
        else:
            throughput = None

        # Get volume name prefix
        volume_name_input = input("Enter a name for the volume(s) or * to quit: ").strip()
        if volume_name_input == '*':
            print("Goodbye!")
            return
        volume_name = volume_name_input
        if not volume_name:
            volume_name = "EBS-Volume"

        # Create and attach volumes
        for i in range(volume_count):
            params = {
                'AvailabilityZone': az,
                'Size': size,
                'VolumeType': ebs_type,
                'Encrypted': True
            }
            if iops:
                params['Iops'] = iops
            if throughput:
                params['Throughput'] = throughput

            vol = ec2.create_volume(**params)
            volume_id = vol['VolumeId']
            
            # Set volume name tag
            if volume_count > 1:
                tag_name = f"{volume_name}-{i+1}"
            else:
                tag_name = volume_name
            
            ec2.create_tags(
                Resources=[volume_id],
                Tags=[{'Key': 'Name', 'Value': tag_name}]
            )
            
            print(f"Created volume {volume_id} with name '{tag_name}'")

            # Wait for available
            print("Waiting for volume to become available...")
            while True:
                desc = ec2.describe_volumes(VolumeIds=[volume_id])
                state = desc['Volumes'][0]['State']
                if state == 'available':
                    break
                time.sleep(2)

            # Find next available device name
            device_name = find_next_available_device(ec2, instance_id)

            print(f"Attaching {volume_id} to {instance_id} as {device_name}")
            ec2.attach_volume(InstanceId=instance_id, VolumeId=volume_id, Device=device_name)

        total_volumes_created += volume_count
        print(f"\nAll {volume_count} volume(s) created and attached!")
        
        # Ask if user wants to attach more volumes
        while True:
            again = input("\nWould you like to attach more volumes to this instance? (y/n) or * to quit: ").lower().strip()
            if again == '*':
                print("Goodbye!")
                return
            if again in ['y', 'yes']:
                break
            elif again in ['n', 'no']:
                # Print summary before exiting
                final_volume_count = len(get_used_device_names(ec2, instance_id))
                print(f"\n=== SUMMARY ===")
                print(f"Instance: {instance_id}")
                print(f"Original volumes attached: {initial_volume_count}")
                print(f"New volumes created and attached: {total_volumes_created}")
                print(f"Total volumes now attached: {final_volume_count}")
                print("Goodbye!")
                return
            else:
                print("Please enter 'y' for yes or 'n' for no.")

if __name__ == "__main__":
    main() 