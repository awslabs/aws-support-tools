#!/usr/bin/env python3

# Modules importing
from __future__ import print_function
import os, sys
import waffun as function
import boto3
import zipfile

# Global Constants
limitWebAcl = '10'

def stageFile(fileName):
    # Trying to 'touch' (create) the provided file
    dummyFile = ""
    try:
        dummyFile = open(fileName, 'w')
    except:
        print("*** Unable to create the file " + fileName + "! ***\n", file=sys.stderr)
        sys.exit(-1)
    else:
        return (dummyFile)

def getWaf(arguments):
    '''
    Prints customer account and calls the right WAF function to get customer's resources.
    The arguments are a list with the following values: [wafType to be considered (1 = global, 2 = regional), region name, Web ACL ID]
    '''

    # Staging all files. The first one is the log file. The second one is the Terraform template file.
    # The third one is the zip file containing the two previous ones.
    listLogTemplate = function.getHomeConfig()
    log = stageFile(listLogTemplate[0])
    template = stageFile(listLogTemplate[1])
    package = listLogTemplate[2]

    print("Your WAFER log file is " + listLogTemplate[0])
    print("Your Terraform template file is " + listLogTemplate[1])

    # Populating first lines of the log file
    log.write("*************************************************************************\n")
    log.write("WAFER - AWS WAF Enhanced Repicator - Version " + function.getVersion() + "\n")
    log.write("*************************************************************************\n")

    webAclId = arguments[2]
    isRegional = False
    suffix = "_"
    region = "us-east-1"
    if arguments[0] == 2: # This indicates that it will be regional WAF
        isRegional = True
        suffix = "regional_"
        region = arguments[1]

    if isRegional:
        print("Considering WAF regional resources on " + region + ".\n")
        log.write(function.getFormattedDateTime() + "Region: " + region + "\n")
        client = boto3.setup_default_session(region_name = region)
        client = boto3.client('waf-regional')
    else:
        print("Considering WAF global resources.\n")
        log.write(function.getFormattedDateTime() + "Global WAF\n")
        client = boto3.client('waf')
    
    if len(webAclId) == 0:
        try:
            response = client.list_web_acls()
        except:
            function.abortMission(log, template, "list_web_acls()")
        else:
            # In case query is ok, proceed with the code
            if len(response) == 0:
                if isRegional:
                    print("You have no Web ACLs on region {}. Exiting...\n".format(region), file=sys.stderr)
                else:
                    print("You have no global Web ACLs.\n", file=sys.stderr)
                log.write(function.getFormattedDateTime() + "End of Log.")
                function.abortMission(log, template)
            else:
                print("Choose which Web ACL you want to consider: ")
                for i in range(len(response['WebACLs'])):
                    print("[{}] Id: {}, Name: {}".format(str(i+1), response['WebACLs'][i]['WebACLId'], response['WebACLs'][i]['Name']))
                print("[0] Abort")
                choice = -1
                while (choice < 0 or choice > len(response)):
                    choice = input("Your choice: ")
                    if  not choice.isdigit():
                        choice = -1
                    else:
                        choice = int(choice)
                if choice == 0:
                    print("Aborting execution.\n", file=sys.stderr)
                    log.write(function.getFormattedDateTime() + "End of Log.")
                    function.abortMission(log, template, "")
                webAclId = response['WebACLs'][choice-1]['WebACLId']
                webAclName = response['WebACLs'][choice-1]['Name']
    else:
        try:
            response = client.get_web_acl(WebACLId = webAclId)
        except:
            if isRegional:
                print("Unable to find the provided Web ACL ID {} on the provided region {}.".format(webAclId, region), file=sys.stderr)
                log.write(function.getFormattedDateTime() + "Unable to find the provided Web ACL " + webAclId + " on the provided region " + region + ".\n")
            else:
                print("Unable to find the provided global Web ACL ID {}.".format(webAclId), file=sys.stderr)
                log.write(function.getFormattedDateTime() + "Unable to find the provided global Web ACL " + webAclId + ".\n")
            function.abortMission(log, template, "")
        webAclName = response['WebACL']['Name']
    
    log.write(function.getFormattedDateTime() + "Web ACL (ID): " + webAclName + " (" + webAclId + ")\n")
    print("Grabbing resources for Web ACL {} (ID: {})...".format(webAclName, webAclId))

    try:
        response1 = client.get_web_acl(WebACLId = webAclId)
    except:
        function.abortMission(log, template, "get_web_acl()")

    metricName = response1['WebACL']['MetricName']
    defaultAction = response1['WebACL']['DefaultAction']['Type']

    # Starting the template writing.
    template.write('provider "aws" {\n')
    if isRegional:
        template.write('  region = "' + region + '"\n')
    else:
        template.write('  region = "us-east-1"\n')
    template.write('}\n\n')
    
    # Getting all conditions.
    conditionsResult = crawlConditions(client, log, template, suffix) 
    template.write(conditionsResult[1])
    template.write("\n\n")

    rules = {}
    
    for i in range(len(response1['WebACL']['Rules'])):
        finalString = ""
        ruleId = response1['WebACL']['Rules'][i]['RuleId']
        ruleType = response1['WebACL']['Rules'][i]['Type']
        if ruleType == 'GROUP':
            try:
                groupTemp = client.get_rule_group(RuleGroupId = ruleId)
            except:
                function.abortMission(log, template, "get_rule_group()")
            groupName = groupTemp['RuleGroup']['Name']
            print("Rule Group (Id): {} ({})".format(groupName, ruleId))
            log.write(function.getFormattedDateTime() + "Group Name: " + groupName + " / Group Id: " + ruleId + "\n")
            try:
                loopGroup = client.list_activated_rules_in_rule_group(RuleGroupId = ruleId)
            except:
                function.abortMission(log, template, "list_activated_rules_in_rule_group()")
            for j in range(len(loopGroup['ActivatedRules'])):
                idTemp = loopGroup['ActivatedRules'][j]['RuleId']
                try:
                    rTemp = client.get_rule(RuleId = idTemp)
                except:
                    function.abortMission(log, template, "get_rule()")
                # Checking if the rule was not already recorded
                if not idTemp in rules:
                    index = 0
                    for key, value in rules.items():
                        if rules[key][:5] == "rule_":
                            index += 1 
                    rules[idTemp] = "rule_" + str(index)
                    nameTemp = rTemp['Rule']['Name']        
                    print("                 Rule Name: {} / Rule ID: {}".format(nameTemp, idTemp))
                    log.write(function.getFormattedDateTime() + "            Rule Name: " + nameTemp + " / Rule ID: " + ruleId + "\n")
                    finalString += "resource \"aws_waf" + suffix + "rule\" \"rule_" + str(index) +"\" {\n"
                    finalString += "  name        = \"" + rTemp['Rule']['Name'] + "\"\n"
                    finalString += "  metric_name = \"" + rTemp['Rule']['MetricName'] + "\"\n\n"
                    for k in range(len(rTemp['Rule']['Predicates'])):
                        if isRegional:
                            finalString += "  predicate {\n"
                        else:
                            finalString += "  predicates {\n"
                        finalString += "    type    = \"" + rTemp['Rule']['Predicates'][k]['Type'] + "\"\n"
                        finalString += "    negated = " + str(rTemp['Rule']['Predicates'][k]['Negated']).lower() + "\n"
                        conditionId = rTemp['Rule']['Predicates'][k]['DataId']
                        finalString += "    data_id = \"${aws_waf" + suffix + conditionsResult[0][conditionId][:-2] + "." + conditionsResult[0][conditionId] + ".id}\"\n"
                        finalString += "  }\n"
                    finalString += "}\n\n"
            finalString += "resource \"aws_waf" + suffix + "rule_group\" \"rule_group_" + str(i) +"\" {\n"
            rules[ruleId] = "rule_group_" + str(i)
            finalString += "  name        = \"" + groupName + "\"\n"
            finalString += "  metric_name = \"" + groupTemp['RuleGroup']['MetricName'] + "\"\n\n"
            for j in range(len(loopGroup['ActivatedRules'])):
                finalString += "  activated_rule {\n"
                finalString += "    action {\n"
                finalString += "      type = \"" + loopGroup['ActivatedRules'][j]['Action']['Type'] + "\"\n"
                finalString += "    }\n\n"
                finalString += "    priority = " + str(loopGroup['ActivatedRules'][j]['Priority']) + "\n"
                finalString += "    rule_id  = \"${aws_waf" + suffix + "rule." + rules[loopGroup['ActivatedRules'][j]['RuleId']] + ".id}\"\n"
                finalString += "  }\n\n"
            finalString += "}\n\n"
            template.write(finalString)
        elif ruleType == "RATE_BASED":
            try:
                rTemp = client.get_rate_based_rule(RuleId = ruleId)
            except:
                function.abortMission(log, template, "get_rate_based_rule()")
            ruleName = rTemp['Rule']['Name']
            ruleAction = response1['WebACL']['Rules'][i]['Action']['Type']
            log.write(function.getFormattedDateTime() + "Rule Name: " + ruleName + " / Rule Id: " + ruleId + "\n")
            print("Rule Name: {} / Rule Id: {}".format(ruleName, ruleId))
            idTemp = rTemp['Rule']['RuleId']
            if not idTemp in rules:
                index = 0
                for key, value in rules.items():
                    if rules[key][:5] == "rule_":
                        index += 1 
                rules[idTemp] = "rule_" + str(index)
                finalString += "resource \"aws_waf" + suffix + "rate_based_rule\" \"rule_" + str(index) +"\" {\n"
                finalString += "  name        = \"" + rTemp['Rule']['Name'] + "\"\n"
                finalString += "  metric_name = \"" + rTemp['Rule']['MetricName'] + "\"\n\n"
                finalString += "  rate_key    = \"" + rTemp['Rule']['RateKey'] + "\"\n"
                finalString += "  rate_limit  = " + str(rTemp['Rule']['RateLimit']) + "\n\n"
                for j in range(len(rTemp['Rule']['MatchPredicates'])):
                    if isRegional:
                        finalString += "  predicate {\n"
                    else:
                        finalString += "  predicates {\n"
                    conditionId = rTemp['Rule']['MatchPredicates'][j]['DataId']
                    finalString += "    data_id = \"${aws_waf" + suffix + conditionsResult[0][conditionId][:-2] + "." + conditionsResult[0][conditionId] + ".id}\"\n"
                    finalString += "    negated = " + str(rTemp['Rule']['MatchPredicates'][j]['Negated']).lower() + "\n"
                    finalString += "    type    = \"" + rTemp['Rule']['MatchPredicates'][j]['Type'] + "\"\n"
                    finalString += "  }\n\n"
                finalString += "}\n\n"
                template.write(finalString)
        elif ruleType == "REGULAR":
            try:
                rTemp = client.get_rule(RuleId = ruleId)
            except:
                function.abortMission(log, template, "get_rule()")
            ruleName = rTemp['Rule']['Name']
            ruleAction = response1['WebACL']['Rules'][i]['Action']['Type']
            log.write(function.getFormattedDateTime() + "Rule Name: " + ruleName + " / Rule Id: " + ruleId + "\n")
            print("Rule Name: {} / Rule Id: {}".format(ruleName, ruleId))
            idTemp = rTemp['Rule']['RuleId']
            if not idTemp in rules:
                index = 0
                for key, value in rules.items():
                    if rules[key][:5] == "rule_":
                        index += 1 
                rules[idTemp] = "rule_" + str(index)
                finalString += "resource \"aws_waf" + suffix + "rule\" \"rule_" + str(index) +"\" {\n"
                finalString += "  name        = \"" + rTemp['Rule']['Name'] + "\"\n"
                finalString += "  metric_name = \"" + rTemp['Rule']['MetricName'] + "\"\n\n"
                for j in range(len(rTemp['Rule']['Predicates'])):
                    if isRegional:
                        finalString += "  predicate {\n"
                    else:
                        finalString += "  predicates {\n"
                    conditionId = rTemp['Rule']['Predicates'][j]['DataId']
                    finalString += "    data_id = \"${aws_waf" + suffix + conditionsResult[0][conditionId][:-2] + "." + conditionsResult[0][conditionId] + ".id}\"\n"
                    finalString += "    negated = " + str(rTemp['Rule']['Predicates'][j]['Negated']).lower() + "\n"
                    finalString += "    type    = \"" + rTemp['Rule']['Predicates'][j]['Type'] + "\"\n"
                    finalString += "  }\n\n"
                finalString += "}\n\n"
                template.write(finalString)

    # Getting all associated resources for the Web ACL.
    resourcesResult = getAssociatedResources(client, webAclId, region, log, template, isRegional) 
    template.write(resourcesResult[1])
    
    finalString = ""
    finalString += "resource \"aws_waf" + suffix + "web_acl\" \"web_acl\" {\n"
    finalString += '  name        = "'+ webAclName + '"\n'
    finalString += '  metric_name = "' + metricName + '"\n\n'
    finalString += '  default_action {\n'
    finalString += '    type = "' + defaultAction + '"\n'
    finalString += '  }\n\n'
    for i in range(len(response1['WebACL']['Rules'])):
        ruleType = response1['WebACL']['Rules'][i]['Type']
        if isRegional:
            finalString += "  rule {\n"
        else:
            finalString += "  rules {\n"
        finalString += "    priority = " + str(response1['WebACL']['Rules'][i]['Priority']) + "\n"
        finalString += "    type     = \"" + ruleType + "\"\n"
        if ruleType == "GROUP":
            finalString += "    rule_id  = \"${aws_waf" + suffix + "rule_group." + rules[response1['WebACL']['Rules'][i]['RuleId']] + ".id}\"\n\n"
            finalString += "    override_action {\n"
            finalString += "      type = \"" + response1['WebACL']['Rules'][i]['OverrideAction']['Type'] + "\"\n"
        elif ruleType == "REGULAR":
            finalString += "    rule_id  = \"${aws_waf" + suffix + "rule." + rules[response1['WebACL']['Rules'][i]['RuleId']] + ".id}\"\n\n"
            finalString += "    action {\n"
            finalString += "      type = \"" + response1['WebACL']['Rules'][i]['Action']['Type'] + "\"\n"
        elif ruleType == "RATE_BASED":
            finalString += "    rule_id  = \"${aws_waf" + suffix + "rate_based_rule." + rules[response1['WebACL']['Rules'][i]['RuleId']] + ".id}\"\n\n"
            finalString += "    action {\n"
            finalString += "      type = \"" + response1['WebACL']['Rules'][i]['Action']['Type'] + "\"\n"
        finalString += "    }\n"    
        finalString += "  }\n\n"
    finalString += "}\n\n"

    # This means there are regional resources associated with the Web ACL. In case it's a Global WAF Web ACL,
    # and there is at least one CloudFront distribution associated with it, this was already covered in the
    # the corresponding CloudFront block while running the getAssociatedResources() function.
    if len(resourcesResult[0]) > 0 and isRegional:
        for z in range(len(resourcesResult[0])):
            finalString += "resource \"aws_wafregional_web_acl_association\" \"web_acl_association_" + str(z) + "\" {\n"
            finalString += "  web_acl_id   = \"${aws_wafregional_web_acl.web_acl.id}\"\n"
            if "alb_dns_name" in resourcesResult[0][z]:
                finalString += "  resource_arn = \"${aws_lb.waferALB.arn}\"\n"  # This means an ALB needs to be associated with the Web ACL
            else:
                # This means an API Gateway needs to be associated with the Web ACL
                finalString += "  resource_arn = \"arn:aws:apigateway:" + region + "::/restapis/${aws_api_gateway_rest_api.waferAPI.id}/stages/waferStage\"\n"
            finalString += "}\n\n"

    # This is the real final part of the template file (the outputs).
    finalString += "output \"Web_ACL_Name\" {\n"
    finalString += "  description = \"Please refer to this Web ACL\"\n"
    finalString += "  value       = \"" + webAclName + "\"\n"
    finalString += "}\n\n"
    
    for z in range(len(resourcesResult[0])):
        finalString += "output \"" + resourcesResult[0][z][0] + "\" {\n"
        finalString += "  description = \"" + resourcesResult[0][z][1] + "\"\n"
        tail = ""
        if "api_gateway_invoke_url" in resourcesResult[0][z]:
            tail = "/WAFER" # Adding the stage nane to the final URL.
        finalString += "  value       = " + resourcesResult[0][z][2] + tail + "\n"
        finalString += "}\n\n"
    template.write(finalString)
    log.write(function.getFormattedDateTime() + "End of Log.")
    print("All done.")
    log.close()
    template.close()

    # Zipping files to facilitate attaching them to an eventual support case.
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    zf = zipfile.ZipFile(package, mode = "w")
    try:
        zf.write(listLogTemplate[0], compress_type = compression)
    except:
        print("Unable to add {} to the zip file!".format(listLogTemplate[0]))
    
    try:
        zf.write(listLogTemplate[1], compress_type = compression)
    except:
        print("Unable to add {} to the zip file!".format(listLogTemplate[1]))
    
    zf.close()
    print("\nIf this operation is related to a support case, upload the file {} to the case.".format(package))


