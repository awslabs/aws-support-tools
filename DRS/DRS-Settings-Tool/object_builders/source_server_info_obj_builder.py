from classes.source_server_info import SourceServer

def source_server_info_obj_builder_for_csv(server):
    source_server_info_obj = SourceServer(**server)
    return source_server_info_obj

def source_server_info_obj_builder(row):
    source_server_info_obj = SourceServer()
    source_server_info_obj.sourceServerID = row[1]
    return source_server_info_obj
    
