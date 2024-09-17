# SPDX-FileCopyrightText: 2020 PANGAEA (https://www.pangaea.de/)
#
# SPDX-License-Identifier: MIT

import enum
import json
import socket
import re
import urllib.parse

import requests

from fuji_server.evaluators.fair_evaluator import FAIREvaluator
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
        self.resolved_urls = []

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

    def compareResolvedUrlIdentifiers(self):
        """Check if the found related_identifiers from README or CITATION file resolve to the same instance of the software.
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
            test_score = self.getTestConfigScore(test_id)

        if len(self.resolved_urls) == 2:
            self.logger.log(
                self.fuji.LOG_SUCCESS,
                f"{self.metric_identifier} : Both found DOIs resolve to the same instance: README: {self.resolved_urls[0]} , CITATION: {self.resolved_urls[1]}."
            )
            test_status = True
            self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
            self.score.earned += test_score
        elif len(self.resolved_urls) == 1:
            self.logger.warning(
                f"{self.metric_identifier} : Only one of the found DOIs in README and CITATION resolves back to the same instance.")
            test_status = True
            self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
            self.score.earned += 1
        else:
            self.logger.warning(
                f"{self.metric_identifier} : None of the found DOIs resolve back to the same instance.")

        return test_status

    def testResolvesSameContent(self, location, pid_url):
        """Check if the given DOI resolves to the same instance of the software"""
        landing_url = self.fuji.landing_url
        # Test if the identifier resolves to the landing page
        if landing_url == pid_url:
            self.logger.log(
                self.fuji.LOG_SUCCESS,
                f"{self.metric_identifier} : DOI ({pid_url}) from {location} resolves back to Landing page {landing_url}."
            )
            self.resolved_urls.append(pid_url)

        else:
            # Test if the identifier resolves to the same instance
            resolved_github_link = self.resolveRelatedIdentifiersFromDoi(pid_url)
            if resolved_github_link:
                # The found GitHub link in DOI metadata resolves back to landing page
                self.logger.log(
                    self.fuji.LOG_SUCCESS,
                    f"{self.metric_identifier} : GitHub link ({resolved_github_link}) from {location} resolves back to landing page ({landing_url})."
                )
                self.resolved_urls.append(resolved_github_link)
            else:
                self.logger.warning(
                    f"{self.metric_identifier} : Resolved DOI from {location} does not resolve to the same instance as the landing page ({landing_url}).")

    def resolveRelatedIdentifiersFromDoi(self, doi_url):
        """Check if zenodo metadata from given DOI contains related_identifiers with GitHub link.

        Returns:
           string : GitHub url identifier when the zenodo metadata from given DOI contains it
        """
        parsed_pid_url = urllib.parse.urlparse(doi_url)
        zenodo_api_url = f"https://zenodo.org/api/records/{parsed_pid_url.path.split('/')[-1]}"
        self.logger.info(
            f"{self.metric_identifier} : Accessing the zenodo api with following url: {zenodo_api_url} ."
        )

        zenodo_api_response = requests.get(zenodo_api_url)
        if zenodo_api_response.status_code == 200:
            self.logger.info(
                f"{self.metric_identifier} : Got zenodo api data from given request url: {zenodo_api_url} ."
            )
        elif zenodo_api_response.status_code == 404:
            self.logger.warning(f"{self.metric_identifier} : ERROR 404: No DOI matches in zenodo api found with given request url: {zenodo_api_url} .")

        zenodo_data = json.loads(zenodo_api_response.content)

        if "related_identifiers" in zenodo_data["metadata"]:
            related_identifiers = zenodo_data["metadata"]["related_identifiers"]
            self.logger.info(
                f"{self.metric_identifier} : Found related_identifiers in zenodo metadata: {related_identifiers} ."
            )

            for identifier in related_identifiers:
                found_identifier = identifier["identifier"]

                github_regex = r"(https?://github.com/([^\s/]+)/([^\s/]+))"
                github_link_match = re.search(github_regex, found_identifier)
                github_link = github_link_match.group(1)

                if github_link:
                    self.logger.info(
                        f"{self.metric_identifier} : Found GitHub link in zenodo metadata: {github_link} ."
                    )
                    landing_url = self.fuji.landing_url
                    if github_link == landing_url:
                        return github_link
                else:
                    self.logger.warning(
                        f"{self.metric_identifier} : No GitHub link found in related_identifiers.")
        else:
            self.logger.warning(
                f"{self.metric_identifier} : No related_identifiers in zenodo metadata found with given DOI: {doi_url}.")

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

            readme_raw = test_requirements["required"]["location"]

            self.logger.info(
                f"{self.metric_identifier} : Looking for zenodo DOI url in {readme_raw[0]} ({test_id})."
            )

            doi_regex = r"\[!\[DOI\]\(https://[^\)]+\)\]\((https://[^\)]+)\)"

            readme = self.fuji.github_data.get(readme_raw[0])

            if readme is not None:
                readme_raw_decoded = readme[0]["content"].decode("utf-8")
                doi_matches = re.findall(doi_regex, readme_raw_decoded)

                if len(doi_matches) > 0:
                    self.logger.info(
                        f"{self.metric_identifier} : Found zenodo DOI url {doi_matches} in {readme_raw[0]} ({test_id}).",
                    )
                    id_helper = IdentifierHelper(doi_matches[0])

                    resolved_url = id_helper.get_identifier_info(self.fuji.pid_collector)["resolved_url"]
                    if resolved_url is not None:
                        self.logger.log(
                            self.fuji.LOG_SUCCESS,
                            f"{self.metric_identifier} : Found resolved zenodo DOI url: {resolved_url} in {readme_raw[0]}  ({test_id})."
                        )
                        self.testResolvesSameContent(readme_raw[0], resolved_url)
                        test_status = True
                        self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
                        self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                        self.score.earned += 1
                        self.content_list.append(resolved_url)
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
            citation_raw = test_requirements["required"]["location"]

            self.logger.info(
                f"{self.metric_identifier} : Looking for zenodo DOI url in {citation_raw[1]} ({test_id})."
            )

            citation = self.fuji.github_data.get(citation_raw[1])

            if citation is not None:
                citation_lines = citation[0]["content"].splitlines()
                for line in citation_lines:
                    if "zenodo" in line.decode("utf-8"):
                        doi = line.decode("utf-8").split(":")[1].strip()
                        if doi.startswith("10.5281/zenodo."):
                            zenodo_url = "https://zenodo.org/records/" + doi.split("zenodo.")[1]
                            self.logger.log(
                                self.fuji.LOG_SUCCESS,
                                f"{self.metric_identifier} : Found zenodo DOI url: {zenodo_url} in {citation_raw[1]} ({test_id})."
                            )
                            self.testResolvesSameContent(citation_raw[1], zenodo_url)
                            test_status = True
                            self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
                            self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                            self.score.earned += 1
                            self.content_list.append(zenodo_url)
                        else:
                            self.logger.warning(
                                f"{self.metric_identifier} : Zenodo DOI in CITATION.cff is in wrong format.")

        return test_status

    def evaluate(self):
        socket.setdefaulttimeout(1)

        self.result = IdentifierIncluded(
            id=self.metric_number, metric_identifier=self.metric_identifier, metric_name=self.metric_name
        )
        self.output = IdentifierIncludedOutput()

        # self.output.object_identifier_included = self.fuji.metadata_merged.get("object_identifier")

        contents = self.fuji.metadata_merged.get("object_content_identifier")

        if contents:
            if isinstance(contents, dict):
                contents = [contents]
            contents = [c for c in contents if c]
            self.result.test_status = "fail"
            if self.testDataSizeTypeNameAvailable(contents):
                self.result.test_status = "pass"
            if self.testDataUrlOrPIDAvailable(contents):
                self.result.test_status = "pass"
        else:
            self.logger.warning('No contents available')

        if self.testZenodoDoiInReadme():
            self.result.test_status = "pass"
        if self.testZenodoDoiInCitationFile():
            self.result.test_status = "pass"
        if self.compareResolvedUrlIdentifiers():
            self.result.test_status = "pass"

        self.result.metric_tests = self.metric_tests
        self.output.object_identifier_included = self.fuji.landing_url
        self.output.object_content_identifier_included = self.content_list
        self.result.output = self.output
        self.result.maturity = self.maturity
        self.result.score = self.score
