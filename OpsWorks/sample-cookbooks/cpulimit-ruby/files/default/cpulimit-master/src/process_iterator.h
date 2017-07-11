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

#ifndef __PROCESS_ITERATOR_H

#define __PROCESS_ITERATOR_H

#include <unistd.h>
#include <limits.h>
#include <dirent.h>

//USER_HZ detection, from openssl code
#ifndef HZ
# if defined(_SC_CLK_TCK) \
     && (!defined(OPENSSL_SYS_VMS) || __CTRL_VER >= 70000000)
#  define HZ ((double)sysconf(_SC_CLK_TCK))
# else
#  ifndef CLK_TCK
#   ifndef _BSD_CLK_TCK_ /* FreeBSD hack */
#    define HZ  100.0
#   else /* _BSD_CLK_TCK_ */
#    define HZ ((double)_BSD_CLK_TCK_)
#   endif
#  else /* CLK_TCK */
#   define HZ ((double)CLK_TCK)
#  endif
# endif
#endif

#ifdef __FreeBSD__
#include <kvm.h>
#endif

// process descriptor
struct process {
	//pid of the process
	pid_t pid;
	//ppid of the process
	pid_t ppid;
	//start time (unix timestamp)
	int starttime;
	//cputime used by the process (in milliseconds)
	int cputime;
	//actual cpu usage estimation (value in range 0-1)
	double cpu_usage;
	//absolute path of the executable file
	char command[PATH_MAX+1];
};

struct process_filter {
	int pid;
	int include_children;
	char program_name[PATH_MAX+1];
};

struct process_iterator {
#ifdef __linux__
	DIR *dip;
	int boot_time;
#elif defined __FreeBSD__
	kvm_t *kd;
	struct kinfo_proc *procs;
	int count;
	int i;
#elif defined __APPLE__
	int i;
	int count;
	int *pidlist;
#endif
	struct process_filter *filter;
};

int init_process_iterator(struct process_iterator *i, struct process_filter *filter);

int get_next_process(struct process_iterator *i, struct process *p);

int close_process_iterator(struct process_iterator *i);

#endif
