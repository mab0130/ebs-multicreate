# Create EBS

Interactive Python scripts for creating and attaching EBS volumes to EC2 instances on AWS.

## Overview

This toolkit includes two specialized scripts:

**createebs.py** - General purpose EBS volume creation tool
**create-sql-ebs.py** - Purpose-built tool for SQL Server RAID volume sets

Both provide user-friendly command-line interfaces to:
- Select AWS profiles from your local configuration
- Choose from available EC2 instances  
- Create encrypted EBS volumes with customizable specifications
- Automatically attach volumes to the selected instance

## Features

### Common Features (Both Scripts)
- **Profile Selection**: Choose from available AWS profiles configured on your system
- **Instance Discovery**: Lists all EC2 instances with their names and IDs
- **Encryption**: All volumes created with AWS managed encryption (alias/aws/ebs)
- **Volume Naming**: Automatic tagging with custom names
- **Automatic Attachment**: Volumes are automatically attached to the selected instance
- **Device Naming**: Uses Linux-style device names (/dev/xvdf, /dev/xvdg, etc.)
- **Session Summary**: Shows volume counts before/after operations
- **Continuous Operation**: Option to create additional volumes on same instance

### createebs.py Features
- **Volume Types**: Supports all EBS volume types (gp2, gp3, io1, io2, st1, sc1, standard)
- **Bulk Creation**: Create up to 10 volumes at once
- **Custom Configuration**: Set size, IOPS, and throughput parameters per volume set

### create-sql-ebs.py Features
- **RAID-Optimized**: Creates multiple disks per volume type for OS-level RAID striping
- **SQL Server Defaults**: Pre-configured for typical SQL workloads
- **Volume Types**: Data (4×250GB), Log (2×100GB), Temp (2×100GB), CommonFiles (1×50GB), Backup (2×500GB)
- **Individual Configuration**: Customize disk count, size, EBS type, and IOPS per volume type
- **Performance Tuning**: gp3 volumes with 3000 IOPS defaults for optimal SQL performance

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

### General Purpose EBS Creation
```bash
python createebs.py
```

The script will guide you through:
1. **Profile Selection**: Choose an AWS profile from your configured profiles
2. **Instance Selection**: Select the target EC2 instance from the list
3. **Volume Type**: Choose the EBS volume type
4. **Volume Count**: Specify how many volumes to create (1-10)
5. **Volume Size**: Set the size in GiB for each volume (1-16384)
6. **Volume Name**: Enter a custom name for volume tagging
7. **Performance Settings**: Configure IOPS and throughput for applicable volume types

### SQL Server RAID Volume Creation
```bash
python create-sql-ebs.py
```

The script will guide you through:
1. **Profile Selection**: Choose an AWS profile from your configured profiles
2. **Instance Selection**: Select the target EC2 instance from the list
3. **Volume Configuration**: For each SQL volume type (Data, Log, Temp, CommonFiles, Backup):
   - Number of disks for RAID striping (1-10)
   - Size per disk in GiB (1-16384)
   - EBS volume type (gp2, gp3, io1, io2, st1, sc1)
   - IOPS per disk (for applicable types)
   - Throughput per disk (for gp3)

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

## SQL Server Volume Defaults

The create-sql-ebs.py script includes optimized defaults for SQL Server workloads:

| Volume Type | Default Disks | Size per Disk | Total Size | IOPS per Disk | Purpose |
|-------------|---------------|---------------|------------|---------------|---------|
| SQL-Data | 4 | 250 GiB | 1 TB | 3000 | Database files (.mdf) |
| SQL-Log | 2 | 100 GiB | 200 GB | 3000 | Transaction logs (.ldf) |
| SQL-Temp | 2 | 100 GiB | 200 GB | 3000 | TempDB files |
| SQL-CommonFiles | 1 | 50 GiB | 50 GB | 3000 | Shared components |
| SQL-Backup | 2 | 500 GiB | 1 TB | 3000 | Database backups |

All defaults use gp3 volumes for optimal cost/performance balance.

## Error Handling

Both scripts include validation for:
- Invalid profile/instance selections
- Volume count limits (1-10)
- Size constraints (1-16384 GiB)
- Numeric input validation
- EBS type validation

## Security Considerations

- All volumes created with AWS managed encryption (alias/aws/ebs)
- Uses existing AWS credentials and profiles
- No hardcoded credentials in the scripts
- Follows AWS SDK best practices for authentication

## Notes

- Volumes are created in the same Availability Zone as the selected instance
- Scripts wait for each volume to become available before attaching
- All volumes are attached sequentially to ensure proper device naming
- Multi-disk volumes are named with -Disk1, -Disk2, etc. for RAID identification
- Both scripts provide session summaries showing before/after volume counts