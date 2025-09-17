'''
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'mwaa_owned_test_dag',
    default_args=default_args,
    description='A simple DAG with Python and Bash operators',
    catchup=False,
    tags=['example', 'simple'],
)

def python_task_function():
    """
    Simple Python function to be executed by PythonOperator
    """
    print("Hello from Python operator!")
    print("Current timestamp:", datetime.now())
    
    # Perform some simple calculations
    numbers = [1, 2, 3, 4, 5]
    total = sum(numbers)
    average = total / len(numbers)
    
    print(f"Numbers: {numbers}")
    print(f"Sum: {total}")
    print(f"Average: {average}")
    
    return f"Python task completed successfully. Average: {average}"

# Python operator task
python_task = PythonOperator(
    task_id='python_task',
    python_callable=python_task_function,
    dag=dag,
)

# Bash operator task
bash_task = BashOperator(
    task_id='bash_task',
    bash_command='''
    echo "Hello from Bash operator!"
    echo "Current date: $(date)"
    echo "Current user: $(whoami)"
    echo "Current directory: $(pwd)"
    echo "Available disk space:"
    df -h | head -5
    echo "Bash task completed successfully!"
    ''',
    dag=dag,
)

# Set task dependencies
# Python task runs first, then Bash task
python_task >> bash_task
