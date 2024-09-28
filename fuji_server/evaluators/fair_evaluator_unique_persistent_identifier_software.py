# SPDX-FileCopyrightText: 2020 PANGAEA (https://www.pangaea.de/)
#
# SPDX-License-Identifier: MIT

from fuji_server.evaluators.fair_evaluator import FAIREvaluator
from fuji_server.models.unique_persistent_identifier_software import UniquePersistentIdentifierSoftware
from fuji_server.models.unique_persistent_identifier_software_output import UniquePersistentIdentifierSoftwareOutput


# TODO: might be able to mix and match with unique and persistent Data/Metadata checks?
class FAIREvaluatorUniquePersistentIdentifierSoftware(FAIREvaluator):
    """
    A class to evaluate the globally unique and persistent identifier of the software (FRSM-01). A child class of FAIREvaluator.
    ...

    Methods
    ------
    evaluate()
        This method will evaluate whether the software is assigned to a unique and persistent identifier.
    """

    def __init__(self, fuji_instance):
        FAIREvaluator.__init__(self, fuji_instance)
        metric = "FRSM-01-F1"
        self.set_metric(metric)

        # Create map from metric test names to class functions. This is necessary as functions may be reused for different metrics relating to licenses.
        self.metric_test_map = {  # overall map
            "testCodeMetaJSONAtRoot": ["FRSM-01-F1-1"],
            "testUniqueIdentifier": ["FRSM-01-F1-2"],
            "testIdentifierScheme": ["FRSM-01-F1-3"],
            "testSchemeCommonlyUsed": ["FRSM-01-F1-4"],
            "testDOIInReadme": ["FRSM-01-F1-CESSDA-1"],
            "testReleasesSemanticVersioning": ["FRSM-01-F1-CESSDA-2"],
            "testReleasesDOI": ["FRSM-01-F1-CESSDA-3"],
        }

    def testUniqueIdentifier(self):
        """The software has a human and machine-readable unique identifier that is resolvable to a machine-readable landing page and follows a defined unique identifier syntax.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testUniqueIdentifier"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for unique identifier is not implemented.")
        return test_status

    def testIdentifierScheme(self):
        """The identifier uses an identifier scheme that guarantees globally uniqueness and persistence.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testIdentifierScheme"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for identifier scheme is not implemented.")
        return test_status

    def testSchemeCommonlyUsed(self):
        """The identifier scheme is commonly used in the domain.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testSchemeCommonlyUsed"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(
                f"{self.metric_identifier} : Test for domain use of identifier scheme is not implemented."
            )
        return test_status

    def testDOIInReadme(self):
        """A version-dependent DOI must be added in the repository's README as the recommended citation.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testDOIInReadme"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for presence of DOI in README is not implemented.")
        return test_status

    def testReleasesSemanticVersioning(self):
        """Releases use the Semantic Versioning 2.0.0 notation.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testReleasesSemanticVersioning"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for release notation is not implemented.")
        return test_status

    def testReleasesDOI(self):
        """Only Major and Minor releases are assigned DOIs.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testReleasesDOI"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            self.logger.warning(f"{self.metric_identifier} : Test for DOIs of releases is not implemented.")
        return test_status

    def testCodeMetaJSONAtRoot(self):
        """The software has a CodeMeta file located at project root.

        Returns:
            bool: True if the test was defined and passed. False otherwise.
        """
        agnostic_test_name = "testCodeMetaJSONAtRoot"
        test_status = False
        test_defined = False
        for test_id in self.metric_test_map[agnostic_test_name]:
            if self.isTestDefined(test_id):
                test_defined = True
                break
        if test_defined:
            test_score = self.getTestConfigScore(test_id)
            codemeta_files = self.fuji.github_data.get("CodeMeta", None)
            if codemeta_files is not None and len(codemeta_files) > 0:
                codemeta_file = codemeta_files[0]["path"]
                test_status = True
                self.maturity = max(self.getTestConfigMaturity(test_id), self.maturity)
                self.setEvaluationCriteriumScore(test_id, test_score, "pass")
                self.score.earned += test_score
                self.logger.log(
                    self.fuji.LOG_SUCCESS,
                    f"{self.metric_identifier} : Found CodeMeta file {codemeta_file} at repository root ({test_id}).",
                )
            if not test_status:
                self.logger.warning(f"{self.metric_identifier} : Did not find a CodeMeta file at repository root ({test_id}).")
        return test_status

    def evaluate(self):
        if self.metric_identifier in self.metrics:
            self.result = UniquePersistentIdentifierSoftware(
                id=self.metric_number, metric_identifier=self.metric_identifier, metric_name=self.metric_name
            )
            self.output = UniquePersistentIdentifierSoftwareOutput()
            self.result.test_status = "fail"
            if self.testCodeMetaJSONAtRoot():
                self.result.test_status = "pass"
            if self.testUniqueIdentifier():
                self.result.test_status = "pass"
            if self.testIdentifierScheme():
                self.result.test_status = "pass"
            if self.testSchemeCommonlyUsed():
                self.result.test_status = "pass"
            if self.testDOIInReadme():
                self.result.test_status = "pass"
            if self.testReleasesSemanticVersioning():
                self.result.test_status = "pass"
            if self.testReleasesDOI():
                self.result.test_status = "pass"
            else:
                self.result.test_status = "fail"
                self.score.earned = 0
                self.logger.warning(self.metric_identifier + " : Failed to check the software identifier.")
            self.result.score = self.score
            self.result.metric_tests = self.metric_tests
            self.result.output = self.output
            self.result.maturity = self.maturity
