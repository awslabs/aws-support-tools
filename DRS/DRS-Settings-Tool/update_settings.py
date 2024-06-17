
import csv
import botocore
from object_builders.drs_launch_settings_obj_builder import drs_launch_settings_obj_builder
from object_builders.launch_template_obj_builder import launch_template_obj_builder
from object_builders.replication_settings_obj_builder import replication_settings_obj_builder
from object_builders.source_server_info_obj_builder import source_server_info_obj_builder
from utils.settings_validator import validate_settings
from utils.logger import get_logger
from utils.logger import path


rows1 = []
rows2 = []
logger1 = get_logger('REVIEW')
logger = get_logger('UPDATE')
def update_settings(file1, file2):
    try:
        with open(file1, 'r') as file1:
            csvreader = csv.reader(file1)
            header = next(csvreader)
            for row in csvreader:
                rows1.append(row)
        with open(file2, 'r') as file2:
            csvreader = csv.reader(file2)
            header = next(csvreader)
            for row2 in csvreader:
                rows2.append(row2)
        for changes, original in zip(rows1, rows2):
            #build objects from CSV with possible changes made
            new_source_server_info_obj = source_server_info_obj_builder(changes)
            new_drs_launch_settings_obj = drs_launch_settings_obj_builder(changes)
            new_launch_template_obj = launch_template_obj_builder(changes)
            new_replication_settings_obj = replication_settings_obj_builder(changes)

            validate_settings(new_source_server_info_obj, new_drs_launch_settings_obj, new_launch_template_obj, new_replication_settings_obj)

            #build objects from CSV with no changes made
            old_source_server_info_obj = source_server_info_obj_builder(original)
            old_drs_launch_settings_obj = drs_launch_settings_obj_builder(original)
            old_launch_template_obj = launch_template_obj_builder(original)
            old_replication_settings_obj = replication_settings_obj_builder(original)


            #compare objects and only update the ones with changes to reduce API calls being made. The "==" method is using the __eq__ function of each class it compares.
            if new_source_server_info_obj.sourceServerID == old_source_server_info_obj.sourceServerID:
                logger1.info("[REVIEW] Reviewing changes made for Source Server - " + new_source_server_info_obj.sourceServerID + "...")
            else:
                logger.info("Source Server ID's are mismatching when comparing CSV files. Please verify you did not remove, add, or change the Source Server ID in any rows. Please re-run the get_settings.py script to recreate the CSV files.")
                break

            if new_drs_launch_settings_obj != old_drs_launch_settings_obj:
                logger.info("[UPDATE] Updating DRS Launch Settings for Source Server: " + new_source_server_info_obj.sourceServerID)
                new_drs_launch_settings_obj.update_basic_launch_settings(new_drs_launch_settings_obj)
            else:
                logger.info("[NO UPDATE] No changes were made to the DRS Launch Settings.")
            
    
            if new_launch_template_obj != old_launch_template_obj:
                logger.info("[UPDATE] Updating Launch Template Settings for Source Server: " + new_source_server_info_obj.sourceServerID)
                new_launch_template_obj.update_launch_template(new_drs_launch_settings_obj.ec2LaunchTemplateID, new_launch_template_obj)
            else:
                logger.info("[NO UPDATE] No changes were made to the Launch Template Settings.")
                

            if new_replication_settings_obj != old_replication_settings_obj:
                logger.info("[UPDATE] Updating DRS Replication Settings for Source Server: " + new_source_server_info_obj.sourceServerID+"\n__________________________________________________")
                new_replication_settings_obj.update_replication_settings(new_replication_settings_obj)
            else:
                logger.info("[NO UPDATE] No changes were made to the DRS Replication Settings.\n__________________________________________________")
        logger.info("Updates have been completed. If changes were made, please re-run the get_settings.py script to create the new CSV files with the updated settings")
    except botocore.exceptions.ClientError as error:
        logger.error(error)
update_settings(path + "\\DRS_Settings.csv", path + "\\DRS_Settings-DO_NOT_EDIT.csv")
