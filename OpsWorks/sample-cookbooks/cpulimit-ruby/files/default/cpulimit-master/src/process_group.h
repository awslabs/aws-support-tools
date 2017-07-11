/**
# Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
 */

#ifndef __PROCESS_GROUP_H

#define __PROCESS_GROUP_H

#include "process_iterator.h"

#include "list.h"

#define PIDHASH_SZ 1024
#define pid_hashfn(x) ((((x) >> 8) ^ (x)) & (PIDHASH_SZ - 1))

struct process_group
{
	//hashtable with all the processes (array of struct list of struct process)
	struct list *proctable[PIDHASH_SZ];
	struct list *proclist;
	pid_t target_pid;
	int include_children;
	struct timeval last_update;
};

int init_process_group(struct process_group *pgroup, int target_pid, int include_children);

void update_process_group(struct process_group *pgroup);

int close_process_group(struct process_group *pgroup);

int find_process_by_pid(pid_t pid);

int find_process_by_name(const char *process_name);

int remove_process(struct process_group *pgroup, int pid);

#endif
