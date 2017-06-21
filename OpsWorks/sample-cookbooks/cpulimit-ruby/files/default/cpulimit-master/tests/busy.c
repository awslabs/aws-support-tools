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

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

void *loop()
{
	while(1);
}

int main(int argc, char **argv) {

	int i = 0;
	int num_threads = 1;
	if (argc == 2) num_threads = atoi(argv[1]);
	for (i=0; i<num_threads-1; i++)
	{
		pthread_t thread;
		int ret;
		if ((ret = pthread_create(&thread, NULL, loop, NULL)) != 0)
		{
			printf("pthread_create() failed. Error code %d\n", ret);
			exit(1);
		}
	}
	loop();
	return 0;
}

