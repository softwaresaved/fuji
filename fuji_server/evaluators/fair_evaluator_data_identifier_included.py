# SPDX-FileCopyrightText: 2020 PANGAEA (https://www.pangaea.de/)
#
# SPDX-License-Identifier: MIT

import enum
import json
import socket
import re

import yaml

from fuji_server.evaluators.fair_evaluator import FAIREvaluator
from fuji_server.harvester.metadata_harvester import MetadataHarvester
from fuji_server.helper.identifier_helper import IdentifierHelper
from fuji_server.models.identifier_included import IdentifierIncluded
from fuji_server.models.identifier_included_output import IdentifierIncludedOutput
from fuji_server.models.identifier_included_output_inner import IdentifierIncludedOutputInner


class FAIREvaluatorDataIdentifierIncluded(FAIREvaluator):
    """
    A class to evaluate whether the metadata includes the identifier of the data is being described (F3-01M).
    A child class of FAIREvaluator.
    ...

    Methods
    ------
    evaluate()
        This method will evaluate whether the metadata contains an identifier, e.g., PID or URL, which indicates the location of the downloadable data content or
        a data identifier that matches the identifier as part of the assessment request.
    """

    def __init__(self, fuji_instance):
        FAIREvaluator.__init__(self, fuji_instance)
        self.set_metric(["FsF-F3-01M", "FRSM-07-F3"])
        self.content_list = []

        self.metadata_found = {}

        self.metric_test_map = {  # overall map
            "testDataSizeTypeNameAvailable": ["FsF-F3-01M-1"],
            "testDataUrlOrPIDAvailable": ["FsF-F3-01M-2", "FRSM-07-F3-1"],
            "testResolvesSameContent": ["FRSM-07-F3-2"],
            "testZenodoDoiInReadme": ["FRSM-07-F3-1"],
            "testZenodoDoiInCitationFile": ["FRSM-07-F3-1"],
        }

    def testDataSizeTypeNameAvailable(self, datainfolist):
        agnostic_test_name = "testDataSizeTypeNameAvailable"
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        test_result = False
        if test_defined:
            test_score = self.getTestConfigScore(test_id)
            if datainfolist:
                for datainfo in datainfolist:
                    if isinstance(datainfo, dict):
                        """if datainfo.get('source'):
                        if isinstance(datainfo['source'], enum.Enum):
                            try:
                                datainfo['source'] = datainfo['source'].acronym()
                            except:
                                pass"""
                        if datainfo.get("type") or datainfo.get("size") or datainfo.get("url"):
                            test_result = True
                            if isinstance(datainfo.get("source"), enum.Enum):
                                datainfo["source"] = datainfo.get("source").name
                            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                            self.maturity = self.metric_tests.get(test_id).metric_test_maturity_config
                            did_output_content = IdentifierIncludedOutputInner()
                            did_output_content.content_identifier_included = datainfo
                            self.content_list.append(did_output_content)
                            # self.fuji.content_identifier.append(datainfo)
            if test_result:
                self.score.earned += test_score
        return test_result

    def testDataUrlOrPIDAvailable(self, datainfolist):
        agnostic_test_name = "testDataUrlOrPIDAvailable"
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        test_result = False
        if test_defined:
            test_score = self.getTestConfigScore(test_id)
            if datainfolist:
                for datainfo in datainfolist:
                    if isinstance(datainfo, dict):
                        if datainfo.get("url"):
                            test_result = True
                            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                            self.maturity = self.metric_tests.get(test_id).metric_test_maturity_config
                        else:
                            self.logger.warning(
                                self.metric_identifier + f" : Object (content) url is empty -: {datainfo}"
                            )
            if test_result:
                self.score.earned += test_score
        return test_result

    def testResolvesSameContent(self):
        """Does the identifier resolve to the same instance of the software?

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testResolvesSameContent"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for identifier resolve target is not implemented.")
        return test_status

    def testZenodoDoiInReadme(self):
        """The README file includes the DOI that represents all versions in Zenodo.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testZenodoDoiInReadme"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            test_score = self.getTestConfigScore(test_id)
            test_requirements = self.metric_tests[test_id].metric_test_requirements[0]

            required_locations = test_requirements["required"]["location"]

            self.logger.info(
                f"{self.metric_identifier} : Looking for zenodo DOI url in {required_locations[0]} ({test_id})."
            )

            doi_regex = r"\[!\[DOI\]\(https://[^\)]+\)\]\((https://[^\)]+)\)"

            readme = self.fuji.github_data.get(required_locations[0])

            if readme is not None:
                readme_raw = readme[0]["content"].decode("utf-8")
                doi_matches = re.findall(doi_regex, readme_raw)

                if len(doi_matches) > 0:
                    self.logger.info(
                        f"{self.metric_identifier} : Found zenodo DOI url {doi_matches} in {required_locations[0]} ({test_id}).",
                    )
                    id_helper = IdentifierHelper(doi_matches[0])

                    resolved_url = id_helper.get_identifier_info(self.fuji.pid_collector)["resolved_url"]
                    if resolved_url is not None:
                        self.logger.log(
                            self.fuji.LOG_SUCCESS,
                            f"{self.metric_identifier} : Found resolved zenodo DOI url: {resolved_url} in {required_locations[0]}  ({test_id})."
                        )
                        test_status = True
                        self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
                        self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                        self.score.earned += test_score
                else:
                    self.logger.warning(f"{self.metric_identifier} : No DOI matches in README found.")

        return test_status

    def testZenodoDoiInCitationFile(self):
        """The CITATION.cff file included in the root of the repository includes the appropriate DOI for the corresponding software release in Zenodo.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testZenodoDoiInCitationFile"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            test_score = self.getTestConfigScore(test_id)
            test_requirements = self.metric_tests[test_id].metric_test_requirements[0]
            required_locations = test_requirements["required"]["location"]

            self.logger.info(
                f"{self.metric_identifier} : Looking for zenodo DOI url in {required_locations[1]} ({test_id})."
            )

            citation = self.fuji.github_data.get(required_locations[1])

            if citation is not None:
                citation_lines = citation[0]["content"].splitlines()
                for line in citation_lines:
                    if "zenodo" in line.decode("utf-8"):
                        doi = line.decode("utf-8").split(":")[1].strip()
                        if doi.startswith("10.5281/zenodo."):
                            zenodo_url = "https://zenodo.org/records/" + doi.split("zenodo.")[1]
                            self.logger.log(
                                    self.fuji.LOG_SUCCESS,
                                    f"{self.metric_identifier} : Found zenodo DOI url: {zenodo_url} in {required_locations[1]} ({test_id})."
                                )
                            test_status = True
                            self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
                            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                            self.score.earned += test_score
                        else:
                            self.logger.warning(f"{self.metric_identifier} : Zenodo DOI in CITATION.cff is in wrong format.")

        return test_status

    def evaluate(self):
        socket.setdefaulttimeout(1)

        self.result = IdentifierIncluded(
            id=self.metric_number, metric_identifier=self.metric_identifier, metric_name=self.metric_name
        )
        self.output = IdentifierIncludedOutput()

        contents = self.fuji.metadata_merged.get("object_content_identifier")

        # if id_object is not None:
        #   self.logger.info('FsF-F3-01M : Object identifier specified -: {}'.format(id_object))
        if contents:

            if isinstance(contents, dict):
                contents = [contents]
            # ignore empty?
            contents = [c for c in contents if c]
            # keep unique only -
            # contents = list({cv['url']:cv for cv in contents}.values())
            # print(contents)
            # number_of_contents = len(contents)
            """if number_of_contents >= self.fuji.FILES_LIMIT:
                self.logger.info(
                    self.metric_identifier
                    + " : The total number of object (content) identifiers specified is above threshold, will use the first -: {} content identifiers for the tests".format(
                        self.fuji.FILES_LIMIT
                    )
                )
                contents = contents[: self.fuji.FILES_LIMIT]"""
            self.result.test_status = "fail"
            if self.testDataSizeTypeNameAvailable(contents):
                self.result.test_status = "pass"
            if self.testDataUrlOrPIDAvailable(contents):
                self.result.test_status = "pass"
        else:
            self.logger.warning('No contents available')

        # if self.testResolvesSameContent():
        #    self.result.test_status = "pass"
        if self.testZenodoDoiInReadme():
            self.result.test_status = "pass"
        if self.testZenodoDoiInCitationFile():
            self.result.test_status = "pass"

        # if self.result.test_status == "pass":
            # self.logger.log(
            #     self.fuji.LOG_SUCCESS,
            #     self.metric_identifier + f" : Number of object content identifier found -: {number_of_contents}",
            # )
        else:
            self.logger.warning(self.metric_identifier + " : Valid data (content) identifier missing.")

        self.result.metric_tests = self.metric_tests
        self.output.object_content_identifier_included = self.content_list
        self.result.output = self.output
        self.result.maturity = self.maturity
        self.result.score = self.score
