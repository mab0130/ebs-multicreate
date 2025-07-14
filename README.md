# Create EBS

An interactive Python script for creating and attaching EBS volumes to EC2 instances on AWS.

## Overview

This tool provides a user-friendly command-line interface to:
- Select AWS profiles from your local configuration
- Choose from available EC2 instances
- Create multiple EBS volumes with customizable specifications
- Automatically attach volumes to the selected instance

## Features

- **Profile Selection**: Choose from available AWS profiles configured on your system
- **Instance Discovery**: Lists all EC2 instances with their names and IDs
- **Volume Types**: Supports all EBS volume types (gp2, gp3, io1, io2, st1, sc1, standard)
- **Bulk Creation**: Create up to 10 volumes at once
- **Custom Configuration**: Set size, IOPS, and throughput parameters
- **Automatic Attachment**: Volumes are automatically attached to the selected instance
- **Device Naming**: Uses Linux-style device names (/dev/xvdf, /dev/xvdg, etc.)

## Requirements

- Python 3.x
- boto3 library
- AWS credentials configured (via AWS CLI, environment variables, or IAM roles)

## Installation

1. Ensure you have Python 3.x installed
2. Install the required dependency:
   ```bash
   pip install boto3
   ```

## Usage

Run the script:
```bash
python createebs.py
```

The script will guide you through:

1. **Profile Selection**: Choose an AWS profile from your configured profiles
2. **Instance Selection**: Select the target EC2 instance from the list
3. **Volume Type**: Choose the EBS volume type
4. **Volume Count**: Specify how many volumes to create (1-10)
5. **Volume Size**: Set the size in GiB for each volume (1-16384)
6. **Performance Settings**: Configure IOPS and throughput for applicable volume types

## Volume Types

- **gp2**: General Purpose SSD (previous generation)
- **gp3**: General Purpose SSD (current generation)
- **io1**: Provisioned IOPS SSD (previous generation)
- **io2**: Provisioned IOPS SSD (current generation)
- **st1**: Throughput Optimized HDD
- **sc1**: Cold HDD
- **standard**: Magnetic volumes (previous generation)

## Performance Configuration

For high-performance volume types:
- **io1/io2**: IOPS configuration required
- **gp3**: Optional IOPS and throughput configuration

## Device Naming

Volumes are attached using Linux device names starting from `/dev/xvdf` and incrementing sequentially (e.g., `/dev/xvdg`, `/dev/xvdh`, etc.).

## Error Handling

The script includes validation for:
- Invalid profile/instance selections
- Volume count limits (1-10)
- Size constraints (1-16384 GiB)
- Numeric input validation

## Security Considerations

- Uses existing AWS credentials and profiles
- No hardcoded credentials in the script
- Follows AWS SDK best practices for authentication

## Notes

- Volumes are created in the same Availability Zone as the selected instance
- The script waits for each volume to become available before attaching
- All volumes are attached sequentially to ensure proper device naming