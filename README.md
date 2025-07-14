# EBS Multi-Create

A Python script that simplifies creating and attaching multiple EBS volumes to EC2 instances through an interactive command-line interface.

## Features

- Interactive AWS profile selection
- EC2 instance selection with instance names
- Support for all EBS volume types (gp2, gp3, io1, io2, st1, sc1, standard)
- Bulk creation of up to 10 volumes
- Automatic volume attachment with sequential device naming
- Configurable IOPS and throughput for supported volume types

## Prerequisites

- Python 3.x
- AWS CLI configured with appropriate credentials
- `boto3` library installed

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ebs-multicreate
```

2. Install required dependencies:
```bash
pip install boto3
```

3. Ensure your AWS credentials are configured via AWS CLI:
```bash
aws configure
```

## Usage

Run the script:
```bash
python createebs.py
```

The script will guide you through:

1. **Profile Selection**: Choose from available AWS profiles
2. **Instance Selection**: Select target EC2 instance from your account
3. **Volume Configuration**:
   - Choose EBS volume type
   - Specify number of volumes (1-10)
   - Set volume size (1-16384 GiB)
   - Configure IOPS (for io1, io2, gp3 types)
   - Set throughput (for gp3 type)

## Volume Types Supported

- **gp2**: General Purpose SSD
- **gp3**: General Purpose SSD (newest generation)
- **io1**: Provisioned IOPS SSD
- **io2**: Provisioned IOPS SSD (newest generation)
- **st1**: Throughput Optimized HDD
- **sc1**: Cold HDD
- **standard**: Magnetic (previous generation)

## Device Naming

Volumes are automatically attached with sequential device names:
- First volume: `/dev/xvdf`
- Second volume: `/dev/xvdg`
- Third volume: `/dev/xvdh`
- And so on...

## Example Output

```
Available AWS Profiles:
[1] default
[2] production

Select profile (1-2): 1

Available EC2 Instances:
[1] InstanceId: i-1234567890abcdef0 | Name: Web Server
[2] InstanceId: i-0987654321fedcba0 | Name: Database Server

Select instance (1-2): 1

Selected Instance: i-1234567890abcdef0 in AZ: us-east-1a

EBS Volume Types:
[1] gp2
[2] gp3
[3] io1
[4] io2
[5] st1
[6] sc1
[7] standard

Select EBS type (1-7): 2
How many volumes to create? (1-10): 3
Enter size (GiB) for each volume (1-16384): 100

Created volume vol-1234567890abcdef0
Waiting for volume to become available...
Attaching vol-1234567890abcdef0 to i-1234567890abcdef0 as /dev/xvdf

Created volume vol-0987654321fedcba0
Waiting for volume to become available...
Attaching vol-0987654321fedcba0 to i-1234567890abcdef0 as /dev/xvdg

Created volume vol-abcdef1234567890
Waiting for volume to become available...
Attaching vol-abcdef1234567890 to i-1234567890abcdef0 as /dev/xvdh

All volumes created and attached!
```

## Security Considerations

- The script uses your configured AWS credentials
- Ensure you have appropriate IAM permissions for EC2 and EBS operations
- Review volume configurations before confirming creation
- Monitor AWS costs, especially for provisioned IOPS volumes

## Required AWS Permissions

Your AWS user/role needs the following permissions:
- `ec2:DescribeInstances`
- `ec2:CreateVolume`
- `ec2:DescribeVolumes`
- `ec2:AttachVolume`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions, please open an issue in the GitHub repository.