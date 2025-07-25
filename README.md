# Create EBS

## Bottom Line Up Front

**What it does:** Automates creation and attachment of encrypted EBS volumes to EC2 instances with intelligent device naming and comprehensive configuration options.

**Two tools available:**
- `createebs.py` - General purpose tool for any EBS volume needs
- `create-sql-ebs.py` - Specialized tool for SQL Server RAID volume sets

**Key benefits:** No manual AWS console clicking, automatic encryption, proper device naming, RAID-optimized configurations for SQL Server, and session summaries.

## Quick Start

### General EBS Volumes
```bash
python createebs.py
# Creates 1-28 encrypted volumes with custom names
# Supports all EBS types, automatic device naming
# Option to create additional volumes on same instance
```

### SQL Server RAID Volumes  
```bash
python create-sql-ebs.py
# Creates optimized volume sets: Data (4×250GB), Log (2×100GB), 
# Temp (2×100GB), CommonFiles (1×50GB), Backup (2×500GB)
# All gp3 with 3000 IOPS, ready for OS RAID configuration
```

## What Each Tool Does

### createebs.py - General Purpose Tool
Creates 1-28 EBS volumes with:
- **Any EBS type** (gp2, gp3, io1, io2, st1, sc1, standard)
- **Custom sizing** (1-16384 GiB per volume)  
- **Custom naming** with automatic tagging
- **Performance tuning** (IOPS/throughput for applicable types)
- **Continuous operation** - create multiple sets on same instance
- **Exit anytime** with `*` command

**Example Output:**
```
Selected Instance: i-1234567890abcdef0 in AZ: us-east-1a
Currently attached volumes: 2

Creating 3 volumes named "WebApp-Storage"...
Created volume vol-abc123 with name 'WebApp-Storage-1'
Created volume vol-def456 with name 'WebApp-Storage-2' 
Created volume vol-ghi789 with name 'WebApp-Storage-3'

=== SUMMARY ===
Instance: i-1234567890abcdef0
Original volumes attached: 2
New volumes created: 3
Total volumes now attached: 5
```

### create-sql-ebs.py - SQL Server RAID Tool
Creates optimized volume sets for SQL Server with intelligent defaults:

| Volume Set | Default Config | Purpose |
|------------|----------------|---------|
| **SQL-Data** | 4 × 250 GiB gp3 @ 3000 IOPS | Database files (.mdf) |
| **SQL-Log** | 2 × 100 GiB gp3 @ 3000 IOPS | Transaction logs (.ldf) |
| **SQL-Temp** | 2 × 100 GiB gp3 @ 3000 IOPS | TempDB files |
| **SQL-CommonFiles** | 1 × 50 GiB gp3 @ 3000 IOPS | Shared components |
| **SQL-Backup** | 2 × 500 GiB gp3 @ 3000 IOPS | Database backups |

**Example Output:**
```
Creating 4 disk(s) for SQL-Data...
Created volume vol-data1 with name 'SQL-Data-Disk1' (250 GiB)
Created volume vol-data2 with name 'SQL-Data-Disk2' (250 GiB)
Created volume vol-data3 with name 'SQL-Data-Disk3' (250 GiB)
Created volume vol-data4 with name 'SQL-Data-Disk4' (250 GiB)

RAID Volume Sets Created:
  SQL-Data: 4 disk(s)
    - SQL-Data-Disk1
    - SQL-Data-Disk2
    - SQL-Data-Disk3
    - SQL-Data-Disk4
  SQL-Log: 2 disk(s)
  SQL-Temp: 2 disk(s)
  SQL-CommonFiles: 1 disk(s)
  SQL-Backup: 2 disk(s)

Ready for RAID configuration in the OS!
```

## Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/mab0130/ebs-multicreate.git
cd ebs-multicreate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure AWS credentials are configured
aws configure  # or use environment variables/IAM roles
```

## How to Use

### For General EBS Volumes
```bash
python createebs.py
```
**Interactive prompts:**
1. Select AWS profile → Choose from your configured profiles
2. Select EC2 instance → Pick target instance (shows current volume count)
3. Choose EBS type → gp2, gp3, io1, io2, st1, sc1, standard
4. Set volume count → 1-28 volumes per batch
5. Set volume size → 1-16384 GiB per volume
6. Enter volume name → Used for tagging (auto-numbered if multiple)
7. Configure performance → IOPS/throughput for applicable types
8. Continue or exit → Option to create more volumes on same instance

**Pro tip:** Type `*` at any prompt to exit gracefully

### For SQL Server RAID Volumes
```bash
python create-sql-ebs.py
```
**Interactive prompts:**
1. Select AWS profile → Choose from your configured profiles  
2. Select EC2 instance → Pick target instance
3. Configure each volume set → Or press Enter to use optimized defaults:
   - **SQL-Data**: 4 disks × 250 GiB = 1TB RAID set
   - **SQL-Log**: 2 disks × 100 GiB = 200GB RAID set
   - **SQL-Temp**: 2 disks × 100 GiB = 200GB RAID set  
   - **SQL-CommonFiles**: 1 disk × 50 GiB = 50GB single disk
   - **SQL-Backup**: 2 disks × 500 GiB = 1TB RAID set

**Result:** Ready-to-configure RAID volume sets with proper naming for OS-level striping

## Key Features

### Security & Best Practices
- ✅ **Automatic encryption** using AWS managed keys (alias/aws/ebs)
- ✅ **No hardcoded credentials** - uses your existing AWS configuration
- ✅ **Intelligent device naming** - automatically finds available `/dev/xvd*` devices
- ✅ **Safe exit** - type `*` at any prompt to quit gracefully

### User Experience  
- ✅ **Current state visibility** - shows existing volume count before starting
- ✅ **Session summaries** - reports before/after volume counts and what was created
- ✅ **Continuous operation** - create multiple volume sets without restarting
- ✅ **Smart defaults** - SQL tool has production-ready configurations built-in
- ✅ **Input validation** - prevents invalid configurations and provides clear error messages

## Technical Details

### Supported EBS Types
| Type | Description | Use Case |
|------|-------------|----------|
| `gp3` | General Purpose SSD (latest) | Balanced price/performance |
| `gp2` | General Purpose SSD | Legacy applications |
| `io1/io2` | Provisioned IOPS SSD | High IOPS requirements |
| `st1` | Throughput Optimized HDD | Big data, data warehouses |
| `sc1` | Cold HDD | Infrequent access |

### Device Naming Convention
- Volumes attach to `/dev/xvdf`, `/dev/xvdg`, `/dev/xvdh`, etc.
- Script automatically detects used devices and assigns next available
- RAID volumes named with `-Disk1`, `-Disk2` suffixes for easy identification

### Volume Limits
- **createebs.py**: 1-28 volumes per batch
- **create-sql-ebs.py**: 1-10 disks per volume type (typically 11 total volumes)
- **Size range**: 1-16384 GiB per volume

## Troubleshooting

**"No AWS profiles found"** → Run `aws configure` to set up credentials  
**"No EC2 instances found"** → Check your AWS region and instance states  
**"No available device names"** → Instance may have maximum volumes attached  
**Script hangs during creation** → Check AWS service status and network connectivity