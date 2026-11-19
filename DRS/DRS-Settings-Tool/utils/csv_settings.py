import os
from utils.logger import path

SETTINGS_CSV = os.path.join(path, 'DRS_Settings.csv')
ORIGINAL_SETTINGS_CSV = os.path.join(path, 'DRS_Settings-DO_NOT_EDIT.csv')

# Column order must match the row built in get_settings.py and the indexes
# used by the object builders when the CSV is read back.
CSV_HEADER = ['Hostname', 'Server ID', 'Launch Template ID', 'Right Sizing', 'Copy Private IP', 'Copy Tags', 'Launch Disposition', 'Launch Into Instance', 'BYOL', 'Recommended Instance Type', 'Target Instance Type', 'Target Key Pair', 'Target AMI ID', 'Target Network Settings', 'Target Disk Settings', 'Target Instance Profile Role', 'Target Instance Tags', 'Target Volume Tags', 'Use Default Replication Security Group', 'Auto Replicate New Disks', 'Bandwidth Throttling', 'Create Public IP for Replication Server', 'Use Private IP for Data Replication', 'Default Large Staging Disk Type', 'PIT Retention Setting(Days)', 'Replication Server Instance Type', 'Staging Disk Settings', 'Staging Disk Encryption', 'Staging Disk Encryption Key Arn', 'Replication Server Security Groups', 'Staging Subnet', 'Use Dedicated Replicator', 'Replication Tags']
