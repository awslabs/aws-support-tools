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

CC?=gcc
CFLAGS?=-Wall -g
TARGETS=busy process_iterator_test
SRC=../src
SYSLIBS?=-lpthread
LIBS=$(SRC)/list.o $(SRC)/process_iterator.o $(SRC)/process_group.o
UNAME := $(shell uname)

ifeq ($(UNAME), FreeBSD)
LIBS+=-lkvm
endif

all::	$(TARGETS)

busy:	busy.c
	$(CC) -o busy busy.c $(SYSLIBS) $(CFLAGS)

process_iterator_test: process_iterator_test.c $(LIBS)
	$(CC) -I$(SRC) -o process_iterator_test process_iterator_test.c $(LIBS) $(SYSLIBS) $(CFLAGS)

clean:
	rm -f *~ *.o $(TARGETS)

