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

def create_volume(ec2, az, volume_name, size, volume_type='gp3', iops=None, throughput=None):
    """Create and return a volume with the specified parameters"""
    params = {
        'AvailabilityZone': az,
        'Size': size,
        'VolumeType': volume_type,
        'Encrypted': True
    }
    if iops:
        params['Iops'] = iops
    if throughput:
        params['Throughput'] = throughput

    vol = ec2.create_volume(**params)
    volume_id = vol['VolumeId']
    
    # Set volume name tag
    ec2.create_tags(
        Resources=[volume_id],
        Tags=[{'Key': 'Name', 'Value': volume_name}]
    )
    
    print(f"Created volume {volume_id} with name '{volume_name}' ({size} GiB)")
    return volume_id

def wait_for_volume_available(ec2, volume_id):
    """Wait for volume to become available"""
    print("Waiting for volume to become available...")
    while True:
        desc = ec2.describe_volumes(VolumeIds=[volume_id])
        state = desc['Volumes'][0]['State']
        if state == 'available':
            break
        time.sleep(2)

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

    # Count initial volumes attached to the instance
    initial_volume_count = len(get_used_device_names(ec2, instance_id))

    print("\n=== SQL Server Volume Configuration ===")
    print("This will create volumes for RAID striping: Data, Log, Temp, CommonFiles, and Backup")
    
    # Define SQL volume configurations with defaults (name, disk_count, size_per_disk, volume_type, iops_per_disk)
    sql_volume_defaults = {
        "SQL-Data": {"disks": 4, "size": 250, "type": "gp3", "iops": 3000},
        "SQL-Log": {"disks": 2, "size": 100, "type": "gp3", "iops": 3000},
        "SQL-Temp": {"disks": 2, "size": 100, "type": "gp3", "iops": 3000},
        "SQL-CommonFiles": {"disks": 1, "size": 50, "type": "gp3", "iops": 3000},
        "SQL-Backup": {"disks": 2, "size": 500, "type": "gp3", "iops": 3000}
    }

    print("\nConfigure each volume set (or press Enter for defaults):")
    volume_configs = []
    
    for vol_name, defaults in sql_volume_defaults.items():
        print(f"\n--- {vol_name} Configuration ---")
        print(f"Default: {defaults['disks']} disks x {defaults['size']} GiB each = {defaults['disks'] * defaults['size']} GiB total")
        
        # Get number of disks
        while True:
            try:
                disks_input = input(f"Number of disks for {vol_name} [default: {defaults['disks']}]: ").strip()
                disk_count = int(disks_input) if disks_input else defaults['disks']
                if 1 <= disk_count <= 10:
                    break
                else:
                    print("Disk count must be between 1 and 10.")
            except ValueError:
                print("Invalid number. Please enter a valid disk count.")
        
        # Get size per disk
        while True:
            try:
                size_input = input(f"Size per disk (GiB) for {vol_name} [default: {defaults['size']}]: ").strip()
                size_per_disk = int(size_input) if size_input else defaults['size']
                if 1 <= size_per_disk <= 16384:
                    break
                else:
                    print("Size must be between 1 and 16384 GiB.")
            except ValueError:
                print("Invalid size. Please enter a number.")
        
        # Get volume type
        ebs_types = ["gp2", "gp3", "io1", "io2", "st1", "sc1"]
        print(f"Volume types: {', '.join([f'{i+1}={t}' for i, t in enumerate(ebs_types)])}")
        while True:
            try:
                type_input = input(f"EBS type for {vol_name} [default: {defaults['type']}]: ").strip()
                if not type_input:
                    volume_type = defaults['type']
                    break
                elif type_input in ebs_types:
                    volume_type = type_input
                    break
                elif type_input.isdigit() and 1 <= int(type_input) <= len(ebs_types):
                    volume_type = ebs_types[int(type_input)-1]
                    break
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid selection.")
        
        # Get IOPS if applicable
        iops_per_disk = None
        if volume_type in ("io1", "io2", "gp3"):
            while True:
                try:
                    iops_input = input(f"IOPS per disk for {vol_name} [default: {defaults['iops'] if volume_type == 'gp3' else 'auto'}]: ").strip()
                    if not iops_input:
                        iops_per_disk = defaults['iops'] if volume_type == 'gp3' else None
                        break
                    else:
                        iops_per_disk = int(iops_input)
                        break
                except ValueError:
                    print("Invalid IOPS value.")
        
        # Get throughput for gp3
        throughput_per_disk = None
        if volume_type == "gp3":
            throughput_input = input(f"Throughput (MB/s) per disk for {vol_name} [default: auto]: ").strip()
            throughput_per_disk = int(throughput_input) if throughput_input else None
        
        total_size = disk_count * size_per_disk
        print(f"Configuration: {disk_count} x {size_per_disk} GiB {volume_type} disks = {total_size} GiB total")
        
        volume_configs.append({
            'name': vol_name,
            'disk_count': disk_count,
            'size_per_disk': size_per_disk,
            'volume_type': volume_type,
            'iops_per_disk': iops_per_disk,
            'throughput_per_disk': throughput_per_disk
        })

    print(f"\n=== Creating SQL Server Volumes ===")
    created_volumes = []

    # Create all volumes based on configurations
    for config in volume_configs:
        vol_name = config['name']
        disk_count = config['disk_count']
        
        print(f"\nCreating {disk_count} disk(s) for {vol_name}...")
        
        for disk_num in range(1, disk_count + 1):
            if disk_count > 1:
                disk_name = f"{vol_name}-Disk{disk_num}"
            else:
                disk_name = vol_name
            
            volume_id = create_volume(
                ec2, 
                az, 
                disk_name, 
                config['size_per_disk'], 
                config['volume_type'], 
                config['iops_per_disk'], 
                config['throughput_per_disk']
            )
            created_volumes.append((volume_id, disk_name, vol_name))

    # Wait for all volumes to become available and attach them
    for volume_id, disk_name, vol_type in created_volumes:
        wait_for_volume_available(ec2, volume_id)
        
        # Find next available device name
        device_name = find_next_available_device(ec2, instance_id)
        
        print(f"Attaching {disk_name} ({volume_id}) to {instance_id} as {device_name}")
        ec2.attach_volume(InstanceId=instance_id, VolumeId=volume_id, Device=device_name)

    # Print summary
    final_volume_count = len(get_used_device_names(ec2, instance_id))
    print(f"\n=== SQL SERVER VOLUMES CREATED ===")
    print(f"Instance: {instance_id}")
    print(f"Original volumes attached: {initial_volume_count}")
    print(f"New SQL volumes created: {len(created_volumes)}")
    print(f"Total volumes now attached: {final_volume_count}")
    
    # Group volumes by type for summary
    volume_groups = {}
    for _, disk_name, vol_type in created_volumes:
        if vol_type not in volume_groups:
            volume_groups[vol_type] = []
        volume_groups[vol_type].append(disk_name)
    
    print("\nRAID Volume Sets Created:")
    for vol_type, disks in volume_groups.items():
        print(f"  {vol_type}: {len(disks)} disk(s)")
        for disk in disks:
            print(f"    - {disk}")
    
    print("\nAll SQL Server volumes created and attached successfully!")
    print("Ready for RAID configuration in the OS!")

if __name__ == "__main__":
    main()