'''
    Note: This is just a POC and is just a potential workaround but not a conplete solution.
          This is subject to change should any updates to the API occur.
'''

import boto3

'''
    Requirements:

        Please make sure you have configured your AWS CLI installed and an IAM user with appropriate permissions credentials available.
        Please install the needed packages namely (boto3)
        This script was written using python3 and ran from a windows and linux environment. It seemed to break on MAC

    Description:

        This algorithm finds all inservice sagemaker instances per region and then sums them up to give you the total number of instances running at any given time.
        We need to find all active instances from Notebook instances, Endpoints (Here we get the current number of instances running as this is subject to change because of potential auto-scaling),
        Training jobs,  Hyperparamater jobs and transform jobs. To succesfully get the number of instances running at any point in time for these jobs we need to poll the API to check if the training instances
        are still running by the time the specified function call completes.
'''

class SageMakerBoto3:

    instancesDictoinary = {}    #This stores all the information about instances in your sagemaker environment
    totalInstances = 0

    '''
        This is the first method called when you instantiate the class in the class driver.
        We configure the client so we can make calls to the sagemakwer api.
        We pass the credentials since hard coded strings as credentials, not recommended.
        We pass the region as this helps us make appropriate calls to every sagemaker region.
    '''
    def __init__(self,access_key,secret_key,sagemakerRegion):
        self.client = boto3.client('sagemaker', aws_access_key_id = access_key, aws_secret_access_key = secret_key, region_name=sagemakerRegion)


    '''
        This method alows our driver to sum up the total instances per region.
    '''
    def getRegionTotal(self):
        return self.totalInstances

    '''
        Finds all the Notebook instancs currently in service
    '''
    def FindRunningNotebooks(self):

        response = self.client.list_notebook_instances(StatusEquals='InService')
        self.instancesDictoinary['NotebookEnv'] = []

        count = 0
        while(True):
            try:
                self.instancesDictoinary['NotebookEnv'].append('InstanceName: ' + str(response["NotebookInstances"][count]['NotebookInstanceName']) + ' InstanceType: ' + str(response["NotebookInstances"][count]['InstanceType']))
                count+=1

            except Exception:
                break

        self.instancesDictoinary['NotebookEnv'].append('TotalNotebooksInstances: ' + str(count))
        self.totalInstances += count

    '''
        Finds all the training jobs, we need to poll the 'list jobs' api to know if instances the training jobs completed
    '''
    def FindTrainingJobInstances(self):

        self.instancesDictoinary['TrainingJobInstances'] = []
        totalTrainingInstances = 0
        count = 0

        while(True):
            try:
                progressPoll = self.client.list_training_jobs(StatusEquals='InProgress')

                jobName = str(progressPoll['TrainingJobSummaries'][count]['TrainingJobName'])
                describejobResponse = self.client.describe_training_job(TrainingJobName=jobName)

                instanceCount = str(describejobResponse['ResourceConfig']['InstanceCount'])
                totalTrainingInstances += int(instanceCount)

                self.instancesDictoinary['TrainingJobInstances'].append('TrainingJobName: ' + jobName + ' InstanceType: ' + str(describejobResponse['ResourceConfig']['InstanceType']) + ' InstanceCount: ' + instanceCount)

                count+=1

            except Exception:
                break

        self.instancesDictoinary['TrainingJobInstances'].append('TotalTrainingInstances: ' + str(totalTrainingInstances))
        self.totalInstances += totalTrainingInstances

    '''
        Finds all the training jobs, we need to poll the 'list jobs' api to know if instances the tuning jobs completed
    '''
    def FindHyperparameterTuningJobInstances(self):

        self.instancesDictoinary['HyperparameterInstances'] = []
        totalHyperparameterInstances = 0
        count = 0

        while(True):

            try:
                progressPoll = self.client.list_hyper_parameter_tuning_jobs(StatusEquals='InProgress')

                tuningJobName = str(progressPoll['HyperParameterTuningJobSummaries'][count]['HyperParameterTuningJobName'])
                describeTuningJobResponse = self.client.describe_hyper_parameter_tuning_job(HyperParameterTuningJobName=tuningJobName)

                instanceCount = str(describeTuningJobResponse['TrainingJobDefinition']['ResourceConfig']['InstanceCount'])
                totalHyperparameterInstances += int(instanceCount)

                self.instancesDictoinary['HyperparameterInstances'].append('TuningJobName: ' + str(describeTuningJobResponse['TrainingJobDefinition']['ResourceConfig']['InstanceType']) + ' InstanceType: ' + instanceType + ' InitialInstanceCount: ' + instanceCount)

                count+=1

            except Exception:
                break

        self.instancesDictoinary['HyperparameterInstances'].append('TotalTuningInstances: ' + str(totalHyperparameterInstances))
        self.totalInstances += totalHyperparameterInstances

    '''
        Finds all the training jobs, we need to poll the 'list jobs' api to know if instances the transform jobs completed
    '''
    def FindTransformJobInstances(self):

        self.instancesDictoinary['batchTransformInstances'] = []
        totalTransformInstances = 0
        count = 0

        while(True):

            try:
                progressPoll = self.client.list_transform_jobs(StatusEquals='InProgress')

                transformJobName = str(progressPoll['TransformJobSummaries'][count]['TransformJobName'])
                describeTransformJobResponse = self.client.describe_transform_job(TransformJobName=transformJobName)

                instanceCount = str(describeTransformJobResponse['TransformResources']['InstanceCount'])
                totalTransformInstances += int(instanceCount)

                self.instancesDictoinary['batchTransformInstances'].append('TransformJobName: ' + transformJobName + ' InstanceType: ' + str(describeTransformJobResponse['TransformResources']['InstanceType']) + ' instanceCount: ' + instanceCount)

                count+=1

            except Exception:
                break

        self.instancesDictoinary['batchTransformInstances'].append('TotalTransformJobInstances: ' + str(totalTransformInstances))

        self.totalInstances += totalTransformInstances
        self.instancesDictoinary['OverallTotalInstances'] = 'TotalInstances: ' + str(self.totalInstances)

    '''
        Find the currently running instances per endpoint, this factors in the possiblity of auto-scaling
    '''
    def FindEndpointInstances(self):

        self.instancesDictoinary['EndpointInstances'] = []
        totalEndpointInstances = 0
        count = 0
        response = self.client.list_endpoints(StatusEquals='InService')

        while(True):

            try:

                endpointName = str(response['Endpoints'][count]['EndpointName'])
                listEndpointConfigResponse = self.client.list_endpoint_configs(NameContains=endpointName)
                describeEndpointConfigResponse = self.client.describe_endpoint_config(EndpointConfigName=str(listEndpointConfigResponse['EndpointConfigs'][0]['EndpointConfigName']))

                describeEndpointResponse = self.client.describe_endpoint(EndpointName=endpointName)
                currentInstanceCount = str(describeEndpointResponse['ProductionVariants'][0]['CurrentInstanceCount'])
                totalEndpointInstances += int(currentInstanceCount)

                self.instancesDictoinary['EndpointInstances'].append('EndpointName: ' + endpointName + ' InstanceType: ' + str(describeEndpointConfigResponse['ProductionVariants'][0]['InstanceType']) + ' CurrentInstanceCount: ' + str(currentInstanceCount) + ' DesiredInstanceCount: ' + str(describeEndpointResponse['ProductionVariants'][0]['DesiredInstanceCount']))

                count+=1

            except Exception:
                break

        self.instancesDictoinary['EndpointInstances'].append('TotalEndpointInstances: ' + str(totalEndpointInstances))
        self.totalInstances += totalEndpointInstances

    '''
        This function makes calls to all the appropriate methods and neatly outputs the results
    '''
    def returnTotalRunningInstances(self,sagemakerRegion):
        self.FindRunningNotebooks()
        self.FindTrainingJobInstances()
        self.FindEndpointInstances()
        self.FindHyperparameterTuningJobInstances()
        self.FindTransformJobInstances()

        print("\n==========================================================================================================" + str(sagemakerRegion) + "==================================================================================================\n")
        print("========================================================================================================================================================================================================================")
        print("NotebookEnv: " + str(self.instancesDictoinary['NotebookEnv']))
        print("TrainingJobInstances: " + str(self.instancesDictoinary['TrainingJobInstances']))
        print("EndpointInstances: " +str(self.instancesDictoinary['EndpointInstances']))
        print("HyperparameterInstances: " +str(self.instancesDictoinary['HyperparameterInstances']))
        print("batchTransformInstances: " +str(self.instancesDictoinary['batchTransformInstances']))
        print("OverallTotalInstancesPerRegion: " + str(self.instancesDictoinary['OverallTotalInstances']))
        print("========================================================================================================================================================================================================================")

#############################################################END OF CLASS#############################################################


#############################################################START OF CLASS DRIVER#############################################################

'''
    This is the first thing to run once you run the script
'''
if __name__ == '__main__':

    regions = ['us-east-1','us-east-2','us-west-1','us-west-2','ap-south-1','ap-northeast-2','ap-southeast-1','ap-southeast-2','ap-northeast-1','ca-central-1','eu-central-1','eu-west-1','eu-west-2']
    access_key = input("Please enter your access key: ")
    secret_key = input("Please enter your secret key: ")

    grandTotal = 0
    for sagemakerRegion in regions:
        sageMaker = SageMakerBoto3(access_key,secret_key,sagemakerRegion)
        sageMaker.returnTotalRunningInstances(sagemakerRegion)
        grandTotal += sageMaker.getRegionTotal()

print("\n=================================================================================================== GRAND TOTAL ACROSS REGIONS: " + str(grandTotal) + " ==========================================================================================\n")