def crawlConditions(botoClient, log, template, suffix):
    '''
    This function crawls all conditions from the provided Boto3 object and returns them in a form of a conditions list and a template string.
    '''

    returnString = ""
    conditionsDict = {}
    # Getting the String Match Conditions
    try:
        test = botoClient.list_byte_match_sets()
    except:
        function.abortMission(log, template, "list_byte_match_sets()")
    for k in range(len(test['ByteMatchSets'])):
        try:
            condition = botoClient.get_byte_match_set(ByteMatchSetId = test['ByteMatchSets'][k]['ByteMatchSetId'])
        except:
            function.abortMission(log, template, "get_byte_match_set()")
        namePrefix = "byte_match_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "byte_match_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['ByteMatchSet']['Name'] + "\"\n\n"
        for l in range(len(condition['ByteMatchSet']['ByteMatchTuples'])):
            returnString += "  byte_match_tuples {\n"
            returnString += "    text_transformation   = \"" + condition['ByteMatchSet']['ByteMatchTuples'][l]['TextTransformation'] + "\"\n"
            returnString += "    target_string         = \"" + str(condition['ByteMatchSet']['ByteMatchTuples'][l]['TargetString'])[2:-1] + "\"\n"
            returnString += "    positional_constraint = \"" + condition['ByteMatchSet']['ByteMatchTuples'][l]['PositionalConstraint'] + "\"\n\n"
            returnString += "    field_to_match {\n"
            returnString += "      type = \"" + condition['ByteMatchSet']['ByteMatchTuples'][l]['FieldToMatch']['Type'] + "\"\n"
            if len(condition['ByteMatchSet']['ByteMatchTuples'][l]['FieldToMatch']) > 1:
                returnString += "      data = \"" + condition['ByteMatchSet']['ByteMatchTuples'][l]['FieldToMatch']['Data'] + "\"\n"
            returnString += "    }\n"
            returnString += "  }"
            if l != len(condition['ByteMatchSet']['ByteMatchTuples']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['ByteMatchSets'][k]['ByteMatchSetId']] = namePrefix
        returnString += "}\n\n"

    returnString += "\n\n"
    # Getting the Regex Pattern Sets
    try:
        test = botoClient.list_regex_pattern_sets()
    except:
        function.abortMission(log, template, "list_regex_pattern_sets()")
    for k in range(len(test['RegexPatternSets'])):
        try:
            condition = botoClient.get_regex_pattern_set(RegexPatternSetId = test['RegexPatternSets'][k]['RegexPatternSetId'])
        except:
            function.abortMission(log, template, "get_regex_pattern_set()")
        namePrefix = "regex_pattern_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "regex_pattern_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name                  = \"" + condition['RegexPatternSet']['Name'] + "\"\n"
        returnString += "  regex_pattern_strings = [ " 
        for l in range(len(condition['RegexPatternSet']['RegexPatternStrings'])):
            # The following loop is to insert another "\" for all Regex pattern sets that have "\", as Terraform may not originally understand them.
            cadTemp = ""
            for m in range(len(condition['RegexPatternSet']['RegexPatternStrings'][l])):
                if condition['RegexPatternSet']['RegexPatternStrings'][l][m] == "\\":
                    cadTemp += "\\\\" + condition['RegexPatternSet']['RegexPatternStrings'][l][m+1:]
                    m += 1
            if len(cadTemp) == 0:
                cadTemp = condition['RegexPatternSet']['RegexPatternStrings'][l]
            returnString += "\"" + cadTemp + "\""
            if l != len(condition['RegexPatternSet']['RegexPatternStrings']) - 1:
                returnString += ", "
        returnString += " ]\n"
        conditionsDict[test['RegexPatternSets'][k]['RegexPatternSetId']] = namePrefix
        returnString += "}\n\n"
    
    # Getting the Regex Match Conditions
    try:
        test = botoClient.list_regex_match_sets()
    except:
        function.abortMission(log, template, "list_regex_match_sets()")
    for k in range(len(test['RegexMatchSets'])):
        try:
            condition = botoClient.get_regex_match_set(RegexMatchSetId = test['RegexMatchSets'][k]['RegexMatchSetId'])
        except:
            function.abortMission(log, template, "get_regex_match_set()")
        namePrefix = "regex_match_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "regex_match_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['RegexMatchSet']['Name'] + "\"\n\n"
        for l in range(len(condition['RegexMatchSet']['RegexMatchTuples'])):
            returnString += "  regex_match_tuple {\n"
            returnString += "    field_to_match {\n"
            returnString += "      type = \"" + condition['RegexMatchSet']['RegexMatchTuples'][l]['FieldToMatch']['Type'] + "\"\n"
            if len(condition['RegexMatchSet']['RegexMatchTuples'][l]['FieldToMatch']) > 1:
                returnString += "      data = \"" + condition['RegexMatchSet']['RegexMatchTuples'][l]['FieldToMatch']['Data'] + "\"\n"
            returnString += "    }\n\n"
            returnString += "    text_transformation   = \"" + condition['RegexMatchSet']['RegexMatchTuples'][l]['TextTransformation'] + "\"\n"
            returnString += "    regex_pattern_set_id  = \"${aws_waf" + suffix + "regex_pattern_set." + conditionsDict[condition['RegexMatchSet']['RegexMatchTuples'][l]['RegexPatternSetId']] + ".id}\"\n"
            returnString += "  }"
            if l != len(condition['RegexMatchSet']['RegexMatchTuples']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['RegexMatchSets'][k]['RegexMatchSetId']] = namePrefix
        returnString += "}\n\n"
    
    # Getting the SQL Injection Conditions
    try:
        test = botoClient.list_sql_injection_match_sets()
    except:
        function.abortMission(log, template, "list_sql_injection_match_sets()")
    for k in range(len(test['SqlInjectionMatchSets'])):
        try:
            condition = botoClient.get_sql_injection_match_set(SqlInjectionMatchSetId = test['SqlInjectionMatchSets'][k]['SqlInjectionMatchSetId'])
        except:
            function.abortMission(log, template, "get_sql_injection_match_set()")
        namePrefix = "sql_injection_match_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "sql_injection_match_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['SqlInjectionMatchSet']['Name'] + "\"\n\n"
        for l in range(len(condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples'])):
            if len(suffix) == 1: # This means it's global WAF (suffix == '_'). Terraaform expects 'tuples' (plural).
                returnString += "  sql_injection_match_tuples {\n"
            else:
                returnString += "  sql_injection_match_tuple {\n"
            returnString += "    text_transformation   = \"" + condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples'][l]['TextTransformation'] + "\"\n"
            returnString += "    field_to_match {\n"
            returnString += "      type = \"" + condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples'][l]['FieldToMatch']['Type'] + "\"\n"
            if len(condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples'][l]['FieldToMatch']) > 1:
                returnString += "      data = \"" + condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples'][l]['FieldToMatch']['Data'] + "\"\n"
            returnString += "    }\n"
            returnString += "  }"
            if l != len(condition['SqlInjectionMatchSet']['SqlInjectionMatchTuples']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['SqlInjectionMatchSets'][k]['SqlInjectionMatchSetId']] = namePrefix
        returnString += "}"
    
    returnString += "\n\n"
    # Getting the Size Constraint Set Conditions
    try:
        test = botoClient.list_size_constraint_sets()
    except:
        function.abortMission(log, template, "list_size_constraint_sets()")
    for k in range(len(test['SizeConstraintSets'])):
        try:
            condition = botoClient.get_size_constraint_set(SizeConstraintSetId = test['SizeConstraintSets'][k]['SizeConstraintSetId'])
        except:
            function.abortMission(log, template, "get_size_constraint_set())")
        namePrefix = "size_constraint_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "size_constraint_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['SizeConstraintSet']['Name'] + "\"\n\n"
        for l in range(len(condition['SizeConstraintSet']['SizeConstraints'])):
            returnString += "  size_constraints {\n"
            returnString += "    text_transformation = \"" + condition['SizeConstraintSet']['SizeConstraints'][l]['TextTransformation'] + "\"\n"
            returnString += "    comparison_operator = \"" + condition['SizeConstraintSet']['SizeConstraints'][l]['ComparisonOperator'] + "\"\n"
            returnString += "    size                = \"" + str(condition['SizeConstraintSet']['SizeConstraints'][l]['Size']) + "\"\n\n"
            returnString += "    field_to_match {\n"
            returnString += "      type = \"" + condition['SizeConstraintSet']['SizeConstraints'][l]['FieldToMatch']['Type'] + "\"\n"
            if len(condition['SizeConstraintSet']['SizeConstraints'][l]['FieldToMatch']) > 1:
                returnString += "      data = \"" + condition['SizeConstraintSet']['SizeConstraints'][l]['FieldToMatch']['Data'] + "\"\n"
            returnString += "    }\n"
            returnString += "  }"
            if l != len(condition['SizeConstraintSet']['SizeConstraints']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['SizeConstraintSets'][k]['SizeConstraintSetId']] = namePrefix
        returnString += "}"

    returnString += "\n\n"
    # Getting the IP Set Conditions
    try:
        test = botoClient.list_ip_sets()
    except:
        function.abortMission(log, template, "list_ip_sets()")
    for k in range(len(test['IPSets'])):
        try:
            condition = botoClient.get_ip_set(IPSetId = test['IPSets'][k]['IPSetId'])
        except:
            function.abortMission(log, template, "get_ip_set()")
        namePrefix = "ipset_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "ipset\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['IPSet']['Name'] + "\"\n\n"
        for l in range(len(condition['IPSet']['IPSetDescriptors'])):
            if len(suffix) == 1: # This means it's global WAF (suffix == '_'). Terraaform expects 'descriptors' (plural).
                returnString += "  ip_set_descriptors {\n"
            else:
                returnString += "  ip_set_descriptor {\n"
            returnString += "    type  = \"" + condition['IPSet']['IPSetDescriptors'][l]['Type'] + "\"\n"
            returnString += "    value = \"" + condition['IPSet']['IPSetDescriptors'][l]['Value'] + "\"\n"
            returnString += "  }"
            if l != len(condition['IPSet']['IPSetDescriptors']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['IPSets'][k]['IPSetId']] = namePrefix
        returnString += "}\n\n"    
    
    # Getting the Geo Conditions
    try:
        test = botoClient.list_geo_match_sets()
    except:
        function.abortMission(log, template, "list_geo_match_sets()")
    for k in range(len(test['GeoMatchSets'])):
        try:
            condition = botoClient.get_geo_match_set(GeoMatchSetId = test['GeoMatchSets'][k]['GeoMatchSetId'])
        except:
            function.abortMission(log, template, "get_geo_match_set()")
        namePrefix = "geo_match_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "geo_match_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['GeoMatchSet']['Name'] + "\"\n\n"
        for l in range(len(condition['GeoMatchSet']['GeoMatchConstraints'])):
            returnString += "  geo_match_constraint {\n"
            returnString += "    type  = \"" + condition['GeoMatchSet']['GeoMatchConstraints'][l]['Type'] + "\"\n"
            returnString += "    value = \"" + condition['GeoMatchSet']['GeoMatchConstraints'][l]['Value'] + "\"\n"
            returnString += "  }"
            if l != len(condition['GeoMatchSet']['GeoMatchConstraints']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['GeoMatchSets'][k]['GeoMatchSetId']] = namePrefix
        returnString += "}\n\n"

    # Getting the XSS Conditions
    try:
        test = botoClient.list_xss_match_sets()
    except:
        function.abortMission(log, template, "list_xss_match_sets()")
    for k in range(len(test['XssMatchSets'])):
        try:
            condition = botoClient.get_xss_match_set(XssMatchSetId = test['XssMatchSets'][k]['XssMatchSetId'])
        except:
            function.abortMission(log, template, "get_xss_match_set()")
        namePrefix = "xss_match_set_" + str(k)
        returnString += "resource \"aws_waf" + suffix + "xss_match_set\" \"" + namePrefix + "\" {\n"
        returnString += "  name = \"" + condition['XssMatchSet']['Name'] + "\"\n\n"
        for l in range(len(condition['XssMatchSet']['XssMatchTuples'])):
            if len(suffix) == 1: # This means it's global WAF (suffix == '_'). Terraform expects 'tuples' (plural).
                returnString += "  xss_match_tuples {\n"
            else:
                returnString += "  xss_match_tuple {\n"
            returnString += "    text_transformation   = \"" + condition['XssMatchSet']['XssMatchTuples'][l]['TextTransformation'] + "\"\n"
            returnString += "    field_to_match {\n"
            returnString += "      type = \"" + condition['XssMatchSet']['XssMatchTuples'][l]['FieldToMatch']['Type'] + "\"\n"
            if len(condition['XssMatchSet']['XssMatchTuples'][l]['FieldToMatch']) > 1:
                returnString += "      data = \"" + condition['XssMatchSet']['XssMatchTuples'][l]['FieldToMatch']['Data'] + "\"\n"
            returnString += "    }\n"
            returnString += "  }"
            if l != len(condition['XssMatchSet']['XssMatchTuples']) - 1:
                returnString += "\n\n"
            else:
                returnString += "\n"
        conditionsDict[test['XssMatchSets'][k]['XssMatchSetId']] = namePrefix
        returnString += "}"
    
    return([conditionsDict, returnString])

def getAssociatedResources(wafClient, AclId, region, log, template, isRegional):
    '''
    Looks into the customer's WebACL and looks for associated resources.
    Returns a list of resources' names in case any is found.
    '''
    
    resourceString = ""
    resourcesList  = []
    
    # Checking if the Web ACL is associated with any resource. If the resulting array las a length greater than zero, 
    # it means there is at least one resource of that type associated with the Web ACL.
    # Looking for ALBs first. If at least one ALB is associated, we need to create all resources to support it:
    # VPC, Subnet, Route Table, Internet Gateway, Target Group and Security Group.
    if isRegional:
        try:
            rAlb = wafClient.list_resources_for_web_acl(WebACLId = AclId, ResourceType = "APPLICATION_LOAD_BALANCER")
        except:
            function.abort(log, template, "list_resources_for_web_acl(ALB)")
        if len(rAlb['ResourceArns']) > 0:
            log.write(function.getFormattedDateTime() + "Found at least one ALB associated with this Web ACL. Creating equivalent resource...\n")
            print("Found at least one ALB associated with this Web ACL. Creating equivalent resource...")
            resourceString += "resource \"aws_vpc\" \"waferVPC\" {\n"
            resourceString += "  cidr_block = \"10.10.0.0/16\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_subnet\" \"waferSubnet1\" {\n"
            resourceString += "  vpc_id            = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  availability_zone = \"" + region + "a\"\n" 
            resourceString += "  cidr_block        = \"10.10.1.0/24\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_subnet\" \"waferSubnet2\" {\n"
            resourceString += "  vpc_id            = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  availability_zone = \"" + region + "b\"\n" 
            resourceString += "  cidr_block        = \"10.10.2.0/24\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_internet_gateway\" \"waferIGW\" {\n"
            resourceString += "  vpc_id = \"${aws_vpc.waferVPC.id}\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table\" \"waferRT\" {\n"
            resourceString += "  vpc_id     = \"${aws_vpc.waferVPC.id}\"\n\n"
            resourceString += "  route {\n"
            resourceString += "    cidr_block = \"0.0.0.0/0\"\n"
            resourceString += "    gateway_id = \"${aws_internet_gateway.waferIGW.id}\"\n"
            resourceString += "  }\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table_association\" \"waferRTAssociation1\" {\n"
            resourceString += "  subnet_id      = \"${aws_subnet.waferSubnet1.id}\"\n"
            resourceString += "  route_table_id = \"${aws_route_table.waferRT.id}\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table_association\" \"waferRTAssociation2\" {\n"
            resourceString += "  subnet_id      = \"${aws_subnet.waferSubnet2.id}\"\n"
            resourceString += "  route_table_id = \"${aws_route_table.waferRT.id}\"\n"
            resourceString += "}\n\n"
            
            resourceString += "resource \"aws_security_group\" \"waferALBSG\" {\n"
            resourceString += "  name        = \"waferALBSG\"\n"
            resourceString += "  description = \"Allow HTTP inbound traffic\"\n"
            resourceString += "  vpc_id      = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  ingress {\n"
            resourceString += "    from_port   = 80\n"
            resourceString += "    to_port     = 80\n"
            resourceString += "    protocol    = \"tcp\"\n"
            resourceString += "    cidr_blocks = [ \"0.0.0.0/0\" ]\n"
            resourceString += "  }\n\n"
            resourceString += "  egress {\n"
            resourceString += "    from_port   = 0\n"
            resourceString += "    to_port     = 0\n"
            resourceString += "    protocol    = \"-1\"\n"
            resourceString += "    cidr_blocks = [ \"0.0.0.0/0\" ]\n"
            resourceString += "  }\n\n"
            resourceString += "  tags = {\n"
            resourceString += "     Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"
            
            resourceString += "resource \"aws_lb\" \"waferALB\" {\n"
            resourceString += "  name               = \"waferALB\"\n"
            resourceString += "  internal           = false\n"
            resourceString += "  load_balancer_type = \"application\"\n"
            resourceString += "  security_groups    = [\"${aws_security_group.waferALBSG.id}\"]\n"
            resourceString += "  subnets            = [\"${aws_subnet.waferSubnet1.id}\", \"${aws_subnet.waferSubnet2.id}\"]\n\n"
            resourceString += "  enable_cross_zone_load_balancing = true\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_lb_target_group\" \"waferALBTG\" {\n"
            resourceString += "  name     = \"waferALBTG\"\n"
            resourceString += "  port     = 80\n"
            resourceString += "  protocol = \"HTTP\"\n"
            resourceString += "  vpc_id   = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_lb_listener\" \"waferALBListener\" {\n"
            resourceString += "  load_balancer_arn = \"${aws_lb.waferALB.arn}\"\n"
            resourceString += "  port     = \"80\"\n"
            resourceString += "  protocol = \"HTTP\"\n\n"
            resourceString += "  default_action {\n"
            resourceString += "    type             = \"forward\"\n"
            resourceString += "    target_group_arn = \"${aws_lb_target_group.waferALBTG.arn}\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"
            
            listTemp = []
            listTemp.append("ALB_DNS_Name")
            listTemp.append("ALB DNS Name")
            listTemp.append("aws_lb.waferALB.dns_name")
            resourcesList.append(listTemp)
        # Let's check also if there's an API Gateway endpoint associated with the Web ACL.
        try:
            rApi = wafClient.list_resources_for_web_acl(WebACLId = AclId, ResourceType = "API_GATEWAY")
        except:
            function.abort(log, template, "list_resources_for_web_acl(API)")
        if len(rApi['ResourceArns']) > 0:
            log.write(function.getFormattedDateTime() + "Found at least one API Gateway endpoint associated with this Web ACL. Creating equivalent resource...\n")
            log.write(function.getFormattedDateTime() + "Do not forget to change the API Gateway Integration method type to something different than 'MOCK'!\n")
            print("Found at least one API Gateway endpoint associated with this Web ACL. Creating equivalent resource...")
            resourceString += "resource \"aws_api_gateway_rest_api\" \"waferAPI\" {\n"
            resourceString += "  name        = \"waferAPI\"\n"
            resourceString += "  description = \"WAFER API\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_api_gateway_resource\" \"waferAPIResource\" {\n"
            resourceString += "  rest_api_id = \"${aws_api_gateway_rest_api.waferAPI.id}\"\n"
            resourceString += "  parent_id   = \"${aws_api_gateway_rest_api.waferAPI.root_resource_id}\"\n"
            resourceString += "  path_part   = \"WAFER\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_api_gateway_method\" \"waferMethod\" {\n"
            resourceString += "  rest_api_id   = \"${aws_api_gateway_rest_api.waferAPI.id}\"\n"
            resourceString += "  resource_id   = \"${aws_api_gateway_resource.waferAPIResource.id}\"\n"
            resourceString += "  http_method   = \"GET\"\n"
            resourceString += "  authorization = \"NONE\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_api_gateway_deployment\" \"waferDeployment\" {\n"
            resourceString += "  depends_on  = [\"aws_api_gateway_integration.waferIntegration\"]\n"
            resourceString += "  rest_api_id = \"${aws_api_gateway_rest_api.waferAPI.id}\"\n"
            resourceString += "  stage_name  = \"test\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_api_gateway_stage\" \"waferStage\" {\n"
            resourceString += "  stage_name    = \"waferStage\"\n"
            resourceString += "  rest_api_id   = \"${aws_api_gateway_rest_api.waferAPI.id}\"\n"
            resourceString += "  deployment_id = \"${aws_api_gateway_deployment.waferDeployment.id}\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_api_gateway_integration\" \"waferIntegration\" {\n"
            resourceString += "  rest_api_id             = \"${aws_api_gateway_rest_api.waferAPI.id}\"\n"
            resourceString += "  resource_id             = \"${aws_api_gateway_resource.waferAPIResource.id}\"\n"
            resourceString += "  http_method             = \"${aws_api_gateway_method.waferMethod.http_method}\"\n"
            resourceString += "  integration_http_method = \"GET\"\n"
            resourceString += "  type                    = \"MOCK\"\n"
            resourceString += "}\n\n"
            
            listTemp = []
            listTemp.append("API_Gateway_Invoke_URL")
            listTemp.append("API Gateway Invoke URL")
            listTemp.append("aws_api_gateway_stage.waferStage.invoke_url")
            resourcesList.append(listTemp)
    else:
        # It's a global WAF, so, we can check if there's a CloudFront distribution associated with the Web ACL.
        try:
            cloudFront = boto3.client('cloudfront')
            rCfn = cloudFront.list_distributions_by_web_acl_id(WebACLId = AclId)
        except:
            function.abort(log, template, "list_distributions_by_web_acl_id(CloudFront)")
        if rCfn['DistributionList']['Quantity'] > 0:
            log.write(function.getFormattedDateTime() + "Found at least one CloudFront distribution associated with this Web ACL. Creating equivalent resource...\n")
            print("Found at least one CloudFront distribution associated with this Web ACL. Creating equivalent resource...")
            # We need to create an ALB first and then use it as the origin for the CloudFront distribution.
            resourceString += "resource \"aws_vpc\" \"waferVPC\" {\n"
            resourceString += "  cidr_block = \"10.10.0.0/16\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_subnet\" \"waferSubnet1\" {\n"
            resourceString += "  vpc_id            = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  availability_zone = \"us-east-1a\"\n" 
            resourceString += "  cidr_block        = \"10.10.1.0/24\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_subnet\" \"waferSubnet2\" {\n"
            resourceString += "  vpc_id            = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  availability_zone = \"us-east-1b\"\n" 
            resourceString += "  cidr_block        = \"10.10.2.0/24\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_internet_gateway\" \"waferIGW\" {\n"
            resourceString += "  vpc_id = \"${aws_vpc.waferVPC.id}\"\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table\" \"waferRT\" {\n"
            resourceString += "  vpc_id     = \"${aws_vpc.waferVPC.id}\"\n\n"
            resourceString += "  route {\n"
            resourceString += "    cidr_block = \"0.0.0.0/0\"\n"
            resourceString += "    gateway_id = \"${aws_internet_gateway.waferIGW.id}\"\n"
            resourceString += "  }\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table_association\" \"waferRTAssociation1\" {\n"
            resourceString += "  subnet_id      = \"${aws_subnet.waferSubnet1.id}\"\n"
            resourceString += "  route_table_id = \"${aws_route_table.waferRT.id}\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_route_table_association\" \"waferRTAssociation2\" {\n"
            resourceString += "  subnet_id      = \"${aws_subnet.waferSubnet2.id}\"\n"
            resourceString += "  route_table_id = \"${aws_route_table.waferRT.id}\"\n"
            resourceString += "}\n\n"
            
            resourceString += "resource \"aws_security_group\" \"waferALBSG\" {\n"
            resourceString += "  name        = \"waferALBSG\"\n"
            resourceString += "  description = \"Allow HTTP inbound traffic\"\n"
            resourceString += "  vpc_id      = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "  ingress {\n"
            resourceString += "    from_port   = 80\n"
            resourceString += "    to_port     = 80\n"
            resourceString += "    protocol    = \"tcp\"\n"
            resourceString += "    cidr_blocks = [ \"0.0.0.0/0\" ]\n"
            resourceString += "  }\n\n"
            resourceString += "  egress {\n"
            resourceString += "    from_port   = 0\n"
            resourceString += "    to_port     = 0\n"
            resourceString += "    protocol    = \"-1\"\n"
            resourceString += "    cidr_blocks = [ \"0.0.0.0/0\" ]\n"
            resourceString += "  }\n\n"
            resourceString += "  tags = {\n"
            resourceString += "     Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"
            
            resourceString += "resource \"aws_lb\" \"waferALB\" {\n"
            resourceString += "  name               = \"waferALB\"\n"
            resourceString += "  internal           = false\n"
            resourceString += "  load_balancer_type = \"application\"\n"
            resourceString += "  security_groups    = [\"${aws_security_group.waferALBSG.id}\"]\n"
            resourceString += "  subnets            = [\"${aws_subnet.waferSubnet1.id}\", \"${aws_subnet.waferSubnet2.id}\"]\n\n"
            resourceString += "  enable_cross_zone_load_balancing = true\n\n"
            resourceString += "  tags = {\n"
            resourceString += "    Name = \"WAFER\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_lb_target_group\" \"waferALBTG\" {\n"
            resourceString += "  name     = \"waferALBTG\"\n"
            resourceString += "  port     = 80\n"
            resourceString += "  protocol = \"HTTP\"\n"
            resourceString += "  vpc_id   = \"${aws_vpc.waferVPC.id}\"\n"
            resourceString += "}\n\n"

            resourceString += "resource \"aws_lb_listener\" \"waferALBListener\" {\n"
            resourceString += "  load_balancer_arn = \"${aws_lb.waferALB.arn}\"\n"
            resourceString += "  port     = \"80\"\n"
            resourceString += "  protocol = \"HTTP\"\n\n"
            resourceString += "  default_action {\n"
            resourceString += "    type             = \"forward\"\n"
            resourceString += "    target_group_arn = \"${aws_lb_target_group.waferALBTG.arn}\"\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"
            
            listTemp = []
            listTemp.append("ALB_DNS_Name")
            listTemp.append("ALB DNS Name")
            listTemp.append("aws_lb.waferALB.dns_name")
            resourcesList.append(listTemp)
            
            # Time to create the CloudFront distribution.
            resourceString += "resource \"aws_cloudfront_distribution\" \"waferCFN\" {\n"
            resourceString += "  comment    = \"WAFER CloudFront Distribution\"\n"
            resourceString += "  enabled    = true\n"
            resourceString += "  web_acl_id = \"${aws_waf_web_acl.web_acl.id}\"\n\n"
            resourceString += "  origin {\n"
            resourceString += "    domain_name = \"${aws_lb.waferALB.dns_name}\"\n"
            resourceString += "    origin_id   = \"ELB-${aws_lb.waferALB.name}\"\n\n"
            resourceString += "    custom_origin_config {\n"
            resourceString += "      http_port              = 80\n"
            resourceString += "      https_port             = 443\n"
            resourceString += "      origin_protocol_policy = \"http-only\"\n"
            resourceString += "      origin_ssl_protocols   = [\"TLSv1\", \"TLSv1.1\", \"TLSv1.2\", \"SSLv3\"]\n"
            resourceString += "    }\n"
            resourceString += "  }\n\n"
            resourceString += "  default_cache_behavior {\n"
            resourceString += "    allowed_methods  = [\"GET\", \"HEAD\", \"OPTIONS\", \"PUT\", \"POST\", \"PATCH\", \"DELETE\"]\n"
            resourceString += "    cached_methods   = [\"GET\", \"HEAD\"]\n"
            resourceString += "    target_origin_id = \"ELB-${aws_lb.waferALB.name}\"\n\n"
            resourceString += "    forwarded_values {\n"
            resourceString += "      query_string = true\n"
            resourceString += "      headers      = [\"*\"]\n"
            resourceString += "      cookies {\n"
            resourceString += "        forward = \"all\"\n"
            resourceString += "      }\n"
            resourceString += "    }\n\n"
            resourceString += "    viewer_protocol_policy = \"allow-all\"\n"
            resourceString += "  }\n\n"
            resourceString += "  viewer_certificate {\n"
            resourceString += "    cloudfront_default_certificate = true\n"
            resourceString += "  }\n\n"
            resourceString += "  restrictions {\n"
            resourceString += "    geo_restriction {\n"
            resourceString += "      restriction_type = \"none\"\n"
            resourceString += "    }\n"
            resourceString += "  }\n"
            resourceString += "}\n\n"

            listTemp = []
            listTemp.append("CloudFront_Distribution_Domain_Name")
            listTemp.append("CloudFront Distribution Name")
            listTemp.append("aws_cloudfront_distribution.waferCFN.domain_name")
            resourcesList.append(listTemp)

    return([resourcesList, resourceString])