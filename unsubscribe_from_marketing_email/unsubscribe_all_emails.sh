#!/bin/bash
# Copyright 2021 Chris Farris <chrisf@primeharbor.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Fast fix inspired by this tweet from Ian Mckay - https://twitter.com/iann0036/status/1176705548290535425

# In theory, AWS says accounts created via Organizations aren't opt-in to marketing emails. So we filter on Invited only. YMMV.
ROOT_EMAIL_LIST=`aws organizations list-accounts --query "Accounts[?JoinedMethod=='INVITED'].Email" --output text`

# AWS will redirect you to a CloudFlare captcha page if you fire too many of these against them at once.
# Sleep is the lazy ratelimiter. check the unsubscribe.log file to see if you see messages like these which indicate success:
# {"formId":"34006","followUpUrl":"https:\/\/pages.awscloud.com\/PreferenceCenterV4-Unsub-PreferenceCenter.html"}

SLEEP_TIME=30

for email in $ROOT_EMAIL_LIST; do
	echo "Unsubscribing $email from AWS Marketing emails"
	encoded_email=`echo ${email} | sed s/@/%40/g`
	curl -s 'https://pages.awscloud.com/index.php/leadCapture/save2' --data 'FirstName=&LastName=&Email='${encoded_email}'&Company=&Phone=&Country=&preferenceCenterCategory=no&preferenceCenterGettingStarted=no&preferenceCenterOnlineInPersonEvents=no&preferenceCenterMonthlyAWSNewsletter=no&preferenceCenterTrainingandBestPracticeContent=no&preferenceCenterProductandServiceAnnoucements=no&preferenceCenterSurveys=no&PreferenceCenter_AWS_Partner_Events_Co__c=no&preferenceCenterOtherAWSCommunications=no&PreferenceCenter_Language_Preference__c=&Title=&Job_Role__c=&Industry=&Level_of_AWS_Usage__c=&LDR_Solution_Area__c=&Unsubscribed=yes&UnsubscribedReason=I%20already%20get%20email%20from%20another%20account&unsubscribedReasonOther=&useCaseMultiSelect=&zOPFormValidationBotVerification=&Website_Referral_Code__c=&zOPURLTrackingTRKCampaign=&zOPEmailValidationHygiene=validate&zOPURLTrackingSiteCatalystSource=&zOPURLTrackingSiteCatalystChannel=em&zOPURLTrackingSiteCatalystPublisher=aws&formid=34006&lpId=127906&subId=6&munchkinId=112-TZM-766&lpurl=%2F%2Fpages.awscloud.com%2Fcommunication-preferences.html%3Fcr%3D%7Bcreative%7D%26kw%3D%7Bkeyword%7D&cr=&kw=&q=&_mkt_trk=id%3A112-TZM-766%26token%3A_mch-pages.awscloud.com-1634828395353-78149&formVid=34006&mkt_tok=MTEyLVRaTS03NjYAAAGArUL0R1AJrZPQKmPub_MWYJS68FkcdjTMmCy7hrG4hzSnK08MaPDXszkwXYVw1Oo6qVoy3QrDShzVolVitJ6g9eeBa4zvvVPU-rtlT8xTKPwbEN4jyFTC&_mktoReferrer=https%3A%2F%2Fpages.awscloud.com%2Fcommunication-preferences.html%3Fsc_channel%3Dem%26sc_campaign%3DGLOBAL_CR_SU_H2-2021-CCAP-SurveyInvite_10.08.21.03%2520-%2520Survey%2520Invite%25201%2520Email%2520Send%26sc_publisher%3Daws%26sc_medium%3Dem_430081%26sc_content%3Dsurvey%26sc_country%3DUS%26sc_region%3D%3Fparam%3Dunsubscribe%26mkt_tok%3DMTEyLVRaTS03NjYAAAGArUL0R1AJrZPQKmPub_MWYJS68FkcdjTMmCy7hrG4hzSnK08MaPDXszkwXYVw1Oo6qVoy3QrDShzVolVitJ6g9eeBa4zvvVPU-rtlT8xTKPwbEN4jyFTC&checksumFields=FirstName%2CLastName%2CEmail%2CCompany%2CPhone%2CCountry%2CpreferenceCenterCategory%2CpreferenceCenterGettingStarted%2CpreferenceCenterOnlineInPersonEvents%2CpreferenceCenterMonthlyAWSNewsletter%2CpreferenceCenterTrainingandBestPracticeContent%2CpreferenceCenterProductandServiceAnnoucements%2CpreferenceCenterSurveys%2CPreferenceCenter_AWS_Partner_Events_Co__c%2CpreferenceCenterOtherAWSCommunications%2CPreferenceCenter_Language_Preference__c%2CTitle%2CJob_Role__c%2CIndustry%2CLevel_of_AWS_Usage__c&checksum=e60aa8324cf0ac1844446eab8eb95a56c6ef1edd0c7f3c8b134f5bfc0259ee90' >> unsubscribe.log
	if [ $? -eq 0 ] ; then
		echo "Success. Sleeping $SLEEP_TIME sec"
	else
		echo "Failure"
	fi
	sleep $SLEEP_TIME
done